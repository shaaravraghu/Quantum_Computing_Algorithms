# No case number required as the function itself is defined in a separate file.
# The oracle gate is created on the basis of the input csv file.

# qiskit version 1.4.5
import pandas as pd
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def load_oracle_from_csv(file_path):
    # FORCE everything to be read as a string to preserve leading zeros
    df = pd.read_csv(file_path, dtype=str).fillna("")

    # Extract number of qubits from the first row of the first column
    num_qubits = int(df.iloc[0, 0])

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
        # Clean the data: remove spaces and ensure it's a string
        output_val = str(row["f(x)"]).strip()
        input_str = str(row["x"]).strip()

        if output_val == "1":
            # Ensure the bit string is exactly the right length (e.g., '0' becomes '000')
            bit_string = input_str.zfill(num_qubits)

            # Debug Print: So you can see it working in the console
            print(f"Adding Oracle Logic for input: {bit_string}")

            # 1. Flip X for '0' bits
            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            # 2. Multi-Controlled X
            oracle_qc.mcx(list(range(num_qubits)), num_qubits)

            # 3. Restore state
            for i, bit in enumerate(reversed(bit_string)):
                if bit == "0":
                    oracle_qc.x(i)

            oracle_qc.barrier()

    return oracle_qc, num_qubits


def run_dj_experiment(file_path, shots):
    # 1. Build the Oracle from the Professor's CSV
    oracle_f, n = load_oracle_from_csv(file_path)

    # 2. Construct the full DJ Circuit
    dj_circuit = QuantumCircuit(n + 1, n)

    # Initialization
    dj_circuit.x(n)  # Put ancilla in |1>
    dj_circuit.h(range(n + 1))  # Put all in superposition
    dj_circuit.barrier()

    # Add Oracle
    dj_circuit.compose(oracle_f, inplace=True)
    dj_circuit.barrier()

    # Interference
    dj_circuit.h(range(n))
    dj_circuit.measure(range(n), range(n))

    # 3. Execute
    simulator = AerSimulator()
    job = simulator.run(dj_circuit, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # 4. Analysis
    zero_string = "0" * n
    zero_count = counts.get(zero_string, 0)
    prob_zero = (zero_count / shots) * 100

    print("-" * 30)
    print(f"RESULTS FOR {n} QUBITS")
    print("-" * 30)
    print(f"Measurement Counts: {counts}")
    print(f"Probability of 'All-Zeros' ({zero_string}): {prob_zero:.2f}%")

    # Judge based on interference
    if prob_zero > 99:
        print("Conclusion: Function is Perfectly CONSTANT")
    elif prob_zero < 1:
        print("Conclusion: Function is Perfectly BALANCED")
    else:
        print(f"Conclusion: NON-PROMISE Function (Broken DJ).")
        print(f"The interference is {prob_zero:.1f}% constructive.")

    # --- PRINTING THE CIRCUITS ---
    print("\n" + "=" * 40)
    print(" 1. ORACLE STRUCTURE (The Truth Table) ")
    print("=" * 40)
    print(oracle_f.draw(output="text"))

    print("\n" + "=" * 40)
    print(" 2. FULL DJ CIRCUIT (Initialization + Oracle + Interference) ")
    print("=" * 40)
    # Using fold=-1 prevents the circuit from breaking into multiple lines
    print(dj_circuit.draw(output="text", fold=-1))
    
    # Extract the measured string
    measured_string = list(counts.keys())[0]
    print(f"The output of Bernstein-vazirani is- {measured_string}")


# --- Execution ---
# Ensure you have created 'function_design.csv' in the same folder
shots = int(input("Enter the number of shots: "))
try:
    run_dj_experiment("1_function_design.csv", shots)
except Exception as e:
    print(
        f"Error: {e}. Please ensure 'function_design.csv' exists and is formatted correctly."
    )
