import numpy as np


# ============================================================
# AMPLITUDE ESTIMATION
# ============================================================

def qft_inverse(state):
    """
    Inverse QFT.
    """
    N = len(state)

    result = np.zeros(N, dtype=complex)

    for y in range(N):

        for x in range(N):

            result[y] += (
                state[x]
                * np.exp(-2j * np.pi * x * y / N)
            )

    return result / np.sqrt(N)


def amplitude_estimation(amplitude, precision_qubits):

    # --------------------------------------------------------
    # a = sin²(theta)
    # --------------------------------------------------------

    theta = np.arcsin(np.sqrt(amplitude))

    N = 2 ** precision_qubits

    # --------------------------------------------------------
    # Phase register state
    # --------------------------------------------------------

    state = np.zeros(N, dtype=complex)

    for k in range(N):

        state[k] = np.exp(
            2j * np.pi * k * theta
        )

    state /= np.sqrt(N)

    # --------------------------------------------------------
    # Inverse QFT
    # --------------------------------------------------------

    state = qft_inverse(state)

    probabilities = np.abs(state) ** 2

    measured = int(np.argmax(probabilities))

    estimated_theta = measured / N

    # --------------------------------------------------------
    # Recover amplitude
    # a = sin²(theta)
    # --------------------------------------------------------

    estimated_amplitude = (
        np.sin(np.pi * estimated_theta) ** 2
    )

    return (
        estimated_amplitude,
        probabilities,
        measured
    )


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("          AMPLITUDE ESTIMATION")
        print("=" * 55)

        print("1. Estimate amplitude")
        print("2. Compare different precision levels")
        print("3. Run predefined examples")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            amplitude = float(
                input("Enter actual amplitude (0 to 1): ")
            )

            precision = int(
                input("Number of precision qubits: ")
            )

            estimated, probabilities, measured = (
                amplitude_estimation(
                    amplitude,
                    precision
                )
            )

            print("\nActual amplitude:    ", amplitude)
            print("Estimated amplitude: ", estimated)

            print(
                "Measured phase index:",
                measured
            )

            print(
                "Absolute error:      ",
                abs(amplitude - estimated)
            )

        elif choice == "2":

            amplitude = float(
                input("Enter actual amplitude (0 to 1): ")
            )

            print("\nPrecision comparison:")

            for precision in range(2, 9):

                estimated, _, _ = amplitude_estimation(
                    amplitude,
                    precision
                )

                error = abs(
                    amplitude - estimated
                )

                print(
                    f"{precision} qubits -> "
                    f"{estimated:.8f} "
                    f"(error={error:.8f})"
                )

        elif choice == "3":

            examples = [
                0.10,
                0.25,
                0.50,
                0.75,
                0.90
            ]

            precision = 6

            print(
                f"\nUsing {precision} precision qubits:\n"
            )

            for amplitude in examples:

                estimated, _, _ = (
                    amplitude_estimation(
                        amplitude,
                        precision
                    )
                )

                print(
                    f"Actual = {amplitude:.2f}   "
                    f"Estimated = {estimated:.6f}"
                )

        elif choice == "4":

            print("Exiting...")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
