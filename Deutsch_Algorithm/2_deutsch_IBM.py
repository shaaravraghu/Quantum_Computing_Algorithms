# Deutsch Algorithm implementation using CSV-defined Oracles
# qiskit version 1.4.5 — IBM Quantum Runtime version
import pandas as pd
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# ── IBM Credentials ───────────────────────────────────────────────────────────
IBM_API_TOKEN = " "
IBM_INSTANCE  = " "

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=IBM_API_TOKEN, instance=IBM_INSTANCE)
backend = service.least_busy(operational=True, simulator=False)
print(f"Running on: {backend.name}")
# ─────────────────────────────────────────────────────────────────────────────


def load_oracle_from_csv(file_path):
    df = pd.read_csv(file_path, dtype=str).fillna("")
    num_qubits = 1
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
            print(f"Adding Oracle Logic for f({bit_string}) = 1")

            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.mcx(list(range(num_qubits)), num_qubits)

            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.barrier()

    return oracle_qc, num_qubits


def run_deutsch_experiment(file_path, shots):
    oracle_f, n = load_oracle_from_csv(file_path)

    if n != 1:
        print(f"Warning: Deutsch Algorithm usually uses 1 input qubit. CSV defines {n}.")

    deutsch_circuit = QuantumCircuit(n + 1, n)
    deutsch_circuit.x(n)
    deutsch_circuit.h(range(n + 1))
    deutsch_circuit.barrier()
    deutsch_circuit.compose(oracle_f, inplace=True)
    deutsch_circuit.barrier()
    deutsch_circuit.h(range(n))
    deutsch_circuit.measure(range(n), range(n))

    # Transpile and run on IBM
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(deutsch_circuit)
    job = Sampler(backend).run([isa_circuit], shots=shots)
    print(f"Job ID: {job.job_id()} | Waiting for results...")
    result = job.result()
    counts = result[0].data.c.get_counts()

    zero_count = counts.get("0", 0)
    prob_zero = (zero_count / shots) * 100

    print("-" * 30)
    print(f"DEUTSCH RESULTS (1 Input Qubit)")
    print("-" * 30)
    print(f"Measurement Counts: {counts}")

    if prob_zero > 99:
        print("Conclusion: Function is CONSTANT")
    elif prob_zero < 1:
        print("Conclusion: Function is BALANCED")
    else:
        print(f"Conclusion: Non-standard function (noise may have affected results).")

    print("\nORACLE:")
    print(oracle_f.draw(output="text"))
    print("\nFULL DEUTSCH CIRCUIT:")
    print(deutsch_circuit.draw(output="text", fold=-1))


# --- Execution ---
shots = int(input("Enter the number of shots: "))
try:
    run_deutsch_experiment("1_function_design.csv", shots)
except Exception as e:
    print(f"Error: {e}. Ensure 'function_design.csv' is correct.")
