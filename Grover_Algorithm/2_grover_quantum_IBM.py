"""
grover_quantum_IBM.py
---------------------
Grover's Algorithm — IBM Quantum Runtime version
qiskit version 1.4.5

Same as grover_quantum.py but runs on real IBM hardware via Qiskit Runtime.
Run grover_input_gen.py first, then this file.
"""

import csv
import math
import os
import sys

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    import matplotlib.pyplot as plt
except ImportError as exc:
    sys.exit(
        f"Import error: {exc}\nInstall with: pip install qiskit qiskit-ibm-runtime matplotlib"
    )

# ── IBM Credentials ───────────────────────────────────────────────────────────
IBM_API_TOKEN = "qlFu1fi7gSOP6e8kiSEUpHhhHhxA5ws1Z4_1HniBxMrY"
IBM_INSTANCE = "crn:v1:bluemix:public:quantum-computing:us-east:a/2d091361e27946c7aca67f1f1f888383:ec5c14bb-e0f4-40f4-82de-5b2ebf6d4341::"

service = QiskitRuntimeService(
    channel="ibm_quantum_platform", token=IBM_API_TOKEN, instance=IBM_INSTANCE
)
backend = service.least_busy(operational=True, simulator=False)
print(f"Running on: {backend.name}")
# ─────────────────────────────────────────────────────────────────────────────

SHOTS = 2048  # Hardcoded, You can vary for your input here.


def read_input(csv_path):
    if not os.path.exists(csv_path):
        sys.exit(f"  ✗  '{csv_path}' not found.\n     Run grover_input_gen.py first.")
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("  ✗  CSV is empty. Re-run grover_input_gen.py.")
    for col in ("Input", "Output"):
        if col not in rows[0]:
            sys.exit(f"  ✗  Missing column '{col}' in CSV.")
    all_states, targets = [], []
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
    lengths = set(len(s) for s in all_states)
    if len(lengths) != 1:
        sys.exit("  ✗  Inconsistent Input string lengths in CSV.")
    n = lengths.pop()
    if n < 2 or n > 10:
        sys.exit(f"  ✗  Input length {n} is out of range [2, 10].")
    expected = 2**n
    if len(all_states) != expected:
        sys.exit(
            f"  ✗  Expected {expected} rows for {n} qubits, found {len(all_states)}."
        )
    if len(targets) == 0:
        print("  ⚠  No states marked as target — expect near-uniform distribution.\n")
    elif len(targets) > 1:
        sys.exit(
            f"  ✗  {len(targets)} states marked. Standard Grover's requires exactly one target."
        )
    return n, all_states, targets


def build_oracle(n, targets):
    qr = QuantumRegister(n, "q")
    ancilla = QuantumRegister(1, "anc")
    oracle = QuantumCircuit(qr, ancilla, name="Oracle")
    if not targets:
        return oracle
    oracle.x(ancilla[0])
    oracle.h(ancilla[0])
    oracle.barrier()
    for target in targets:
        zero_pos = [i for i, bit in enumerate(target) if bit == "0"]
        if zero_pos:
            oracle.x(zero_pos)
        oracle.barrier()
        oracle.mcx(list(range(n)), ancilla[0])
        oracle.barrier()
        if zero_pos:
            oracle.x(zero_pos)
        oracle.barrier()
    oracle.h(ancilla[0])
    oracle.x(ancilla[0])
    return oracle


def build_diffuser(n):
    qr = QuantumRegister(n, "q")
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


def build_grover_circuit(n, targets, iterations):
    qr = QuantumRegister(n, "q")
    ancilla = QuantumRegister(1, "anc")
    cr = ClassicalRegister(n, "c")
    qc = QuantumCircuit(qr, ancilla, cr)
    qc.h(range(n))
    qc.barrier(label="init")
    oracle = build_oracle(n, targets)
    diffuser = build_diffuser(n)
    for i in range(iterations):
        qc.append(oracle, list(range(n)) + [n])
        qc.barrier(label=f"iter {i + 1}")
        qc.append(diffuser, list(range(n)))
        if i < iterations - 1:
            qc.barrier()
    qc.measure(range(n), range(n))
    return qc


def msb_first(state):
    return state[::-1]


def analyse(counts, targets, n):
    total = sum(counts.values())
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_state = msb_first(sorted_counts[0][0])
    top_prob = sorted_counts[0][1] / total * 100

    print("\n── Measurement Results ──────────────────────────────────────")
    print(f"  {'State (MSB→LSB)':<20}  {'Counts':>6}  {'Probability':>11}")
    print("  " + "─" * 46)
    for state, count in sorted_counts:
        disp = msb_first(state)
        marker = "  ◄ TARGET" if disp in targets else ""
        print(f"  |{disp}⟩{'':<15}  {count:>6}  {count/total*100:>9.2f}%{marker}")
    print("─" * 60)
    print(f"\n  Most measured state : |{top_state}⟩  ({top_prob:.1f}% of shots)")
    if not targets:
        print(
            "  Result              : ⚠  No target marked — uniform distribution shown."
        )
    elif top_state in targets:
        print(f"  Result              : ✓  TARGET FOUND  |{top_state}⟩")
    else:
        hit_prob = counts.get(targets[0][::-1], 0) / total * 100
        print(f"  Result              : ✗  Top state ≠ target |{targets[0]}⟩")
        print(
            f"                        (target had {hit_prob:.1f}% — noise may have affected results)"
        )
    print()


def plot_counts(counts, targets, n):
    from matplotlib.patches import Patch

    total = sum(counts.values())
    all_keys = [format(i, f"0{n}b") for i in range(2**n)]
    display = {k: counts.get(k[::-1], 0) for k in all_keys}
    labels = list(display.keys())
    values = list(display.values())
    probs = [v / total * 100 for v in values]
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
                ha="center",
                va="bottom",
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
    ax.set_xticklabels(
        labels, rotation=60 if len(labels) > 8 else 45, ha="right", fontsize=8
    )

    target_label = "|none⟩" if not targets else f"|{targets[0]}⟩"
    ax.set_title(
        f"Grover's Algorithm  |  target {target_label}  |  {SHOTS} shots  |  IBM Hardware",
        fontsize=12,
        pad=12,
    )

    legend = [Patch(facecolor="#3B8BD4", label="Other states")]
    if targets:
        legend.insert(0, Patch(facecolor="#C04828", label=f"Target  {target_label}"))
    ax.legend(handles=legend, fontsize=10, loc="upper left")

    plt.tight_layout()
    plt.savefig("grover_results_IBM.png", dpi=150)
    print("  ✓  Histogram saved  : grover_results_IBM.png")
    plt.show()


def main():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "1_grover_input.csv"
    )
    n, all_states, targets = read_input(csv_path)
    iterations = max(1, round((math.pi / 4) * math.sqrt(2**n)))

    print("=" * 60)
    print("  Grover's Algorithm — IBM Quantum Hardware Run")
    print("=" * 60)
    print(f"  Qubits          : {n}")
    print(f"  Search space    : {2**n} states")
    print(
        f"  Marked states   : {len(targets)}  ({', '.join(f'|{t}⟩' for t in targets) if targets else 'none'})"
    )
    print(f"  Grover iters    : {iterations}  (≈ π/4 · √{2**n})")
    print(f"  Shots           : {SHOTS}")
    print(f"  Backend         : {backend.name}")
    print("=" * 60)

    print("\nBuilding Grover circuit …")
    qc = build_grover_circuit(n, targets, iterations)
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

    print(f"\nTranspiling and submitting to IBM ({SHOTS} shots) …")
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(qc)
    job = Sampler(backend).run([isa_circuit], shots=SHOTS)
    print(f"Job ID: {job.job_id()} | Waiting for results (may take several minutes)...")
    result = job.result()
    counts = result[0].data.c.get_counts()

    analyse(counts, targets, n)
    plot_counts(counts, targets, n)


main()
