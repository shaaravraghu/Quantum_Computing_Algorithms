"""
grover_quantum.py
-----------------
Grover's Algorithm — Quantum Circuit (File 2 of 2)

Reads grover_input.csv (written by grover_input_gen.py) and:
  1. Parses the truth table — finds all rows where Output == 1
  2. Infers n_qubits from the Input string length (not the Qubits column)
  3. Builds the uniform-superposition initialisation (H on all qubits)
  4. Constructs a Phase-Kickback Oracle for each marked state
  5. Constructs the Grover Diffuser (amplitude amplification)
  6. Repeats Oracle + Diffuser ≈ π/4 · √(2^n) times
  7. Measures all qubits
  8. Draws the circuit (text + matplotlib PNG)
  9. Plots a histogram of measurement counts with marked states highlighted
 10. Reports found state(s) and whether they match the marked set

If no state is marked (all outputs = 0), the circuit still runs and produces
a near-uniform distribution, as expected for an identity oracle.

Dependencies:
    pip install qiskit qiskit-aer matplotlib

Usage:
    python grover_input_gen.py     # first — writes grover_input.csv
    python grover_quantum.py       # then  — builds, simulates, reports
"""

import csv
import math
import os
import sys

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit_aer import AerSimulator
    import matplotlib.pyplot as plt
except ImportError as exc:
    sys.exit(
        f"Import error: {exc}\n"
        "Install with:  pip install qiskit qiskit-aer matplotlib"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CSV reader
# ══════════════════════════════════════════════════════════════════════════════

def read_input(csv_path: str) -> tuple[int, list[str], list[str]]:
    """
    Parse 1_grover_input.csv.

    Returns:
        n          — number of qubits (derived from len(Input string))
        all_states — every input bitstring in order
        targets    — bitstrings where Output == 1

    n is always derived from the Input column length, never from the Qubits column.
    """
    if not os.path.exists(csv_path):
        sys.exit(
            f"  ✗  '{csv_path}' not found.\n"
            "     Run  grover_input_gen.py  first."
        )

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("  ✗  CSV is empty. Re-run grover_input_gen.py.")

    # Validate columns
    for col in ("Input", "Output"):
        if col not in rows[0]:
            sys.exit(f"  ✗  Missing column '{col}' in CSV.")

    all_states = []
    targets    = []

    for row in rows:
        inp = row["Input"].strip()
        out = row["Output"].strip()

        if not all(ch in "01" for ch in inp):
            sys.exit(f"  ✗  Non-binary Input value: '{inp}'")
        if out not in ("0", "1"):
            sys.exit(f"  ✗  Output must be 0 or 1, got: '{out}'")

        all_states.append(inp)
        if out == "1":
            targets.append(inp)

    # Derive n from Input string length (all must be equal)
    lengths = set(len(s) for s in all_states)
    if len(lengths) != 1:
        sys.exit("  ✗  Inconsistent Input string lengths in CSV.")

    n = lengths.pop()

    if n < 2 or n > 10:
        sys.exit(f"  ✗  Input length {n} is out of range [2, 10].")

    expected = 2 ** n
    if len(all_states) != expected:
        sys.exit(
            f"  ✗  Expected {expected} rows for {n} qubits, found {len(all_states)}."
        )

    # Standard Grover's: exactly one target. Warn if zero.
    if len(targets) == 0:
        print("  ⚠  No states marked as target (all outputs = 0).")
        print("     Running with identity oracle — expect uniform distribution.\n")
    elif len(targets) > 1:
        sys.exit(
            f"  ✗  {len(targets)} states are marked as 1. "
            "Standard Grover's requires exactly one target.\n"
            "     Please re-run grover_input_gen.py and mark only one state."
        )

    return n, all_states, targets


# ══════════════════════════════════════════════════════════════════════════════
#  Oracle — phase kickback on the target state
# ══════════════════════════════════════════════════════════════════════════════

def build_oracle(n: int, targets: list[str]) -> QuantumCircuit:
    """
    Phase-kickback oracle.

    For each marked state t:
      • Flip (X) every qubit where t[i] == '0'  →  maps t to |11…1⟩
      • MCX onto ancilla  →  phase kickback of −1 onto t
      • Unflip the same qubits

    If targets is empty, returns an identity oracle (no gates).

    Bit ordering:
        Qiskit measures q[n-1]..q[0] and reverses the string for display.
        After msb_first() reversal, target[i] aligns with q[i] directly.
    """
    qr      = QuantumRegister(n, "q")
    ancilla = QuantumRegister(1, "anc")
    oracle  = QuantumCircuit(qr, ancilla, name="Oracle")

    if not targets:
        return oracle                              # identity — no marks

    # Ancilla → |−⟩  (phase kickback trick)
    oracle.x(ancilla[0])
    oracle.h(ancilla[0])
    oracle.barrier()

    for target in targets:
        # Qiskit measures q[n-1]...q[0] as a string (MSB-first in output).
        # After msb_first() reversal, display string matches target directly.
        # So target[i] corresponds to q[n-1-i] in the circuit — but Qiskit's
        # output string is already reversed, meaning target[i] → q[i] here.
        zero_pos = [i for i, bit in enumerate(target) if bit == "0"]

        if zero_pos:
            oracle.x(zero_pos)
        oracle.barrier()

        oracle.mcx(list(range(n)), ancilla[0])
        oracle.barrier()

        if zero_pos:
            oracle.x(zero_pos)
        oracle.barrier()

    # Restore ancilla to |0⟩
    oracle.h(ancilla[0])
    oracle.x(ancilla[0])

    return oracle


# ══════════════════════════════════════════════════════════════════════════════
#  Diffuser — Grover amplitude-amplification operator
# ══════════════════════════════════════════════════════════════════════════════

def build_diffuser(n: int) -> QuantumCircuit:
    """
    Grover diffuser: 2|s⟩⟨s| − I  (reflects about the uniform superposition).

    Steps:  H⊗n → X⊗n → n-controlled-Z → X⊗n → H⊗n
    The n-controlled-Z is built as: H on q[n-1] → MCX → H on q[n-1].
    """
    qr   = QuantumRegister(n, "q")
    diff = QuantumCircuit(qr, name="Diffuser")

    diff.h(range(n))
    diff.barrier()
    diff.x(range(n))
    diff.barrier()
    diff.h(n - 1)
    diff.mcx(list(range(n - 1)), n - 1)
    diff.h(n - 1)
    diff.barrier()
    diff.x(range(n))
    diff.barrier()
    diff.h(range(n))

    return diff


# ══════════════════════════════════════════════════════════════════════════════
#  Full Grover circuit
# ══════════════════════════════════════════════════════════════════════════════

def build_grover_circuit(n: int, targets: list[str], iterations: int) -> QuantumCircuit:
    """
    Assemble: |0⟩^n |0⟩_anc  →  H^n  →  (Oracle + Diffuser)^k  →  Measure
    """
    qr      = QuantumRegister(n, "q")
    ancilla = QuantumRegister(1, "anc")
    cr      = ClassicalRegister(n, "c")
    qc      = QuantumCircuit(qr, ancilla, cr)

    qc.h(range(n))
    qc.barrier(label="init")

    oracle   = build_oracle(n, targets)
    diffuser = build_diffuser(n)

    for i in range(iterations):
        qc.append(oracle,   list(range(n)) + [n])
        qc.barrier(label=f"iter {i + 1}")
        qc.append(diffuser, list(range(n)))
        if i < iterations - 1:
            qc.barrier()

    qc.measure(range(n), range(n))
    return qc


# ══════════════════════════════════════════════════════════════════════════════
#  Simulation & reporting
# ══════════════════════════════════════════════════════════════════════════════

SHOTS = 4096


def simulate(qc: QuantumCircuit) -> dict:
    sim        = AerSimulator()
    transpiled = transpile(qc, sim)
    return sim.run(transpiled, shots=SHOTS).result().get_counts(transpiled)


def msb_first(state: str) -> str:
    """Qiskit returns LSB-first strings; reverse for human-readable MSB-first."""
    return state[::-1]


def analyse(counts: dict, targets: list[str], n: int) -> None:
    total         = sum(counts.values())
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state     = msb_first(sorted_counts[0][0])
    top_prob      = sorted_counts[0][1] / total * 100

    print("\n── Measurement Results ──────────────────────────────────────")
    print(f"  {'State (MSB→LSB)':<20}  {'Counts':>6}  {'Probability':>11}")
    print("  " + "─" * 46)
    for state, count in sorted_counts:
        disp   = msb_first(state)
        marker = "  ◄ TARGET" if disp in targets else ""
        print(f"  |{disp}⟩{'':<15}  {count:>6}  {count/total*100:>9.2f}%{marker}")
    print("─" * 60)

    print(f"\n  Most measured state : |{top_state}⟩  ({top_prob:.1f}% of shots)")

    if not targets:
        print("  Result              : ⚠  No target marked — uniform distribution shown.")
    elif top_state in targets:
        print(f"  Result              : ✓  TARGET FOUND  |{top_state}⟩")
    else:
        hit_prob = counts.get(targets[0][::-1], 0) / total * 100
        print(f"  Result              : ✗  Top state ≠ target |{targets[0]}⟩")
        print(f"                        (target had {hit_prob:.1f}% probability)")
    print()


def plot_counts(counts: dict, targets: list[str], n: int) -> None:
    """
    Histogram — all 2^n states shown, marked states in coral, others in blue.
    Left y-axis: counts. Right y-axis: probability (%).
    Each bar is labelled with its probability above it.
    """
    from matplotlib.patches import Patch

    total = sum(counts.values())

    # Ensure ALL 2^n states appear, even those with 0 counts
    all_keys = [format(i, f"0{n}b") for i in range(2 ** n)]
    display  = {k: counts.get(k[::-1], 0) for k in all_keys}

    labels = list(display.keys())
    values = list(display.values())
    probs  = [v / total * 100 for v in values]
    colors = ["#C04828" if k in targets else "#3B8BD4" for k in labels]

    fig_w = max(10, len(labels) * 0.55)
    fig, ax = plt.subplots(figsize=(fig_w, 5))

    bars = ax.bar(labels, values, color=colors, edgecolor="none", width=0.6)

    for bar, prob in zip(bars, probs):
        if prob > 0.05:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + total * 0.003,
                f"{prob:.1f}%",
                ha="center", va="bottom",
                fontsize=7 if len(labels) > 16 else 8,
                color="#333333",
            )

    ax2 = ax.twinx()
    ax2.set_ylim(0, ax.get_ylim()[1] / total * 100)
    ax2.set_ylabel("Probability (%)", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}%"))

    ax.set_xlabel("Measured State (MSB → LSB)", fontsize=11)
    ax.set_ylabel("Counts", fontsize=11)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=60 if len(labels) > 8 else 45, ha="right", fontsize=8)

    target_label = "|none⟩" if not targets else f"|{targets[0]}⟩"
    ax.set_title(
        f"Grover's Algorithm  |  target {target_label}  |  {SHOTS} shots  |  {n} qubits  ({2**n} states)",
        fontsize=12, pad=12,
    )

    legend = [Patch(facecolor="#3B8BD4", label="Other states")]
    if targets:
        legend.insert(0, Patch(facecolor="#C04828", label=f"Target  {target_label}"))
    ax.legend(handles=legend, fontsize=10, loc="upper left")

    plt.tight_layout()
    plt.savefig("grover_results.png", dpi=150)
    print("  ✓  Histogram saved  : grover_results.png")
    plt.show()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    csv_path             = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1_grover_input.csv")
    n, all_states, targets = read_input(csv_path)
    iterations           = max(1, round((math.pi / 4) * math.sqrt(2 ** n)))

    print("=" * 60)
    print("  Grover's Algorithm — Quantum Simulation")
    print("=" * 60)
    print(f"  Qubits          : {n}  (= length of input strings in CSV)")
    print(f"  Search space    : {2**n} states")
    print(f"  Marked states   : {len(targets)}  ({', '.join(f'|{t}⟩' for t in targets) if targets else 'none'})")
    print(f"  Grover iters    : {iterations}  (≈ π/4 · √{2**n})")
    print(f"  Shots           : {SHOTS}")
    print("=" * 60)

    print("\nBuilding Grover circuit …")
    qc      = build_grover_circuit(n, targets, iterations)
    qc_draw = qc.decompose()

    print("\n── Circuit (text) ──────────────────────────────────────────")
    print(qc_draw.draw(output="text", fold=120))

    try:
        fig = qc_draw.draw(output="mpl", fold=25, style="bw")
        fig.savefig("grover_circuit.png", dpi=150, bbox_inches="tight")
        print("  ✓  Circuit diagram saved : grover_circuit.png")
        plt.show()
    except Exception as exc:
        print(f"  (Matplotlib circuit diagram skipped: {exc})")

    print("\nRunning simulation on AerSimulator …")
    counts = simulate(qc)

    analyse(counts, targets, n)
    plot_counts(counts, targets, n)


if __name__ == "__main__":
    main()
