import numpy as np


# ============================================================
# TROTTER-SUZUKI DECOMPOSITION
# ============================================================

I = np.eye(2, dtype=complex)

X = np.array([
    [0, 1],
    [1, 0]
], dtype=complex)

Z = np.array([
    [1, 0],
    [0, -1]
], dtype=complex)


def kron(A, B):
    return np.kron(A, B)


def matrix_exponential(H, time):
    """
    Compute exp(-iHt) using eigendecomposition.
    """

    eigenvalues, eigenvectors = np.linalg.eigh(H)

    return (
        eigenvectors
        @ np.diag(
            np.exp(-1j * eigenvalues * time)
        )
        @ eigenvectors.conj().T
    )


def exact_evolution(A, B, t):

    H = A + B

    return matrix_exponential(
        H,
        t
    )


def trotter_evolution(A, B, t, steps):

    dt = t / steps

    UA = matrix_exponential(
        A,
        dt
    )

    UB = matrix_exponential(
        B,
        dt
    )

    step = UA @ UB

    result = np.eye(
        len(A),
        dtype=complex
    )

    for _ in range(steps):
        result = result @ step

    return result


def error(U_exact, U_trotter):

    return np.linalg.norm(
        U_exact - U_trotter
    )


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("          TROTTER-SUZUKI DECOMPOSITION")
        print("=" * 60)

        print("1. A = X⊗X, B = Z⊗Z")
        print("2. A = X, B = Z")
        print("3. Compare Trotter steps")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "4":
            break

        if choice == "1":

            A = kron(X, X)
            B = kron(Z, Z)

        elif choice == "2":

            A = X
            B = Z

        elif choice == "3":

            A = kron(X, X)
            B = kron(Z, Z)

            t = float(
                input("Evolution time t: ")
            )

            exact = exact_evolution(
                A,
                B,
                t
            )

            print("\nTrotter approximation errors:")

            for steps in [1, 2, 4, 8, 16, 32]:

                approximation = (
                    trotter_evolution(
                        A,
                        B,
                        t,
                        steps
                    )
                )

                print(
                    f"Steps = {steps:2} "
                    f"Error = {error(exact, approximation):.8f}"
                )

            continue

        else:

            print("Invalid choice.")
            continue

        t = float(
            input("Evolution time t: ")
        )

        steps = int(
            input("Number of Trotter steps: ")
        )

        exact = exact_evolution(
            A,
            B,
            t
        )

        approximation = trotter_evolution(
            A,
            B,
            t,
            steps
        )

        print(
            "\nApproximation error:",
            error(exact, approximation)
        )


if __name__ == "__main__":
    main()
