"""
shor_input_gen.py
-----------------
Shor's Algorithm — Input Generator (File 1 of 3)

The professor provides:
  • N  — the number to factor
  • a  — the base (must be coprime to N)

This file runs all classical pre-checks before any quantum work:
  1. N even           → factor 2 trivially
  2. N prime          → already prime, nothing to factor
  3. N a prime power  → handle classically
  4. GCD(a, N) ≠ 1   → GCD is itself a non-trivial factor

If all checks pass, it computes the qubit counts and writes shor_input.csv.

Output CSV format:
  N, a, n_count, n_target
  15, 7, 8, 4
"""

import csv
import math
import os
import sys


# ── classical utilities ────────────────────────────────────────────────────────

def is_prime(n: int) -> bool:
    """Basic primality test."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.isqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def prime_power_base(n: int) -> int | None:
    """
    If n = p^k for some prime p and k >= 2, return p. Otherwise return None.
    """
    for k in range(2, int(math.log2(n)) + 1):
        root = round(n ** (1 / k))
        for candidate in [root - 1, root, root + 1]:
            if candidate >= 2 and candidate ** k == n and is_prime(candidate):
                return candidate
    return None


def classical_period(a: int, N: int) -> int:
    """Brute-force period of a^x mod N (for pre-check / small N verification)."""
    r, val = 1, a % N
    while val != 1:
        val = (val * a) % N
        r  += 1
        if r > N:
            return -1        # should not happen for valid a
    return r


# ── input helpers ──────────────────────────────────────────────────────────────

def get_N() -> int:
    print("\nEnter N — the number you want to factor.")
    print("  • Must be a positive odd composite integer.")
    print("  • Recommended range for simulation: 15 ≤ N ≤ 63")
    print("  • Example: 15, 21, 35\n")
    while True:
        raw = input("N: ").strip()
        if not raw.isdigit():
            print("  ✗  Please enter a positive integer.")
            continue
        n = int(raw)
        if n < 4:
            print("  ✗  N must be at least 4.")
            continue
        return n


def get_a(N: int) -> int:
    print(f"\nEnter k — the base for period finding.")
    print(f"  • Must satisfy 1 < k < {N}")
    print(f"  • GCD(k, N) must equal 1 (coprime)")
    print(f"  • Recommended choices for N={N}: ", end="")
    suggestions = [x for x in range(2, N) if math.gcd(x, N) == 1][:N-2]
    print(", ".join(map(str, suggestions)))
    print()
    while True:
        raw = input("k: ").strip()
        if not raw.isdigit():
            print("  ✗  Please enter a positive integer.")
            continue
        a = int(raw)
        if a <= 1 or a >= N:
            print(f"  ✗  a must satisfy 1 < a < {N}.")
            continue
        return a


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 56)
    print("  Shor's Algorithm — Input Configuration")
    print("=" * 56)

    N = get_N()

    # ── Classical pre-checks ───────────────────────────────────────────────────

    print(f"\n── Classical Pre-checks for N = {N} ──────────────────────")

    # Check 1: even
    if N % 2 == 0:
        print(f"  ⚡ N = {N} is even.")
        print(f"     Trivial factor found: 2 × {N // 2} = {N}")
        print("     No quantum circuit needed.")
        sys.exit(0)

    # Check 2: prime
    if is_prime(N):
        print(f"  ⚡ N = {N} is prime — nothing to factor.")
        sys.exit(0)

    # Check 3: prime power
    base = prime_power_base(N)
    if base is not None:
        k = round(math.log(N) / math.log(base))
        print(f"  ⚡ N = {N} = {base}^{k} — prime power, handled classically.")
        print(f"     Factor: {base}")
        sys.exit(0)

    print(f"  ✓  N = {N} is a valid composite — proceeding to quantum phase.")

    # ── Get a ──────────────────────────────────────────────────────────────────
    a = get_a(N)

    # Check 4: GCD(a, N)
    g = math.gcd(a, N)
    if g != 1:
        print(f"\n  ⚡ GCD({a}, {N}) = {g} — non-trivial factor found classically!")
        print(f"     {N} = {g} × {N // g}")
        print("     No quantum circuit needed.")
        sys.exit(0)

    print(f"  ✓  GCD({a}, {N}) = 1 — valid base, proceeding.")

    # ── Qubit counts ───────────────────────────────────────────────────────────
    # n_target : enough qubits to represent values 0 … N-1
    # n_count  : 2 × n_target for sufficient QFT precision
    n_target = math.ceil(math.log2(N))
    n_count  = 2 * n_target

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n── Summary ───────────────────────────────────────────────")
    print(f"  N               : {N}")
    print(f"  a               : {a}")
    print(f"  n_target qubits : {n_target}  (ceil(log₂{N}))")
    print(f"  n_count  qubits : {n_count}  (2 × n_target, for QFT precision)")
    print(f"  Total qubits    : {n_count + n_target}")
    print(f"  Function        : f(x) = {a}ˣ mod {N}")
    print("─" * 56)

    # ── Write CSV ──────────────────────────────────────────────────────────────
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shor_input.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["N", "a", "n_count", "n_target"])
        writer.writerow([N, a, n_count, n_target])

    print(f"\n  ✓  Saved to : {out_path}")
    print("  Run  shor_quantum.py  to build and simulate the circuit.\n")


if __name__ == "__main__":
    main()
