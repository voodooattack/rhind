"""Referee checks on two structural claims (exact integers only).

(a) 'Why primes' (main.typ l.268-280): pairwise-coprime composite keys are said not to be
    closed. Test: keys 15, 22, 91, 323 (pairwise coprime, all composite), values 0..m-1
    (any residue, units or not). Memory = sum v/m mod 1. Recall by the m-primary part,
    presence by gcd(m, D) > 1, value query by gcd(m, den(F - xS)) == 1, agreeing likewise.
(b) Re-binding (l.418-425): 'exactness of this kind and holistic transport cannot be had
    together'. Test: a packed record as an element of (Z/2^w)^m; moving field i to field j is
    a group endomorphism (additive) and exact.
"""

import random
from fractions import Fraction
from math import gcd, prod


def frac(F):
    return F - (F.numerator // F.denominator)


def component(F, m):
    """value at modulus m: the m-part of F, read through g = gcd(m, den F)."""
    N, D = F.numerator, F.denominator
    g = gcd(m, D)
    if g == 1:
        return 0
    c = N * pow(D // g, -1, g) % g  # F's g-part = c/g
    return c * (m // g) % m  # = (c*(m/g))/m


keys = [15, 22, 91, 323]
assert all(gcd(a, b) == 1 for i, a in enumerate(keys) for b in keys[i + 1 :])
rng = random.Random(7)
bad = 0
for t in range(20000):
    va = {m: rng.randrange(m) for m in keys}
    vb = {m: rng.choice([va[m], rng.randrange(m)]) for m in keys}
    Fa = frac(sum((Fraction(v, m) for m, v in va.items()), Fraction(0)))
    Fb = frac(sum((Fraction(v, m) for m, v in vb.items()), Fraction(0)))
    # recall + presence
    bad += any(component(Fa, m) != va[m] for m in keys)
    bad += any((gcd(m, Fa.denominator) > 1) != (va[m] != 0) for m in keys)
    # closure: sum is the memory of per-key sums mod m
    Fs = frac(Fa + Fb)
    bad += any(component(Fs, m) != (va[m] + vb[m]) % m for m in keys)
    # value query with bag S = sum 1/m (x < min key)
    x = rng.randrange(1, 15)
    S = sum((Fraction(1, m) for m in keys), Fraction(0))
    den = frac(Fa - x * S).denominator
    bad += {m for m in keys if gcd(m, den) == 1} != {m for m in keys if va[m] == x}
    # agreeing
    den = frac(Fa - Fb).denominator
    bad += {m for m in keys if gcd(m, den) == 1} != {m for m in keys if va[m] == vb[m]}
print("(a) pairwise-coprime composite keys, 20,000 trials, mismatches:", bad)
print(
    "    the paper's example 4/15 + 1/15 = 1/3: component at 15 =",
    component(frac(Fraction(4, 15) + Fraction(1, 15)), 15),
    "(= 4+1, correct)",
)

# (b) packed record in (Z/2^w)^m, field move i -> j is additive and exact
w, m = 10, 8
M = (1 << w) - 1


def add(R1, R2):  # group law of (Z/2^w)^m on packed integers
    return sum(
        ((((R1 >> (w * k)) & M) + ((R2 >> (w * k)) & M)) & M) << (w * k)
        for k in range(m)
    )


def move(R, i, j):  # endomorphism: project field i, inject at j, keep others, clear i
    vi = (R >> (w * i)) & M
    keep = R & ~((M << (w * i)) | (M << (w * j)))
    return keep | (vi << (w * j))


bad = 0
for t in range(20000):
    a = [rng.randrange(1 << w) for _ in range(m)]
    b = [rng.randrange(1 << w) for _ in range(m)]
    a[3] = b[3] = 0  # target field empty, as in the paper's rebind
    A = sum(v << (w * k) for k, v in enumerate(a))
    B = sum(v << (w * k) for k, v in enumerate(b))
    bad += move(add(A, B), 1, 3) != add(move(A, 1, 3), move(B, 1, 3))
    bad += ((move(A, 1, 3) >> (w * 3)) & M) != a[1]
print(
    "(b) packed (Z/2^10)^8: field move is additive and exact; mismatches in 20,000 trials:",
    bad,
)
