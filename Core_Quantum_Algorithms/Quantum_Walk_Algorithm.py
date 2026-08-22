import numpy as np


# ============================================================
# QUANTUM WALK ON A CYCLE
# ============================================================

def hadamard():

    return np.array([
        [1, 1],
        [1, -1]
    ], dtype=complex) / np.sqrt(2)


def quantum_walk(num_positions, steps):

    """
    Discrete-time quantum walk on a cycle.

    Each position has two coin states:

        |0> -> move left
        |1> -> move right
    """

    H = hadamard()

    # State[position, coin]
    state = np.zeros(
        (num_positions, 2),
        dtype=complex
    )

    # Start at position 0
    # with equal coin superposition
    state[0, 0] = 1 / np.sqrt(2)
    state[0, 1] = 1 / np.sqrt(2)

    for _ in range(steps):

        # ----------------------------------------------------
        # Coin operation
        # ----------------------------------------------------

        new_state = np.zeros_like(state)

        for position in range(num_positions):

            new_state[position] = (
                H @ state[position]
            )

        # ----------------------------------------------------
        # Conditional shift
        # ----------------------------------------------------

        shifted = np.zeros_like(state)

        for position in range(num_positions):

            # Coin 0 -> move left
            left = (
                position - 1
            ) % num_positions

            shifted[left, 0] += (
                new_state[position, 0]
            )

            # Coin 1 -> move right
            right = (
                position + 1
            ) % num_positions

            shifted[right, 1] += (
                new_state[position, 1]
            )

        state = shifted

    # Position probabilities
    probabilities = np.sum(
        np.abs(state) ** 2,
        axis=1
    )

    return state, probabilities


def print_distribution(probabilities):

    print("\nPosition probabilities:")

    for position, probability in enumerate(
        probabilities
    ):

        print(
            f"Position {position:>3}: "
            f"{probability:.6f}"
        )


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("             QUANTUM WALK")
        print("=" * 55)

        print("1. Run quantum walk")
        print("2. Compare different step counts")
        print("3. Compare different cycle sizes")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            positions = int(
                input("Number of positions: ")
            )

            steps = int(
                input("Number of steps: ")
            )

            state, probabilities = (
                quantum_walk(
                    positions,
                    steps
                )
            )

            print_distribution(
                probabilities
            )

        elif choice == "2":

            positions = int(
                input("Number of positions: ")
            )

            for steps in [1, 2, 4, 8, 16]:

                _, probabilities = (
                    quantum_walk(
                        positions,
                        steps
                    )
                )

                print(
                    f"\nSteps = {steps}"
                )

                print_distribution(
                    probabilities
                )

        elif choice == "3":

            steps = int(
                input("Number of steps: ")
            )

            for positions in [8, 16, 32]:

                _, probabilities = (
                    quantum_walk(
                        positions,
                        steps
                    )
                )

                print(
                    f"\nCycle size = {positions}"
                )

                print_distribution(
                    probabilities
                )

        elif choice == "4":

            print("Exiting...")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
