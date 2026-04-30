import numpy as np

def solve():
    with open("simon_data.txt", "r") as f:
        lines = f.readlines()
    n = int(lines[0].strip())
    equations = np.array([[int(b) for b in l.strip()] for l in lines[1:]])

    print(f"Solving for n={n}...")
    for i in range(1, 1 << n):
        candidate = np.array([int(b) for b in format(i, f'0{n}b')])
        if not np.any(np.dot(equations, candidate) % 2):
            print(f"FOUND SECRET STRING: {format(i, f'0{n}b')}")
            return
    print("Secret string is 000 (or insufficient equations).")

solve()