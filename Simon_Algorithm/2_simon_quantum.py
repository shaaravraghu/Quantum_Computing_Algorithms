import pandas as pd
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def load_simon_oracle(file_path):
    df = pd.read_csv(file_path, dtype=str).fillna("")
    n = int(df.iloc[0, 0])

    # 2n qubits: n for input, n for output (ancilla)
    oracle_qc = QuantumCircuit(2 * n)

    for _, row in df.iterrows():
        in_str = str(row["x"]).strip().zfill(n)
        out_str = str(row["f(x)"]).strip().zfill(n)

        # 1. Prepare input state match
        for i, bit in enumerate(reversed(in_str)):
            if bit == "0":
                oracle_qc.x(i)

        # 2. Multi-Controlled bit flip for each '1' in the output string
        # If input is 'in_str', XOR 'out_str' into the ancilla register
        for j, out_bit in enumerate(reversed(out_str)):
            if out_bit == "1":
                # mcx controlled by all input qubits, targeting ancilla j
                oracle_qc.mcx(list(range(n)), n + j)

        # 3. Restore input state
        for i, bit in enumerate(reversed(in_str)):
            if bit == "0":
                oracle_qc.x(i)
        oracle_qc.barrier()

    return oracle_qc, n


def run_simon(file_path):
    oracle, n = load_simon_oracle(file_path)
    qc = QuantumCircuit(2 * n, n)
    qc.h(range(n))
    qc.barrier()
    qc.compose(oracle, inplace=True)
    qc.barrier()
    qc.h(range(n))
    qc.measure(range(n), range(n))

    sim = AerSimulator()
    unique_y = set()
    print("Collecting equations...")

    with open("simon_data.txt", "w") as f:
        f.write(f"{n}\n")
        while len(unique_y) < n:
            res = sim.run(qc, shots=1, memory=True).result()
            y = res.get_memory()[0]
            if y not in unique_y:
                unique_y.add(y)
                f.write(f"{y}\n")
                print(f"Captured: {y}")
                
    import matplotlib.pyplot as plt

    # 1. Convert the messy Oracle into a single clean 'Block' for the Full Circuit
    oracle_instruction = oracle.to_instruction(label=" Simon Oracle \n (CSV Defined) ")
    
    # Create a 'Display' version of the full circuit
    display_qc = QuantumCircuit(2 * n, n)
    display_qc.h(range(n))
    display_qc.barrier()
    display_qc.append(oracle_instruction, range(2 * n)) # Adds the whole oracle as one box
    display_qc.barrier()
    display_qc.h(range(n))
    display_qc.measure(range(n), range(n))

    print("\n[Visualizing...] Generating High-Res Diagrams...")

    # 2. Draw the Full High-Level Circuit
    # 'mpl' output requires the 'matplotlib' and 'pylatexenc' libraries
    try:
        # High-level view (The Box)
        display_qc.draw(output='mpl', style='iqp', filename='simon_full_circuit.png')
        print("✔ Saved 'simon_full_circuit.png' (High-level view)")

        # Deep-dive view (The Truth Table Guts)
        # We 'decompose' it once to see the internal MCX gates clearly
        oracle.decompose().draw(output='mpl', style='bw', plot_barriers=False, 
                                filename='simon_oracle_details.png', scale=0.7)
        print("✔ Saved 'simon_oracle_details.png' (Truth Table logic)")
        
        # Show them if in a Jupyter environment
        plt.show()
    except Exception as e:
        print(f"Note: Matplotlib draw failed ({e}). Falling back to compact text...")
        print(display_qc.draw(output='text', fold=-1))


run_simon("1_function_design.csv")
