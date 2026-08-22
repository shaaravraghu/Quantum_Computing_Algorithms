import numpy as np


# ============================================================
# HAMILTONIAN SIMULATION
# ============================================================

I = np.eye(2, dtype=complex)

X = np.array([
    [0, 1],
    [1, 0]
], dtype=complex)

Y = np.array([
    [0, -1j],
    [1j, 0]
], dtype=complex)

Z = np.array([
    [1, 0],
    [0, -1]
], dtype=complex)


def kron(*matrices):
    result = matrices[0]

    for matrix in matrices[1:]:
        result = np.kron(result, matrix)

    return result


def evolve(hamiltonian, state, time):
    """
    Exact Hamiltonian evolution:

        |psi(t)> = exp(-iHt)|psi(0)>
    """

    eigenvalues, eigenvectors = np.linalg.eigh(
        hamiltonian
    )

    U = (
        eigenvectors
        @ np.diag(np.exp(-1j * eigenvalues * time))
        @ eigenvectors.conj().T
    )

    return U @ state


def expectation(hamiltonian, state):
    return np.real(
        np.vdot(state, hamiltonian @ state)
    )


def print_state(state):

    print("\nQuantum state:")

    n = int(np.log2(len(state)))

    for i, amplitude in enumerate(state):

        probability = abs(amplitude) ** 2

        if probability > 1e-10:

            print(
                f"|{i:0{n}b}> : "
                f"{amplitude.real:+.6f}"
                f"{amplitude.imag:+.6f}i"
                f"   P={probability:.6f}"
            )


def get_hamiltonian(choice):

    if choice == "1":
        # H = Z
        return Z

    if choice == "2":
        # H = X
        return X

    if choice == "3":
        # H = Z ⊗ Z
        return kron(Z, Z)

    if choice == "4":
        # H = X⊗X + Z⊗Z
        return kron(X, X) + kron(Z, Z)

    raise ValueError("Invalid Hamiltonian.")


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("             HAMILTONIAN SIMULATION")
        print("=" * 60)

        print("1. H = Z")
        print("2. H = X")
        print("3. H = Z ⊗ Z")
        print("4. H = X⊗X + Z⊗Z")
        print("5. Exit")

        choice = input("\nChoose Hamiltonian: ")

        if choice == "5":
            break

        try:
            H = get_hamiltonian(choice)

            dimension = len(H)

            state = np.zeros(
                dimension,
                dtype=complex
            )

            basis = int(
                input(
                    f"Initial basis state (0-{dimension-1}): "
                )
            )

            state[basis] = 1

            time = float(
                input("Evolution time t: ")
            )

            final_state = evolve(
                H,
                state,
                time
            )

            print_state(final_state)

            print(
                "\nEnergy expectation:",
                expectation(H, final_state)
            )

        except ValueError as error:
            print(error)


if __name__ == "__main__":
    main()
