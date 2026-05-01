"""
shor_quantum_IBM.py
-------------------
Shor's Algorithm — IBM Quantum Runtime version
qiskit version 1.4.5

Same as shor_quantum.py but runs on real IBM hardware via Qiskit Runtime.
Run shor_input_gen.py first, then this file, then shor_classical_post.py.
"""

import csv
import math
import os
import sys

import numpy as np

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit.circuit.library import QFT, UnitaryGate
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    import matplotlib.pyplot as plt
except ImportError as exc:
    sys.exit(
        f"Import error: {exc}\nInstall with: pip install qiskit qiskit-aer qiskit-ibm-runtime matplotlib numpy"
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

SHOTS = int(input("Enter the number of shots: "))


def read_input(csv_path):
    if not os.path.exists(csv_path):
        sys.exit(f"  ✗  '{csv_path}' not found.\n     Run shor_input_gen.py first.")
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("  ✗  CSV is empty. Re-run shor_input_gen.py.")
    row = rows[0]
    try:
        N = int(row["N"].strip())
        a = int(row["a"].strip())
        n_count = int(row["n_count"].strip())
        n_target = int(row["n_target"].strip())
    except (KeyError, ValueError) as e:
        sys.exit(f"  ✗  Bad CSV format: {e}")
    return N, a, n_count, n_target


def mod_exp_unitary(a, power, N, n_target):
    dim = 2**n_target
    U = np.zeros((dim, dim), dtype=complex)
    mult = pow(int(a), int(power), int(N))
    for y in range(dim):
        image = (y * mult) % N if y < N else y
        U[image][y] = 1.0
    return U


def controlled_mod_exp(a, N, n_count, n_target):
    qr_count = QuantumRegister(n_count, "count")
    qr_target = QuantumRegister(n_target, "target")
    qc = QuantumCircuit(qr_count, qr_target, name="ModExp")
    for j in range(n_count):
        power = 2**j
        U_mat = mod_exp_unitary(a, power, N, n_target)
        U_gate = UnitaryGate(U_mat, label=f"U^{power}").control(1)
        qc.append(U_gate, [qr_count[j]] + list(qr_target))
    return qc


def build_shor_circuit(N, a, n_count, n_target):
    qr_count = QuantumRegister(n_count, "count")
    qr_target = QuantumRegister(n_target, "target")
    cr = ClassicalRegister(n_count, "c")
    qc = QuantumCircuit(qr_count, qr_target, cr)
    qc.h(qr_count)
    qc.barrier(label="superposition")
    qc.x(qr_target[0])
    qc.barrier(label="|1⟩ init")
    mod_exp = controlled_mod_exp(a, N, n_count, n_target)
    qc.append(mod_exp, list(qr_count) + list(qr_target))
    qc.barrier(label="mod exp")
    iqft = QFT(n_count, inverse=True, do_swaps=True, name="IQFT")
    qc.append(iqft, qr_count)
    qc.barrier(label="IQFT")
    qc.measure(qr_count, cr)
    return qc


def print_counts(counts, n_count):
    total = sum(counts.values())
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    print("\n── Raw Measurement Results (counting register) ──────────────")
    print(f"  {'Bitstring':<20}  {'Phase (dec)':<14}  {'Counts':>6}  {'Prob':>7}")
    print("  " + "─" * 52)
    for bits, count in sorted_counts[:12]:
        phase_int = int(bits, 2)
        phase_frac = phase_int / (2**n_count)
        print(
            f"  {bits:<20}  {phase_frac:<14.6f}  {count:>6}  {count/total*100:>5.1f}%"
        )
    if len(sorted_counts) > 12:
        print(f"  … ({len(sorted_counts) - 12} more low-probability states)")
    print()


def plot_counts(counts, N, a, n_count):
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
        f"Shor's Algorithm  |  N={N}, a={a}  |  {SHOTS} shots  |  IBM Hardware",
        fontsize=12,
        pad=10,
    )
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    plt.tight_layout()
    plt.savefig("shor_results_IBM.png", dpi=150)
    print("  ✓  Histogram saved  : shor_results_IBM.png")
    plt.show()


def write_output_csv(counts, n_count, out_path):
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bitstring", "phase_int", "phase_frac", "counts", "n_count"])
        for bits, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            phase_int = int(bits, 2)
            phase_frac = phase_int / (2**n_count)
            writer.writerow([bits, phase_int, f"{phase_frac:.8f}", count, n_count])
    print(f"  ✓  Phase samples saved : {out_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_in = os.path.join(base_dir, "shor_input.csv")
    csv_out = os.path.join(base_dir, "shor_output.csv")

    N, a, n_count, n_target = read_input(csv_in)

    print("=" * 60)
    print("  Shor's Algorithm — IBM Quantum Hardware Run")
    print("=" * 60)
    print(f"  N               : {N}")
    print(f"  a               : {a}")
    print(f"  Function        : f(x) = {a}ˣ mod {N}")
    print(f"  Counting qubits : {n_count}")
    print(f"  Target qubits   : {n_target}")
    print(f"  Total qubits    : {n_count + n_target}")
    print(f"  Shots           : {SHOTS}")
    print(f"  Backend         : {backend.name}")
    print("=" * 60)

    print("\nBuilding Shor circuit …")
    qc = build_shor_circuit(N, a, n_count, n_target)

    print("\n── Circuit (text, decomposed) ──────────────────────────────")
    print(qc.decompose(reps=1).draw(output="text", fold=120))

    try:
        fig = qc.decompose(reps=1).draw(output="mpl", fold=25, style="bw")
        fig.savefig("shor_circuit.png", dpi=150, bbox_inches="tight")
        print("  ✓  Circuit diagram saved : shor_circuit.png")
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

    print_counts(counts, n_count)
    write_output_csv(counts, n_count, csv_out)
    plot_counts(counts, N, a, n_count)

    print("── Period (classical verification) ─────────────────────────")
    r_classical, val = 1, a % N
    while val != 1 and r_classical <= N:
        val = (val * a) % N
        r_classical += 1
    if val == 1:
        print(
            f"  Periodicity     : p = {r_classical}  (i.e. {a}^{r_classical} mod {N} = 1)"
        )
    else:
        print(f"  Periodicity     : could not find period for a={a}, N={N}")
    print()
    print("  Run  shor_classical_post.py  to extract the factors.\n")


main()
