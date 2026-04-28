# Deutsch-Jozsa Algorithm — IBM Quantum Runtime version
# qiskit version 1.4.5
import pandas as pd
import numpy as np
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# ── IBM Credentials ───────────────────────────────────────────────────────────
IBM_API_TOKEN = "qlFu1fi7gSOP6e8kiSEUpHhhHhxA5ws1Z4_1HniBxMrY"
IBM_INSTANCE = "crn:v1:bluemix:public:quantum-computing:us-east:a/2d091361e27946c7aca67f1f1f888383:ec5c14bb-e0f4-40f4-82de-5b2ebf6d4341::"

service = QiskitRuntimeService(
    channel="ibm_quantum_platform", token=IBM_API_TOKEN, instance=IBM_INSTANCE
)
backend = service.least_busy(operational=True, simulator=False)
print(f"Running on: {backend.name}")
# ─────────────────────────────────────────────────────────────────────────────


def load_oracle_from_csv(file_path):
    df = pd.read_csv(file_path, dtype=str).fillna("")
    num_qubits = int(df.iloc[0, 0])
    oracle_qc = QuantumCircuit(num_qubits + 1)

    outputs = df["f(x)"].astype(str).str.strip()
    ones_count = (outputs == "1").sum()
    total_possible_inputs = 2**num_qubits

    if ones_count == 0:
        print("Optimization: Detected Constant 0. Oracle remains Identity.")
        return oracle_qc, num_qubits

    if ones_count == total_possible_inputs:
        print("Optimization: Detected Constant 1. Applying single X gate to ancilla.")
        oracle_qc.x(num_qubits)
        return oracle_qc, num_qubits

    for index, row in df.iterrows():
        output_val = str(row["f(x)"]).strip()
        input_str = str(row["x"]).strip()

        if output_val == "1":
            bit_string = input_str.zfill(num_qubits)
            print(f"Adding Oracle Logic for input: {bit_string}")

            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.mcx(list(range(num_qubits)), num_qubits)

            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.barrier()

    return oracle_qc, num_qubits


def run_dj_experiment(file_path, shots):
    oracle_f, n = load_oracle_from_csv(file_path)

    dj_circuit = QuantumCircuit(n + 1, n)
    dj_circuit.x(n)
    dj_circuit.h(range(n + 1))
    dj_circuit.barrier()
    dj_circuit.compose(oracle_f, inplace=True)
    dj_circuit.barrier()
    dj_circuit.h(range(n))
    dj_circuit.measure(range(n), range(n))

    # Transpile and run on IBM
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(dj_circuit)
    job = Sampler(backend).run([isa_circuit], shots=shots)
    print(f"Job ID: {job.job_id()} | Waiting for results...")
    result = job.result()
    counts = result[0].data.c.get_counts()

    zero_string = "0" * n
    zero_count = counts.get(zero_string, 0)
    prob_zero = (zero_count / shots) * 100

    print("-" * 30)
    print(f"RESULTS FOR {n} QUBITS")
    print("-" * 30)
    print(f"Measurement Counts: {counts}")
    print(f"Probability of 'All-Zeros' ({zero_string}): {prob_zero:.2f}%")

    if prob_zero > 90:
        print("Conclusion: Function is Perfectly CONSTANT")
    elif prob_zero < 10:
        print("Conclusion: Function is Perfectly BALANCED")
    else:
        print(f"Conclusion: NON-PROMISE Function (or noise affected results).")
        print(f"The interference is {prob_zero:.1f}% constructive.")

    print("\n" + "=" * 40)
    print(" 1. ORACLE STRUCTURE (The Truth Table) ")
    print("=" * 40)
    print(oracle_f.draw(output="text"))

    print("\n" + "=" * 40)
    print(" 2. FULL DJ CIRCUIT (Initialization + Oracle + Interference) ")
    print("=" * 40)
    print(dj_circuit.draw(output="text", fold=-1))


# --- Execution ---
shots = int(input("Enter the number of shots: "))
try:
    run_dj_experiment("1_function_design.csv", shots)
except Exception as e:
    print(
        f"Error: {e}. Please ensure 'function_design.csv' exists and is formatted correctly."
    )
