"""Referee checks: library edge cases. Exact integers/Fractions only."""

import random
from fractions import Fraction
from math import prod, gcd, comb
from rhind import ExactMemory, is_prime, odd_primes, AdicMemory, Schema

# 1. Miller-Rabin bound: psi_12 (Sorenson-Webster 2015), strong pseudoprime to first 12 prime bases
psi12 = 318665857834031151167461
f1, f2 = 399165290221, 798330580441
print(
    "psi12 == f1*f2:",
    f1 * f2 == psi12,
    "| is_prime(psi12):",
    is_prime(psi12),
    "| psi12 < 3.3e24:",
    psi12 < 33 * 10**23,
)
try:
    m = ExactMemory.build({psi12: 5})
    print(
        "build accepted composite key psi12; get(f1) ->",
        m.get(f1) if is_prime(f1) else "n/a",
        "| f1 in m:",
        f1 in m,
    )
except ValueError as e:
    print("build refused:", e)

# 2. project() with a non-prime / overlapping key list
m = ExactMemory.build({11: 3, 13: 5, 17: 7})
p = m.project([11, 143])
print(
    "project([11,143]) on {11:3,13:5,17:7}: D =", p.D, "= 11^2*13?", p.D == 11 * 11 * 13
)
try:
    p.get(11)
except ValueError as e:
    print("  get(11) on the projection raises:", e)
print(
    "  correct sub-memory on {11,13}:",
    ExactMemory.build({11: 3, 13: 5}).F,
    " got:",
    p.F,
)

# 3. Prop 2 / analogy / agreeing randomized, with empty roles, keys outside R, x at several roles
rng = random.Random(1)
bad = 0
for t in range(3000):
    R = odd_primes(rng.randint(1, 12), start_after=rng.randint(10, 200))
    extra = odd_primes(
        rng.randint(0, 4), start_after=R[-1] + rng.randint(0, 50)
    )  # keys outside R
    xmax = min(R) - 1
    vals = {
        q: rng.choice([0, 0, rng.randrange(1, min(R)), rng.randrange(1, q)]) for q in R
    }
    for q in extra:
        vals[q] = rng.randrange(1, q)
    F = ExactMemory.build({q: v for q, v in vals.items() if v})
    bag = ExactMemory.key_bag(R)
    x = rng.randrange(1, xmax + 1)
    want = prod(q for q in R if vals[q] == x)
    if F.holding(x, bag) != want:
        bad += 1
    G = ExactMemory.build(
        {
            q: (v if rng.random() < 0.5 else rng.randrange(1, q))
            for q, v in vals.items()
            if v
        }
    )
    gv = {q: (G.get(q) or 0) for q in set(vals)}
    wantag = prod(q for q in vals if vals[q] and gv[q] == vals[q])
    if F.agreeing(G) != wantag:
        bad += 1
print("Prop 2 / agreeing random trials mismatches:", bad)

# x not below every key of the bag: library refuses
try:
    ExactMemory.build({11: 3}).holding(11, ExactMemory.key_bag([11, 13]))
except ValueError as e:
    print("x >= min R refused:", e)
# x at two roles -> analogy None
A = ExactMemory.build({101: 7, 103: 9})
B = ExactMemory.build({101: 5, 103: 5})
print(
    "analogy with x at two roles of B:",
    A.analogy(B, 5, ExactMemory.key_bag([101, 103])),
)
# empty memory
E = ExactMemory()
print(
    "empty: D",
    E.D,
    "get(101)",
    E.get(101),
    "holding",
    E.holding(1, ExactMemory.key_bag([101])),
    "agreeing(E)",
    E.agreeing(E),
)

# 4. Adic: value 0 vs absent, value divisible by q
s = Schema({5: 3, 7: 2})
a = AdicMemory.build({5: 0, 7: 0}, s)
b = AdicMemory.build({}, s)
print(
    "adic: value 0 at both keys == empty memory:",
    a == b,
    "(absence not readable; paper's graded section does not say so)",
)
c = AdicMemory.build({5: 25}, s)
print(
    "adic: value 25 at key 5^3 -> den(F) =",
    c.F.denominator,
    "(prime 5 at exponent 1, not 3)",
)

# 5. enumerative code vs D / gamma / bitmap (paper l.584-586)
U = 20000
d = {
    10: 171,
    100: 1370,
    300: 3162,
    1000: 7510,
    3000: 14178,
    10000: 20000,
}  # best of the three per JSON
print(
    "enumerative ceil(log2 C(U,K)) vs best of three:",
    {K: ((comb(U, K) - 1).bit_length(), d[K]) for K in d},
)
