"""An 'ordinary data structure' baseline: a packed record (m fields of b data bits + 1 guard bit)
held in ONE Python int. The paper's holistic queries become a constant number of whole-word
operations (XOR, add, AND), linear in size, with no gcd. Checked against rhind on random records.
Exact integers only."""

import random, time
from math import prod
from rhind import ExactMemory, AdicMemory, Schema, encode_path, odd_primes

rng = random.Random(3)


def masks(m, w):
    H = sum(1 << (i * w + w - 1) for i in range(m))  # guard bits
    L = sum(((1 << (w - 1)) - 1) << (i * w) for i in range(m))  # data bits
    return H, L


def pack(vals, w):
    return sum(v << (i * w) for i, v in enumerate(vals))


def zero_fields(Z, H, L):
    """Guard-bit mask of the fields of Z that are zero (Z has clear guard bits)."""
    return H & ~((Z + L) & H)


def fields(mask, m, w):
    return [i for i in range(m) if mask >> (i * w + w - 1) & 1]


V = 1000
b = (V - 1).bit_length()
w = b + 1
for m in (10, 100, 1000):
    keys = odd_primes(m, start_after=V)
    H, L = masks(m, w)
    bagE = ExactMemory.key_bag(keys)
    ok = True
    for _ in range(50):
        a = [rng.randrange(V) for _ in range(m)]
        c = [x if rng.randrange(2) else rng.randrange(V) for x in a]
        Ra, Rc = pack(a, w), pack(c, w)
        x = rng.choice(a) or 1
        # value query: fields holding x
        Xb = pack([x] * m, w)
        swar_hold = fields(zero_fields(Ra ^ Xb, H, L), m, w)
        Ea = ExactMemory.build({q: v for q, v in zip(keys, a) if v})
        Ec = ExactMemory.build({q: v for q, v in zip(keys, c) if v})
        ok &= prod(keys[i] for i in swar_hold) == Ea.holding(x, bagE)
        # agreeing roles (both non-empty and equal, as ExactMemory.agreeing counts them)
        swar_agree = [i for i in fields(zero_fields(Ra ^ Rc, H, L), m, w) if a[i]]
        ok &= prod(keys[i] for i in swar_agree) == Ea.agreeing(Ec)
    print(
        f" m={m:4d}: SWAR == rhind on 50 records: {ok};  packed bits={m*w} (floor {m*b})  vs rhind fraction bits ~{Ea.bits()}, schema-mode N ~{Ea.N.bit_length() if Ea.D==prod(keys) else 'n/a'}"
    )

print(
    "graded depth: base-4 paths of 4 levels, 2 bits/digit, per-field depth >= j via k zero-field tests"
)
K, B = 4, 4
for m in (10, 100):
    keys = odd_primes(m, start_after=B)
    sch = Schema({q: K for q in keys})
    w = 2 * K + 1
    H, Lf = masks(m, w)
    ok = True
    for _ in range(50):
        pa = [[rng.randrange(B) for _ in range(K)] for _ in range(m)]
        pb = [
            p[:j] + [rng.randrange(B) for _ in range(K - j)]
            for p in pa
            for j in [rng.randrange(K + 1)]
        ]
        enc2 = lambda p: sum(
            c << (2 * i) for i, c in enumerate(p)
        )  # root choice in the lowest digit
        Z = pack([enc2(p) for p in pa], w) ^ pack([enc2(p) for p in pb], w)
        depth = [0] * m
        for j in range(1, K + 1):
            Lj = sum(((1 << (2 * j)) - 1) << (i * w) for i in range(m))
            for i in fields(zero_fields(Z & Lj, H, Lf), m, w):
                depth[i] = j
        A = AdicMemory.build({q: encode_path(p, q) for q, p in zip(keys, pa)}, sch)
        Bm = AdicMemory.build({q: encode_path(p, q) for q, p in zip(keys, pb)}, sch)
        ag = A.agreement_with(Bm)
        ok &= depth == [ag[q] for q in keys]
    print(
        f" m={m:4d}: SWAR depths == rhind.adic depths: {ok}; packed bits={m*w} (info {m*2*K}) vs AdicMemory N bits ~{A.bits()}"
    )
