"""
043 — Concepts as keys, hierarchies as digits: bag and tree nearness together.

PROMOTED 2026-10-03 → proofs/005 (claims). Kept here as the original
exploration record.

Proof 004's P5 called non-prefix similarity a boundary: four attributes
packed into ONE value as levels of a path, and q-adic depth matched the
shared-attribute count for only 121/256 of pairs. That was an encoding
choice. Here each attribute gets its own key (the bag, as in banana-lab's
proof 128: shared keys = shared concepts), and each attribute's value is a
q-adic path in that attribute's own hierarchy (the tree). One
agreement_with call then returns every attribute's depth of agreement.

Predictions, on record BEFORE the first run:
  P1  Bag similarity exactly. The 256 leaves of 004's P5 (4 attributes, 4
      values each), one attribute per key at precision 1: the number of keys
      agreeing at full depth equals the shared-attribute count for all
      65,536 ordered pairs (004 encoding: 121/256).
  P2  Bag and tree together. m attributes (m = 4, 16, 64), each a hierarchy
      of 3 levels, branching 3 (27 leaves), one key per attribute at
      precision 3; pairs with a prescribed depth per attribute, uniform in
      {0,…,3}. Exact: every attribute's depth right, every pair. MAP-I
      (h = Σ prefix vectors per attribute, R = Σ role ⊙ h; per role, clean-up
      against that attribute's 27 leaves in both records, then the depth):
      ≥ 99% at n = 10,000 for every m (004's common-mode argument,
      σ_diff ≈ √(2nk(m−1)) ≤ 2,000 against a margin of n); < 50% at the exact
      record's bits.
  P3  Size: the exact record is under 1/10 of MAP-I's bits at n = 10,000, at
      every m.
  P4  Huffman-like keys (proof 128's frequency order). Sparse records over
      1,000 attributes; attribute i present with probability 1/(i + 1)
      (Zipf), value a 3-level path with choices 1…3 (0 = absent, so an
      absent attribute leaves the denominator). Fraction-mode size
      (numerator + reduced denominator), summed over 2,000 records:
      frequency order (frequent attribute → small prime) ≤ 75% of a random
      order, and the reversed order is the largest of the three.

Exact integers and Fractions; numpy only as an int64 engine for MAP-I.

Results (2026-10-03, ~2 min):
  P1 HELD: 65,536/65,536 pairs exact with one attribute per key (004's
     single-value encoding: 30,976 = 121/256).
  P2 HELD:      m   exact        bits   MAP n=10⁴   MAP bits   same bits
                4   80/80          37        100%     50,000         45%
               16   320/320       223        100%     60,000         38%
               64   1280/1280   1,291        100%     80,000         38%
  P3 HELD: the exact record is 1/1,350 to 1/62 of MAP-I's bits.
  P4 HELD: fraction-mode bits over 2,000 sparse Zipf records: frequency
     order 608,896, random 992,776, reversed 1,109,384; frequency/random =
     61% (predicted ≤ 75%), reversed largest. Proof 128's frequency order
     is Huffman-like in the plainest sense: frequent concepts get the
     cheapest keys.
Reading: 004's P5 boundary was the encoding, not the memory. With concepts
as keys (the bag) and each concept's value a q-adic path (the tree), one
subtraction gives every concept's depth of agreement, exact, including the
shared-concept count a VSA bag gives. What remains per KEY is that
nearness inside one value is prefix-shaped. MAP-I matches the depths at
n = 10,000 (with a clean-up per role) at 62–1,350× the bits.
"""

import random
from fractions import Fraction
from itertools import product

import numpy as np

from rhind import AdicMemory, Schema, encode_path, odd_primes

SEED = 43
N_BIG = 10000


def shared_prefix(a, b, k):
    j = 0
    while j < k and a[j] == b[j]:
        j += 1
    return j


def p1():
    leaves = list(product(range(4), repeat=4))
    keys = odd_primes(4, start_after=4)
    schema = Schema({q: 1 for q in keys})
    mem = {a: AdicMemory.build(dict(zip(keys, a)), schema) for a in leaves}
    hit = 0
    for a in leaves:
        for b in leaves:
            ag = mem[a].agreement_with(mem[b])
            hit += sum(ag[q] == 1 for q in keys) == sum(x == y for x, y in zip(a, b))
    return hit, len(leaves) ** 2


class Map:
    def __init__(self, m, n, rng):
        self.n, self.rng, self.vec = n, rng, {}
        self.roles = rng.choice(np.array([-1, 1], dtype=np.int64), size=(m, n))

    def v(self, key):
        if key not in self.vec:
            self.vec[key] = self.rng.choice(
                np.array([-1, 1], dtype=np.int64), size=self.n
            )
        return self.vec[key]

    def h(self, attr, path):
        return sum(self.v((attr, tuple(path[: i + 1]))) for i in range(len(path)))

    def record(self, paths):
        return sum(self.roles[r] * self.h(r, p) for r, p in enumerate(paths))


def p2_p3(m, rng, trials=20):
    K, B = 3, 3
    leaves = list(product(range(B), repeat=K))
    keys = odd_primes(m, start_after=4)
    schema = Schema({q: K for q in keys})
    ok = tot = 0
    recs = []
    for _ in range(trials):
        a = [rng.choice(leaves) for _ in keys]
        b = []
        for p in a:
            j = rng.randrange(K + 1)
            if j == K:
                b.append(p)
            else:
                b.append(
                    tuple(
                        list(p[:j])
                        + [rng.choice([c for c in range(B) if c != p[j]])]
                        + [rng.randrange(B) for _ in range(K - j - 1)]
                    )
                )
        A = AdicMemory.build({q: encode_path(p, q) for q, p in zip(keys, a)}, schema)
        Bm = AdicMemory.build({q: encode_path(p, q) for q, p in zip(keys, b)}, schema)
        ag = A.agreement_with(Bm)
        ok += sum(ag[q] == shared_prefix(x, y, K) for q, x, y in zip(keys, a, b))
        tot += m
        recs.append((a, b, A.bits()))
    ex_bits = max(r[2] for r in recs)

    def map_acc(n_of):
        nr = np.random.default_rng(SEED + m)
        hits = width = 0
        for a, b, bits in recs:
            n = n_of(bits)
            M = Map(m, n, nr)
            RA, RB = M.record(a), M.record(b)
            width = max(width, (2 * int(np.abs(RA).max()) + 1).bit_length())
            for r in range(m):
                H = np.stack([M.h(r, leaf) for leaf in leaves])
                la = leaves[int((H @ (M.roles[r] * RA)).argmax())]
                lb = leaves[int((H @ (M.roles[r] * RB)).argmax())]
                hits += shared_prefix(la, lb, K) == shared_prefix(a[r], b[r], K)
        return hits, width

    big, width = map_acc(lambda b: N_BIG)
    same, _ = map_acc(lambda b: max(8, b // width))
    return ok, tot, ex_bits, big, same, N_BIG * width


def p4(rng, records=2000, attrs=1000):
    K = 3
    primes = odd_primes(attrs, start_after=4)  # all > 3 = max choice
    present = [
        [i for i in range(attrs) if rng.randrange(i + 1) == 0] for _ in range(records)
    ]
    paths = [
        {i: tuple(rng.randrange(1, 4) for _ in range(K)) for i in rec}
        for rec in present
    ]
    orders = {"frequency": list(range(attrs)), "reversed": list(reversed(range(attrs)))}
    shuffled = list(range(attrs))
    rng.shuffle(shuffled)
    orders["random"] = shuffled
    out = {}
    for name, order in orders.items():
        key_of = {i: primes[order[i]] for i in range(attrs)}
        total = 0
        for rec in paths:
            # fraction mode: only present attributes enter the reduced F
            F = sum(
                (
                    Fraction(encode_path(p, key_of[i]), key_of[i] ** K)
                    for i, p in rec.items()
                ),
                Fraction(0),
            )
            F -= F.numerator // F.denominator
            total += F.numerator.bit_length() + F.denominator.bit_length()
        out[name] = total
    return out


def main():
    rng = random.Random(SEED)
    hit, tot = p1()
    print(
        f"P1: one attribute per key: shared-attribute count exact for {hit}/{tot} pairs (004 encoding: 30,976)"
    )
    for m in (4, 16, 64):
        ok, tot, ex_bits, big, same, map_bits = p2_p3(m, rng)
        print(
            f"P2/P3 m={m:>2}: exact {ok}/{tot}, {ex_bits} bits | MAP n=10,000 {100 * big // tot}% ({map_bits} bits) | same bits {100 * same // tot}%"
        )
    sizes = p4(rng)
    print(
        f"P4: fraction-mode bits over 2,000 sparse records: "
        + ", ".join(f"{k} {v:,}" for k, v in sizes.items())
        + f"  (frequency / random = {100 * sizes['frequency'] // sizes['random']}%)"
    )


if __name__ == "__main__":
    main()
