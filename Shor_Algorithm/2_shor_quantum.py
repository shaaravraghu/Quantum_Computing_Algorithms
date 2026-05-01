"""
shor_quantum.py
---------------
Shor's Algorithm — Quantum Circuit (File 2 of 3)

Reads shor_input.csv (written by shor_input_gen.py) and:
  1. Builds the counting register  (n_count qubits)  in uniform superposition
  2. Builds the target register    (n_target qubits)  initialised to |1⟩
  3. Applies controlled modular exponentiation  |j⟩|y⟩ → |j⟩|y · aʲ mod N⟩
     using a UnitaryGate constructed from the classical mod-exp matrix.
     This approach is exact and simulator-friendly for small N (≤ 63).
  4. Applies the Inverse QFT to the counting register
  5. Measures the counting register
  6. Draws the circuit (text + matplotlib PNG)
  7. Saves raw phase measurement samples to shor_output.csv

Dependencies:
    pip install qiskit qiskit-aer matplotlib numpy

Usage:
    python shor_input_gen.py       # first  — writes shor_input.csv
    python shor_quantum.py         # second — builds, simulates, saves samples
    python shor_classical_post.py  # third  — extracts factors
"""

import csv
import math
import os
import sys

import numpy as np

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.circuit.library import QFT
    from qiskit.circuit.library import UnitaryGate
    from qiskit_aer import AerSimulator
    import matplotlib.pyplot as plt
except ImportError as exc:
    sys.exit(
        f"Import error: {exc}\n"
        "Install with:  pip install qiskit qiskit-aer matplotlib numpy"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CSV reader
# ══════════════════════════════════════════════════════════════════════════════

def read_input(csv_path: str) -> tuple[int, int, int, int]:
    """Parse shor_input.csv → (N, a, n_count, n_target)."""
    if not os.path.exists(csv_path):
        sys.exit(
            f"  ✗  '{csv_path}' not found.\n"
            "     Run  shor_input_gen.py  first."
        )
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("  ✗  CSV is empty. Re-run shor_input_gen.py.")

    row = rows[0]
    try:
        N        = int(row["N"].strip())
        a        = int(row["a"].strip())
        n_count  = int(row["n_count"].strip())
        n_target = int(row["n_target"].strip())
    except (KeyError, ValueError) as e:
        sys.exit(f"  ✗  Bad CSV format: {e}")

    return N, a, n_count, n_target


# ══════════════════════════════════════════════════════════════════════════════
#  Modular exponentiation unitary
# ══════════════════════════════════════════════════════════════════════════════

def mod_exp_unitary(a: int, power: int, N: int, n_target: int) -> np.ndarray:
    """
    Build the 2^n_target × 2^n_target unitary matrix for the map:
        |y⟩  →  |y · a^power mod N⟩    for y in [0, N-1]
        |y⟩  →  |y⟩                    for y in [N, 2^n_target - 1]

    States y ≥ N are mapped to themselves (they are outside the mod-N domain
    and must be handled to keep the matrix unitary).
    """
    dim  = 2 ** n_target
    U    = np.zeros((dim, dim), dtype=complex)
    mult = pow(int(a), int(power), int(N))   # a^power mod N

    for y in range(dim):
        if y < N:
            image = (y * mult) % N
        else:
            image = y                         # identity on out-of-range states
        U[image][y] = 1.0

    return U


def controlled_mod_exp(a: int, N: int, n_count: int, n_target: int) -> QuantumCircuit:
    """
    Build the full controlled modular exponentiation block.

    For each counting qubit j (0 … n_count-1), apply the gate:
        controlled-U^(2^j)  where U|y⟩ = |a·y mod N⟩

    The j-th counting qubit controls U^(2^j) on the target register.
    Together these implement the map:
        |x⟩|1⟩  →  |x⟩|a^x mod N⟩
    """
    qr_count  = QuantumRegister(n_count,  "count")
    qr_target = QuantumRegister(n_target, "target")
    qc        = QuantumCircuit(qr_count, qr_target, name="ModExp")

    for j in range(n_count):
        power   = 2 ** j
        U_mat   = mod_exp_unitary(a, power, N, n_target)
        U_gate  = UnitaryGate(U_mat, label=f"U^{power}").control(1)
        # control qubit = count[j], target qubits = target[0..n_target-1]
        qc.append(U_gate, [qr_count[j]] + list(qr_target))

    return qc


# ══════════════════════════════════════════════════════════════════════════════
#  Full Shor circuit
# ══════════════════════════════════════════════════════════════════════════════

def build_shor_circuit(N: int, a: int, n_count: int, n_target: int) -> QuantumCircuit:
    """
    Assemble the full Shor period-finding circuit:

        |0⟩^n_count   →  H^n_count  ─────────────────┐
                                                       ├─ measure counting reg
        |0⟩^n_target  →  X[0]  →  ModExp  →  IQFT ──┘

    Step by step:
      1. H on all counting qubits  (uniform superposition over 0…2^n_count - 1)
      2. X on target[0]            (initialise target register to |1⟩)
      3. Controlled modular exp    (entangles counting and target registers)
      4. Inverse QFT on counting   (extracts period as a phase)
      5. Measure counting register
    """
    qr_count  = QuantumRegister(n_count,  "count")
    qr_target = QuantumRegister(n_target, "target")
    cr        = ClassicalRegister(n_count, "c")
    qc        = QuantumCircuit(qr_count, qr_target, cr)

    # Step 1: superposition on counting register
    qc.h(qr_count)
    qc.barrier(label="superposition")

    # Step 2: target register → |1⟩
    qc.x(qr_target[0])
    qc.barrier(label="|1⟩ init")

    # Step 3: controlled modular exponentiation
    mod_exp = controlled_mod_exp(a, N, n_count, n_target)
    qc.append(mod_exp, list(qr_count) + list(qr_target))
    qc.barrier(label="mod exp")

    # Step 4: inverse QFT on counting register
    iqft = QFT(n_count, inverse=True, do_swaps=True, name="IQFT")
    qc.append(iqft, qr_count)
    qc.barrier(label="IQFT")

    # Step 5: measure counting register
    qc.measure(qr_count, cr)

    return qc


# ══════════════════════════════════════════════════════════════════════════════
#  Simulation
# ══════════════════════════════════════════════════════════════════════════════

SHOTS = 2048


def simulate(qc: QuantumCircuit) -> dict:
    sim        = AerSimulator()
    transpiled = transpile(qc, sim, optimization_level=1)
    return sim.run(transpiled, shots=SHOTS).result().get_counts(transpiled)


# ══════════════════════════════════════════════════════════════════════════════
#  Reporting
# ══════════════════════════════════════════════════════════════════════════════

def print_counts(counts: dict, n_count: int) -> None:
    total         = sum(counts.values())
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    print("\n── Raw Measurement Results (counting register) ──────────────")
    print(f"  {'Bitstring':<20}  {'Phase (dec)':<14}  {'Counts':>6}  {'Prob':>7}")
    print("  " + "─" * 52)

    for bits, count in sorted_counts[:12]:
        phase_int = int(bits, 2)
        phase_frac = phase_int / (2 ** n_count)
        print(f"  {bits:<20}  {phase_frac:<14.6f}  {count:>6}  {count/total*100:>5.1f}%")

    if len(sorted_counts) > 12:
        print(f"  … ({len(sorted_counts) - 12} more low-probability states)")
    print()


def plot_counts(counts: dict, N: int, a: int, n_count: int) -> None:
    total  = sum(counts.values())
    # Convert bitstrings to decimal phase integers for x-axis
    phases = {int(k, 2): v for k, v in counts.items()}
    phases = dict(sorted(phases.items()))

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(
        [str(k) for k in phases.keys()],
        phases.values(),
        color="#534AB7",
        edgecolor="none",
        width=0.8,
    )
    ax.set_xlabel(f"Measured phase value (0 … {2**n_count - 1})", fontsize=11)
    ax.set_ylabel("Counts", fontsize=11)
    ax.set_title(
        f"Shor's Algorithm  |  N={N}, a={a}  |  {SHOTS} shots",
        fontsize=12, pad=10,
    )
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    plt.tight_layout()
    plt.savefig("shor_results.png", dpi=150)
    print("  ✓  Histogram saved  : shor_results.png")
    plt.show()


def write_output_csv(counts: dict, n_count: int, out_path: str) -> None:
    """
    Write raw phase samples to shor_output.csv for classical post-processing.
    Each row is one measured bitstring with its decimal phase value and count.
    """
    total = sum(counts.values())
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bitstring", "phase_int", "phase_frac", "counts", "n_count"])
        for bits, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            phase_int  = int(bits, 2)
            phase_frac = phase_int / (2 ** n_count)
            writer.writerow([bits, phase_int, f"{phase_frac:.8f}", count, n_count])
    print(f"  ✓  Phase samples saved : {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    csv_in     = os.path.join(base_dir, "shor_input.csv")
    csv_out    = os.path.join(base_dir, "shor_output.csv")

    N, a, n_count, n_target = read_input(csv_in)

    print("=" * 60)
    print("  Shor's Algorithm — Quantum Period Finding")
    print("=" * 60)
    print(f"  N               : {N}")
    print(f"  a               : {a}")
    print(f"  Function        : f(x) = {a}ˣ mod {N}")
    print(f"  Counting qubits : {n_count}")
    print(f"  Target qubits   : {n_target}")
    print(f"  Total qubits    : {n_count + n_target}")
    print(f"  Shots           : {SHOTS}")
    print("=" * 60)

    print("\nBuilding Shor circuit …")
    qc = build_shor_circuit(N, a, n_count, n_target)

    # Text circuit (decomposed for readability)
    print("\n── Circuit (text, decomposed) ──────────────────────────────")
    print(qc.decompose(reps=1).draw(output="text", fold=120))

    # Matplotlib circuit diagram
    try:
        fig = qc.decompose(reps=1).draw(output="mpl", fold=25, style="bw")
        fig.savefig("shor_circuit.png", dpi=150, bbox_inches="tight")
        print("  ✓  Circuit diagram saved : shor_circuit.png")
        plt.show()
    except Exception as exc:
        print(f"  (Matplotlib circuit diagram skipped: {exc})")

    print(f"\nRunning simulation ({SHOTS} shots) on AerSimulator …")
    counts = simulate(qc)

    print_counts(counts, n_count)
    write_output_csv(counts, n_count, csv_out)
    plot_counts(counts, N, a, n_count)

    # ── Classical period verification ─────────────────────────────────────────
    print("── Period (classical verification) ─────────────────────────")
    r_classical, val = 1, a % N
    while val != 1 and r_classical <= N:
        val = (val * a) % N
        r_classical += 1
    if val == 1:
        print(f"  Periodicity     : p = {r_classical}  (i.e. {a}^{r_classical} mod {N} = 1)")
    else:
        print(f"  Periodicity     : could not find period for a={a}, N={N}")
    print()

    print("  Run  shor_classical_post.py  to extract the factors.\n")


if __name__ == "__main__":
    main()
