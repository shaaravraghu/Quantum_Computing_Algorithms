
import numpy as np


# ============================================================
# AMPLITUDE AMPLIFICATION
# ============================================================

def amplitude_amplification(N, marked_states, iterations=None):
    """
    Simulates amplitude amplification for N basis states.

    marked_states:
        List of indices considered "good".

    iterations:
        Number of Grover/amplitude-amplification iterations.
    """

    marked_states = list(marked_states)

    # Initial uniform superposition
    state = np.ones(N, dtype=complex) / np.sqrt(N)

    if iterations is None:
        M = len(marked_states)
        iterations = max(
            1,
            int(np.floor(np.pi / 4 * np.sqrt(N / M)))
        )

    for _ in range(iterations):

        # ----------------------------------------------------
        # Oracle:
        # Flip the phase of every marked state
        # ----------------------------------------------------
        for i in marked_states:
            state[i] *= -1

        # ----------------------------------------------------
        # Diffusion operator
        #
        # state -> 2|s><s|state - state
        # ----------------------------------------------------
        mean = np.mean(state)

        state = 2 * mean - state

    probabilities = np.abs(state) ** 2

    return state, probabilities


def print_results(probabilities, marked_states):

    print("\nMeasurement probabilities:")

    for i, p in enumerate(probabilities):

        label = "GOOD" if i in marked_states else "BAD"

        print(
            f"|{i:>3}> : "
            f"{p:.6f}   {label}"
        )

    best = int(np.argmax(probabilities))

    print("\nMost probable state:", best)

    if best in marked_states:
        print("SUCCESS: marked state found!")
    else:
        print("The maximum probability is not a marked state.")


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("        AMPLITUDE AMPLIFICATION")
        print("=" * 55)

        print("1. Single marked state")
        print("2. Multiple marked states")
        print("3. Custom number of iterations")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            N = int(input("Number of states N: "))

            marked = int(
                input(f"Marked state (0-{N-1}): ")
            )

            state, probabilities = amplitude_amplification(
                N,
                [marked]
            )

            print_results(probabilities, [marked])

        elif choice == "2":

            N = int(input("Number of states N: "))

            raw = input(
                "Enter marked states separated by spaces: "
            )

            marked = list(map(int, raw.split()))

            state, probabilities = amplitude_amplification(
                N,
                marked
            )

            print_results(probabilities, marked)

        elif choice == "3":

            N = int(input("Number of states N: "))

            raw = input(
                "Enter marked states separated by spaces: "
            )

            marked = list(map(int, raw.split()))

            iterations = int(
                input("Number of amplification iterations: ")
            )

            state, probabilities = amplitude_amplification(
                N,
                marked,
                iterations
            )

            print_results(probabilities, marked)

        elif choice == "4":

            print("Exiting...")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
