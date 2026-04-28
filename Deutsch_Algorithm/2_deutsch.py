# Deutsch Algorithm implementation using CSV-defined Oracles
# qiskit version 1.4.5
import pandas as pd
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def load_oracle_from_csv(file_path):
    # Load CSV and ensure strings to preserve '0'
    df = pd.read_csv(file_path, dtype=str).fillna("")

    # For Deutsch Algorithm, num_qubits should be 1
    num_qubits = 1

    # Circuit: 1 input qubit + 1 ancilla = 2 qubits
    oracle_qc = QuantumCircuit(num_qubits + 1)

    ## For minimum number of gates
    # Count how many rows have an output of "1"
    outputs = df["f(x)"].astype(str).str.strip()
    ones_count = (outputs == "1").sum()
    total_possible_inputs = 2**num_qubits

    if ones_count == 0:
        # Constant 0: The oracle does nothing
        print("Optimization: Detected Constant 0. Oracle remains Identity.")
        return oracle_qc, num_qubits

    if ones_count == total_possible_inputs:
        # Constant 1: Just flip the ancilla once for all inputs
        print("Optimization: Detected Constant 1. Applying single X gate to ancilla.")
        oracle_qc.x(num_qubits)
        return oracle_qc, num_qubits

    for index, row in df.iterrows():
        output_val = str(row["f(x)"]).strip()
        input_str = str(row["x"]).strip()

        if output_val == "1":
            bit_string = input_str.zfill(num_qubits)
            print(f"Adding Oracle Logic for f({bit_string}) = 1")

            # 1. Flip X for '0' bits
            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            # 2. Controlled-X (since n=1, mcx is just a CNOT)
            oracle_qc.mcx(list(range(num_qubits)), num_qubits)

            # 3. Restore state
            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.barrier()

    return oracle_qc, num_qubits


def run_deutsch_experiment(file_path, shots):
    # 1. Build the Oracle
    oracle_f, n = load_oracle_from_csv(file_path)

    if n != 1:
        print(
            f"Warning: Deutsch Algorithm usually uses 1 input qubit. CSV defines {n}."
        )

    # 2. Construct Deutsch Circuit (n input + 1 ancilla)
    # n=1 means a 2-qubit circuit with 1 classical bit
    deutsch_circuit = QuantumCircuit(n + 1, n)

    # Initialization
    deutsch_circuit.x(n)  # Ancilla to |1>
    deutsch_circuit.h(range(n + 1))  # All to superposition
    deutsch_circuit.barrier()

    # Add Oracle
    deutsch_circuit.compose(oracle_f, inplace=True)
    deutsch_circuit.barrier()

    # Interference
    deutsch_circuit.h(range(n))
    deutsch_circuit.measure(range(n), range(n))

    # 3. Execute
    simulator = AerSimulator()
    job = simulator.run(deutsch_circuit, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # 4. Analysis
    # In Deutsch: '0' means Constant, '1' means Balanced
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
        print(f"Conclusion: Non-standard function.")

    # --- PRINTING ---
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
