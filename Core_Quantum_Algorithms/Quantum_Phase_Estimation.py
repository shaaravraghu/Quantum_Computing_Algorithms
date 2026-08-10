import numpy as np


# ---------------------------------------------------------
# Basic quantum gates
# ---------------------------------------------------------

H = (1 / np.sqrt(2)) * np.array([
    [1,  1],
    [1, -1]
], dtype=complex)


# ---------------------------------------------------------
# Quantum Fourier Transform
# ---------------------------------------------------------

def qft(state):
    """
    Apply QFT to a quantum state vector.
    """
    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):
        for x in range(N):
            result[y] += state[x] * np.exp(
                2j * np.pi * x * y / N
            )

    return result / np.sqrt(N)


def inverse_qft(state):
    """
    Apply inverse QFT.
    """
    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):
        for x in range(N):
            result[y] += state[x] * np.exp(
                -2j * np.pi * x * y / N
            )

    return result / np.sqrt(N)


# ---------------------------------------------------------
# QPE
# ---------------------------------------------------------

def quantum_phase_estimation(theta, n_qubits):
    """
    Estimate the phase theta using QPE.

    theta:
        Phase in [0, 1)

    n_qubits:
        Number of phase-estimation qubits
    """

    N = 2 ** n_qubits

    # -----------------------------------------------------
    # Step 1: Create uniform superposition
    #
    # |0...0> -> (1/sqrt(N)) sum_k |k>
    # -----------------------------------------------------

    state = np.ones(N, dtype=complex) / np.sqrt(N)

    # -----------------------------------------------------
    # Step 2:
    #
    # Controlled-U^(2^k) operations encode the phase.
    #
    # For eigenstate |psi>:
    #
    # U^(2^k)|psi>
    #     = exp(2*pi*i*theta*2^k)|psi>
    #
    # This creates:
    #
    # sum_k exp(2*pi*i*theta*k)|k>
    # -----------------------------------------------------

    for k in range(N):

        state[k] *= np.exp(
            2j * np.pi * theta * k
        )

    # -----------------------------------------------------
    # Step 3: Apply inverse QFT
    # -----------------------------------------------------

    state = inverse_qft(state)

    # -----------------------------------------------------
    # Step 4: Measurement probabilities
    # -----------------------------------------------------

    probabilities = np.abs(state) ** 2

    # Most probable state
    measured_value = np.argmax(probabilities)

    # Convert binary integer -> phase
    estimated_phase = measured_value / N

    return estimated_phase, probabilities


# ---------------------------------------------------------
# Run QPE
# ---------------------------------------------------------

theta = 1 / 8
n_qubits = 3

estimated_phase, probabilities = quantum_phase_estimation(
    theta,
    n_qubits
)

print("Actual phase:   ", theta)
print("Estimated phase:", estimated_phase)

print("\nMeasurement probabilities:")

for i, probability in enumerate(probabilities):

    if probability > 1e-10:
        binary = format(i, f"0{n_qubits}b")

        print(
            f"|{binary}> : {probability:.4f}"
        )
