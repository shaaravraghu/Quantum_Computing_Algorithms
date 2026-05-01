This is the CSV simulation of Shor's factoring algorithm.
How to use:

1. Run the 1_shor_input_gen.py file.
Enter the number to factor (N) and the base (a) when prompted.
The file runs classical pre-checks (primality, GCD, even number) before proceeding.
If the checks pass, it saves the configuration to shor_input.csv.
Make sure the CSV file is not open in the background while running this file, as it will not be edited.

2. Run the 2_shor_quantum.py file.
This file has Qiskit included and reads shor_input.csv to build the quantum period-finding circuit.
It applies the QFT register, modular exponentiation, and inverse QFT.

For the IBM Implementation, enter your IBM Credentials and run the IBM Script file. Note the differences.
The circuit is visualized using matplotlib and saved as shor_circuit.png.
The raw phase measurement samples are saved to shor_output.csv.
Make sure you are in the directory where these files reside.

3. Run the 3_shor_classical_post.py file.
This file has Qiskit not included in it. This is purely classical.
It reads shor_output.csv and applies continued fractions to extract period candidates.
It validates each candidate and computes GCD to recover the factors.
Make sure you are in the directory where these files reside.

Output: The two factors p and q such that N = p × q.

Inputs worth testing: 

1. N=15, a=7
2. N=21, a=2
