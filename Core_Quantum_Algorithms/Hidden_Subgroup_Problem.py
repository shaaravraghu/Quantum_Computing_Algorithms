import itertools


# ============================================================
# HIDDEN SUBGROUP PROBLEM
# ============================================================

def generate_group(n):
    """
    Generate the additive group Z_n.
    """
    return list(range(n))


def coset(group, subgroup, g):
    """
    Return g + H modulo n.
    """

    n = len(group)

    return sorted(
        {(g + h) % n for h in subgroup}
    )


def oracle(group, subgroup, x):
    """
    Oracle value.

    Two elements have the same oracle output
    if they belong to the same coset of H.
    """

    n = len(group)

    return min(
        (x + h) % n
        for h in subgroup
    )


def find_hidden_subgroup(group, oracle_function):
    """
    Brute-force classical reconstruction.

    This is NOT the quantum speedup.
    It demonstrates the mathematical HSP structure.
    """

    n = len(group)

    outputs = {}

    for x in group:

        value = oracle_function(x)

        outputs.setdefault(
            value,
            []
        ).append(x)

    # Pick the coset containing 0
    zero_coset = outputs[
        oracle_function(0)
    ]

    # Elements in H are exactly the elements
    # that occur in the coset containing 0.
    return sorted(zero_coset)


def print_cosets(group, subgroup):

    print("\nCosets of the hidden subgroup:")

    seen = set()

    for g in group:

        current = tuple(
            coset(group, subgroup, g)
        )

        if current not in seen:

            print(
                f"{g} + H = {list(current)}"
            )

            seen.add(current)


# ============================================================
# MENU
# ============================================================

def main():

    while True:

        print("\n" + "=" * 55)
        print("        HIDDEN SUBGROUP PROBLEM")
        print("=" * 55)

        print("1. Z_n with custom subgroup")
        print("2. Predefined examples")
        print("3. Show cosets")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            n = int(
                input("Enter n for Z_n: ")
            )

            raw = input(
                "Enter subgroup elements separated by spaces: "
            )

            subgroup = list(
                map(int, raw.split())
            )

            group = generate_group(n)

            discovered = find_hidden_subgroup(
                group,
                lambda x: oracle(
                    group,
                    subgroup,
                    x
                )
            )

            print(
                "\nActual hidden subgroup:",
                subgroup
            )

            print(
                "Discovered subgroup:    ",
                discovered
            )

        elif choice == "2":

            examples = [
                (8, [0, 4]),
                (12, [0, 4, 8]),
                (16, [0, 4, 8, 12]),
                (15, [0, 5, 10])
            ]

            for n, subgroup in examples:

                group = generate_group(n)

                discovered = find_hidden_subgroup(
                    group,
                    lambda x,
                    g=group,
                    h=subgroup:
                        oracle(g, h, x)
                )

                print(
                    f"\nZ_{n}"
                )

                print(
                    "Actual:    ",
                    subgroup
                )

                print(
                    "Discovered:",
                    discovered
                )

        elif choice == "3":

            n = int(
                input("Enter n for Z_n: ")
            )

            raw = input(
                "Enter subgroup elements: "
            )

            subgroup = list(
                map(int, raw.split())
            )

            group = generate_group(n)

            print_cosets(
                group,
                subgroup
            )

        elif choice == "4":

            print("Exiting...")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()
