import numpy as np


# ============================================================
# QUANTUM APPROXIMATE COUNTING
# ============================================================

def inverse_qft(state):

    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):

        for x in range(N):

            result[y] += (
                state[x]
                * np.exp(
                    -2j * np.pi * x * y / N
                )
            )

    return result / np.sqrt(N)


def approximate_count(
    total_items,
    marked_items,
    precision_qubits
):

    N = total_items
    M = marked_items

    if M <= 0 or M >= N:

        raise ValueError(
            "Marked items must satisfy 0 < M < N."
        )

    # --------------------------------------------------------
    # Marked fraction
    #
    # a = M / N
    # --------------------------------------------------------

    amplitude = M / N

    # a = sin²(theta)

    theta = np.arcsin(
        np.sqrt(amplitude)
    )

    # Phase estimation resolution

    P = 2 ** precision_qubits

    # --------------------------------------------------------
    # Create phase-estimation state
    # --------------------------------------------------------

    state = np.zeros(
        P,
        dtype=complex
    )

    for k in range(P):

        state[k] = np.exp(
            2j * np.pi * k * theta
        )

    state /= np.sqrt(P)

    # --------------------------------------------------------
    # Inverse QFT
    # --------------------------------------------------------

    state = inverse_qft(state)

    probabilities = np.abs(state) ** 2

    measured = int(
        np.argmax(probabilities)
    )

    estimated_theta = measured / P

    # --------------------------------------------------------
    # Recover marked fraction
    # --------------------------------------------------------

    estimated_fraction = (
        np.sin(
            np.pi * estimated_theta
        ) ** 2
    )

    # --------------------------------------------------------
    # Recover number of marked items
    # --------------------------------------------------------

    estimated_count = (
        N * estimated_fraction
    )

    return (
        estimated_count,
        estimated_fraction,
        probabilities,
        measured
    )


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("         QUANTUM APPROXIMATE COUNTING")
        print("=" * 60)

        print("1. Estimate number of marked items")
        print("2. Compare precision")
        print("3. Predefined examples")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            N = int(
                input("Total number of items N: ")
            )

            M = int(
                input("Actual marked items M: ")
            )

            precision = int(
                input("Precision qubits: ")
            )

            try:

                estimated, fraction, _, measured = (
                    approximate_count(
                        N,
                        M,
                        precision
                    )
                )

                print("\n" + "-" * 50)

                print(
                    f"Actual count:       {M}"
                )

                print(
                    f"Estimated count:    {estimated:.6f}"
                )

                print(
                    f"Actual fraction:     {M / N:.6f}"
                )

                print(
                    f"Estimated fraction: {fraction:.6f}"
                )

                print(
                    f"Measured index:     {measured}"
                )

                print(
                    f"Absolute error:     "
                    f"{abs(M - estimated):.6f}"
                )

            except ValueError as error:

                print(error)

        elif choice == "2":

            N = int(
                input("Total items N: ")
            )

            M = int(
                input("Actual marked items M: ")
            )

            print("\nPrecision comparison:")

            for precision in range(3, 11):

                try:

                    estimated, _, _, _ = (
                        approximate_count(
                            N,
                            M,
                            precision
                        )
                    )

                    error = abs(
                        M - estimated
                    )

                    print(
                        f"{precision:2} qubits -> "
                        f"estimate = {estimated:10.5f} | "
                        f"error = {error:.5f}"
                    )

                except ValueError as error:

                    print(error)

        elif choice == "3":

            examples = [
                (100, 10),
                (100, 25),
                (100, 50),
                (1000, 100),
                (1000, 250)
            ]

            precision = 8

            print(
                f"\nUsing {precision} precision qubits:\n"
            )

            for N, M in examples:

                estimated, _, _, _ = (
                    approximate_count(
                        N,
                        M,
                        precision
                    )
                )

                print(
                    f"N={N:4} | "
                    f"Actual={M:4} | "
                    f"Estimated={estimated:10.4f}"
                )

        elif choice == "4":

            print("Exiting...")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
