"""
shor_classical_post.py
----------------------
Shor's Algorithm — Classical Post-Processing (File 3 of 3)

Reads shor_output.csv (written by shor_quantum.py) and:
  1. Takes the top measured phase values
  2. Converts each phase to a rational s/r via continued fractions
  3. Validates each candidate period r  (a^r mod N == 1, r even, non-trivial)
  4. Computes GCD(a^(r/2) ± 1, N) to extract factors
  5. Reports the non-trivial factor pair p, q such that N = p × q

No Qiskit dependency — this file is purely classical.

Usage:
    python shor_input_gen.py       # first  — writes shor_input.csv
    python shor_quantum.py         # second — writes shor_output.csv
    python shor_classical_post.py  # third  — extracts and prints factors
"""

import csv
import math
import os
import sys
from fractions import Fraction


# ══════════════════════════════════════════════════════════════════════════════
#  CSV readers
# ══════════════════════════════════════════════════════════════════════════════

def read_quantum_output(csv_path: str) -> list[tuple[int, float, int, int]]:
    """
    Parse shor_output.csv.
    Returns list of (phase_int, phase_frac, counts, n_count) sorted by counts desc.
    """
    if not os.path.exists(csv_path):
        sys.exit(
            f"  ✗  '{csv_path}' not found.\n"
            "     Run  shor_quantum.py  first."
        )
    rows = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append((
                int(row["phase_int"]),
                float(row["phase_frac"]),
                int(row["counts"]),
                int(row["n_count"]),
            ))
    if not rows:
        sys.exit("  ✗  shor_output.csv is empty. Re-run shor_quantum.py.")
    return rows


def read_input_config(csv_path: str) -> tuple[int, int]:
    """Parse shor_input.csv → (N, a)."""
    if not os.path.exists(csv_path):
        sys.exit(
            f"  ✗  '{csv_path}' not found.\n"
            "     Run  shor_input_gen.py  first."
        )
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("  ✗  shor_input.csv is empty.")
    return int(rows[0]["N"]), int(rows[0]["a"])


# ══════════════════════════════════════════════════════════════════════════════
#  Continued fractions — phase → period candidate
# ══════════════════════════════════════════════════════════════════════════════

def phase_to_period_candidates(phase_frac: float, n_count: int, N: int) -> list[int]:
    """
    Convert a measured phase fraction to period candidates using continued fractions.

    The QFT produces a phase ≈ s/r for some integer s.
    Continued fraction expansion of phase_frac finds rational approximations s/r
    with denominator r ≤ N.  Each denominator is a candidate for the period.

    Returns a list of unique candidate r values.
    """
    if phase_frac == 0.0:
        return []                       # phase 0 carries no period information

    candidates = []
    # Use Python's Fraction with a limited denominator to get convergents
    frac = Fraction(phase_frac).limit_denominator(N)

    # Collect the denominator and its small multiples (in case r = k·denom)
    r = frac.denominator
    for multiplier in range(1, 5):
        candidate = r * multiplier
        if candidate <= N and candidate not in candidates:
            candidates.append(candidate)

    return candidates


# ══════════════════════════════════════════════════════════════════════════════
#  Period validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_period(r: int, a: int, N: int) -> tuple[bool, str]:
    """
    Check that r is a valid period for a^x mod N:
      1. r > 0
      2. a^r mod N == 1              (r is actually a period)
      3. r is even                   (needed for factor extraction)
      4. a^(r/2) mod N ≠ N-1        (not the trivial ±1 case)
    Returns (valid: bool, reason: str).
    """
    if r <= 0:
        return False, "r ≤ 0"
    if pow(a, r, N) != 1:
        return False, f"a^r mod N = {pow(a, r, N)} ≠ 1"
    if r % 2 != 0:
        return False, "r is odd"
    half = pow(a, r // 2, N)
    if half == N - 1:
        return False, f"a^(r/2) mod N = {half} = N-1 (trivial)"
    return True, "ok"


# ══════════════════════════════════════════════════════════════════════════════
#  Factor extraction
# ══════════════════════════════════════════════════════════════════════════════

def extract_factors(r: int, a: int, N: int) -> tuple[int, int] | None:
    """
    Given a valid period r, compute:
        m1 = GCD(a^(r/2) - 1, N)
        m2 = GCD(a^(r/2) + 1, N)
    Return (m1, m2) if both are non-trivial (1 < m1,m2 < N), else None.
    """
    half  = pow(a, r // 2, N)
    m1    = math.gcd(half - 1, N)
    m2    = math.gcd(half + 1, N)

    if 1 < m1 < N:
        return m1, N // m1
    if 1 < m2 < N:
        return m2, N // m2
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    input_csv  = os.path.join(base_dir, "shor_input.csv")
    output_csv = os.path.join(base_dir, "shor_output.csv")

    N, a         = read_input_config(input_csv)
    phase_rows   = read_quantum_output(output_csv)
    n_count      = phase_rows[0][3]
    total_shots  = sum(r[2] for r in phase_rows)

    print("=" * 60)
    print("  Shor's Algorithm — Classical Post-Processing")
    print("=" * 60)
    print(f"  N               : {N}")
    print(f"  k               : {a}")
    print(f"  Function        : f(x) = {a}ˣ mod {N}")
    print(f"  n_count         : {n_count} qubits  →  {2**n_count} phase slots")
    print(f"  Phase samples   : {len(phase_rows)} distinct values ({total_shots} total shots)")
    print("=" * 60)

    # ── Process top phase measurements ────────────────────────────────────────
    print("\n── Continued Fraction Analysis ─────────────────────────────")
    print(f"  {'Phase frac':<14}  {'Candidate r':<14}  {'Valid?':<8}  Reason")
    print("  " + "─" * 54)

    found_factors = None
    seen_r        = set()

    # Try top-probability phases first
    for phase_int, phase_frac, counts, _ in phase_rows:

        if phase_int == 0:
            print(f"  {phase_frac:<14.6f}  {'—':<14}  {'skip':<8}  Phase = 0, no info")
            continue

        candidates = phase_to_period_candidates(phase_frac, n_count, N)

        for r in candidates:
            if r in seen_r:
                continue
            seen_r.add(r)

            valid, reason = validate_period(r, a, N)
            prob_str      = f"{counts/total_shots*100:.1f}%"
            print(f"  {phase_frac:<14.6f}  r = {r:<10}  {'✓' if valid else '✗':<8}  {reason}  [{prob_str}]")

            if valid and found_factors is None:
                factors = extract_factors(r, a, N)
                if factors:
                    found_factors = (r, factors[0], factors[1])

        if found_factors:
            break                       # stop once we have a valid factorisation

    # ── Final report ──────────────────────────────────────────────────────────
    print("\n── Result ──────────────────────────────────────────────────")

    if found_factors:
        r, m1, m2 = found_factors
        raw_half   = a ** (r // 2)          # true integer a^(r/2), no mod
        print(f"  Period found    : r = {r}")
        print(f"  a^(r/2)        : {a}^{r//2} = {raw_half}")
        print(f"  a^(r/2) mod N  : {pow(a, r//2, N)}")
        print(f"  a^(r/2) - 1    : {raw_half - 1}")
        print(f"  a^(r/2) + 1    : {raw_half + 1}")
        print(f"  GCD candidates : GCD({raw_half - 1}, {N}) and GCD({raw_half + 1}, {N})")
        print()
        print(f"  m1 = {raw_half - 1}, m2 = {raw_half + 1}")
        print()
        print(f"  ✓  FACTORS FOUND")
        # print(f"     {N}  =  {m1}  ×  {m2}")
        print("N1 =",m1,"N2 =",m2)
        print()
        # Verify
        if m1 * m2 == N:
            print(f"  Verification   : {m1} × {m2} = {m1*m2} = N  ✓")
        else:
            print(f"  Verification   : {m1} × {m2} = {m1*m2} ≠ {N}  ✗  (unexpected)")
    else:
        print("  ✗  No valid period found in this run.")
        print("     This can happen due to quantum randomness — the QFT sometimes")
        print("     measures an uninformative phase. Re-run shor_quantum.py and")
        print("     shor_classical_post.py to try again.")

    print()


if __name__ == "__main__":
    main()
