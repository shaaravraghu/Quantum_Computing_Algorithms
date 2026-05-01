This is the CSV simulation of Grover's search algorithm.
How to use:

1. In the 1_grover_input.csv file, enter the truth table of the function to be searched by the grover's Search ALgorithm.
Make sure that all the rows begin with the number of qubits, unlike the previous inputs. 
As per the number of qubits, enter all the possible inputs and set only one output value (f(x)) to 1, keeping the rest as 0.
Save the csv file before proceeding further.

2. Run the 2_grover_quantum.py file.
This file has Qiskit included and reads grover_input.csv to build the Grover circuit.
It runs the oracle and diffuser for the optimal number of iterations (≈ π/4 · √(2^n)).

For the IBM Implementation, Enter your credentials in the IBM Script and run the same. The total number of shots is hardcoded to 2048, you can vary the same for your customised inputs.

The circuit is visualized using matplotlib and saved as grover_circuit.png.
The measurement histogram is saved as grover_results.png.
Make sure you are in the directory where these files reside.

Note the difference in SImulation and implementation and summarise your results.

Output: The marked target state, found with high probability.

Recommendation: begin from n=3 gradually till higher n's for better visualisation of the amplified state.
The circuit's matplotlib visualisation will get clumsier as the n increases.