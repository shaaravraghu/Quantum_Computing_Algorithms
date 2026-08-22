import numpy as np


# ============================================================
# QPE + HAMILTONIAN SIMULATION
# ============================================================

Z = np.array([
    [1, 0],
    [0, -1]
], dtype=complex)


X = np.array([
    [0, 1],
    [1, 0]
], dtype=complex)


def matrix_exponential(H, t):

    eigenvalues, eigenvectors = np.linalg.eigh(H)

    return (
        eigenvectors
        @ np.diag(
            np.exp(-1j * eigenvalues * t)
        )
        @ eigenvectors.conj().T
    )


def inverse_qft(state):

    N = len(state)

    result = np.zeros(
        N,
        dtype=complex
    )

    for y in range(N):

        for x in range(N):

            result[y] += (
                state[x]
                * np.exp(
                    -2j * np.pi * x * y / N
                )
            )

    return result / np.sqrt(N)


def estimate_energy(
    energy,
    precision_qubits,
    evolution_time
):

    # Phase:
    #
    # exp(-iEt)
    #
    # phase = Et / 2π

    phase = (
        (energy * evolution_time)
        / (2 * np.pi)
    ) % 1

    N = 2 ** precision_qubits

    state = np.zeros(
        N,
        dtype=complex
    )

    for k in range(N):

        state[k] = np.exp(
            2j * np.pi * k * phase
        )

    state /= np.sqrt(N)

    state = inverse_qft(state)

    probabilities = np.abs(state) ** 2

    measured = int(
        np.argmax(probabilities)
    )

    estimated_phase = measured / N

    estimated_energy = (
        2 * np.pi
        * estimated_phase
        / evolution_time
    )

    return estimated_energy, probabilities


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("       QPE + HAMILTONIAN SIMULATION")
        print("=" * 60)

        print("1. H = Z")
        print("2. H = X")
        print("3. Custom eigenvalue")
        print("4. Precision comparison")
        print("5. Exit")

        choice = input("\nChoose an option: ")

        if choice == "5":
            break

        if choice == "1":

            eigenvalues = [1, -1]

            energy = float(
                input(
                    "Choose eigenvalue (+1 or -1): "
                )
            )

        elif choice == "2":

            eigenvalues = [1, -1]

            energy = float(
                input(
                    "Choose eigenvalue (+1 or -1): "
                )
            )

        elif choice == "3":

            energy = float(
                input("Enter eigenvalue E: ")
            )

        elif choice == "4":

            energy = float(
                input("Enter eigenvalue E: ")
            )

            t = float(
                input("Evolution time t: ")
            )

            print("\nPrecision comparison:")

            for qubits in range(3, 10):

                estimate, _ = estimate_energy(
                    energy,
                    qubits,
                    t
                )

                print(
                    f"{qubits} qubits -> "
                    f"E ≈ {estimate:.8f}"
                )

            continue

        else:

            print("Invalid choice.")
            continue

        t = float(
            input("Evolution time t: ")
        )

        qubits = int(
            input("Precision qubits: ")
        )

        estimate, probabilities = (
            estimate_energy(
                energy,
                qubits,
                t
            )
        )

        print("\nActual energy:", energy)
        print("Estimated energy:", estimate)

        print(
            "Absolute error:",
            abs(energy - estimate)
        )


if __name__ == "__main__":
    main()
