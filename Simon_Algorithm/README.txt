This is the csv simulation of the simons algorithm.

How to use: 
1. Enter the function input and the output in the 1_function_design.csv file. The outputs must be such that the function is two-one, for the simon's algorithm to function properly.

2. Run the 2_simon_quantum.py, the quantum processing part. Since the circuit is large, matplotlib visualisation has been added for circuit visualization.
the particular file has qiskit included and will keep running till it extracts outputs for n unique inputs.
n being the string length.
the processed file is saved in simon_data.txt. That is a collection of all strings such that <z,c>(Inner product of z and c, c=secret string)=0.

For the IBM Quantum Implementation of the same program, Just run the IBM Version of the algorithm after entering all your credentials correctly, And then proceed to step 3. Note your results when the same algorithm runs on a noisy environment.

3. run the 3_simon_classical.py file. This file has qiskit not included in it. This is purely classical and solves n linear equations to obtain n bits of the string.
This file processes the simon_data.txt file and outputs the n-bit string.

make sure that you are in that particular directory where these files reside.

Output: The input(encoded) string.