# Direct Implementation
import numpy as np


def qft(state):
    """
    Quantum Fourier Transform.

    state: quantum state vector of length N
    """

    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):
        for x in range(N):

            phase = np.exp(
                2j * np.pi * x * y / N
            )

            result[y] += state[x] * phase

    return result / np.sqrt(N)


def inverse_qft(state):
    """
    Inverse Quantum Fourier Transform.
    """

    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):
        for x in range(N):

            phase = np.exp(
                -2j * np.pi * x * y / N
            )

            result[y] += state[x] * phase

    return result / np.sqrt(N)




# Test it on a Basis State
import numpy as np


# 3 qubits -> 8-dimensional state
state = np.zeros(8, dtype=complex)

# Prepare |3>
state[3] = 1


result = qft(state)


print("QFT(|3>):")

for i, amplitude in enumerate(result):

    print(
        f"|{i:03b}> : "
        f"{amplitude.real:.4f}"
        f"{amplitude.imag:+.4f}i"
    )



























# Verify QFT is reversible
state = np.zeros(8, dtype=complex)

# |3>
state[3] = 1


transformed = qft(state)

recovered = inverse_qft(transformed)


print("Original:")
print(state)

print("\nRecovered:")
print(np.round(recovered, 10))

































# QFT of a superposition
state = np.zeros(8, dtype=complex)

state[0] = 1 / np.sqrt(2)
state[4] = 1 / np.sqrt(2)


result = qft(state)


print("QFT result:")

for i, amplitude in enumerate(result):

    probability = abs(amplitude) ** 2

    print(
        f"|{i:03b}> : "
        f"{amplitude.real:.4f}"
        f"{amplitude.imag:+.4f}i"
        f"   P = {probability:.4f}"
    )




























# Matrix Version
import numpy as np


def qft_matrix(N):

    omega = np.exp(
        2j * np.pi / N
    )

    Q = np.zeros(
        (N, N),
        dtype=complex
    )

    for y in range(N):
        for x in range(N):

            Q[y, x] = (
                omega ** (x * y)
            ) / np.sqrt(N)

    return Q


Q = qft_matrix(8)

print(np.round(Q, 3))
