"""Recompute Tab. 'Deng-Raviv' from the paper's stated rule; check whether the N <= 2^14 cap
binds; and measure how much of the exact memory's bits MAP actually gets in 001 (n is set
from the worst-case counter width (2K+1).bit_length(), not the realised width). Integers only.
"""

import random
from math import comb
import numpy as np

U, V = 20000, 1000


def blocks(N, size):
    k, c = 1, N
    while c < size:
        k, c = k + 1, c * N
    return k


def pp(limit):
    s = bytearray([1]) * (limit + 1)
    s[0:2] = b"\0\0"
    for i in range(2, limit + 1):
        if s[i]:
            s[i * i :: i] = bytearray(len(s[i * i :: i]))
            N, m = i, 1
            while N <= limit:
                yield i, m, N
                N, m = N * i, m + 1


def dr(u, cap):
    best = None
    for p, m, N in pp(cap):
        k = blocks(N, U) + blocks(N, V)
        if (N - 1) // (k - 1) < u:
            continue
        b = N * N * (comb(u + p - 1, p - 1) - 1).bit_length()
        if best is None or b < best[0]:
            best = (b, f"{p}^{m}", k)
    return best


for K in (10, 30, 100, 300, 1000, 3000):
    print(K, "cap 2^14:", dr(K, 1 << 14), "| cap 2^16:", dr(K, 1 << 16))
# MAP width actually used vs affordable, 001 setting
rng = np.random.default_rng(0)
ex_bits = {10: 327, 100: 3212, 1000: 32396, 3000: 97587}
for K, b in ex_bits.items():
    wc = (2 * K + 1).bit_length()
    n = max(8, b // wc)
    mem = (
        rng.choice(np.array([-1, 1]), size=(K, n))
        * rng.choice(np.array([-1, 1]), size=(K, n))
    ).sum(axis=0)
    real = (2 * int(np.abs(mem).max()) + 1).bit_length()
    print(
        f"K={K}: n used {n} (width {wc}); realised width {real}; bits actually spent {n*real} of {b} ({100*n*real//b}%)"
    )
