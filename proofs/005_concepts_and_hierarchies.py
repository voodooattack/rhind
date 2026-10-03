"""
005 — Concepts as keys, hierarchies as digits: bag and tree nearness together

Promoted from exploration 043 (explorations/). Library: rhind.adic.

Proof 004 measured nearness INSIDE one value: q-adic depth is the length
of a shared prefix, so four independent attributes packed into one value
match the shared-attribute count for only 121/256 of pairs. A record is
more than one value. Give each attribute (concept) its own key — the bag,
where shared keys are shared concepts — and let each attribute's value be
a q-adic path in that attribute's own hierarchy — the tree. One
agreement_with call then returns every attribute's depth of agreement.

Predictions, on record BEFORE running (exploration 043 measured them):
  P1  Bag similarity, exactly. The 256 leaves of 004's P5 (4 attributes,
      4 values), one attribute per key: the number of keys agreeing at full
      depth equals the shared-attribute count for all 65,536 ordered pairs
      (one value per leaf, as in 004: exactly 121/256).
  P2  Bag and tree together. m = 4, 16, 64 attributes, each a hierarchy of 3
      levels with branching 3; prescribed depths per attribute, uniform in
      {0,…,3}. Exact: every attribute's depth right in every pair. MAP-I
      (prefix-sum leaf vectors per attribute, R = Σ role ⊙ h; per role,
      clean-up against that attribute's 27 leaves in both records):
      ≥ 99% at n = 10,000 for every m; < 50% at the exact record's bits.
  P3  The exact record is under 1/10 of MAP-I's bits at n = 10,000.
  P4  Frequent concepts on small primes (banana-lab proof 128's order) is
      Huffman-like: sparse records over 1,000 attributes, attribute i present
      with probability 1/(i + 1), values 3-level paths with choices 1…3;
      summed fraction-mode size (numerator + reduced denominator) over 2,000
      records is ≤ 75% of a random assignment's, and the reversed order is
      the largest of the three.

Exact integers and Fractions; numpy only as an int64 engine for MAP-I.
"""

import random
from fractions import Fraction
from itertools import product

import numpy as np

from proofreport import finding, proof_report, row, table, verified_section
from rhind import AdicMemory, Schema, encode_path, odd_primes

SEED = 43
N_BIG = 10000
K, B = 3, 3


def _prefix(a, b, k):
    j = 0
    while j < k and a[j] == b[j]:
        j += 1
    return j


class _Map:
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


def _pct(a, b):
    return f"{100 * a // b}%"


@proof_report(
    title="005 — Concepts as keys, hierarchies as digits: bag and tree nearness together",
    source=__file__,
)
def run():
    rng = random.Random(SEED)

    @verified_section("P1 — bag similarity exactly: one attribute per key")
    @table(
        headers=["pairs", "per_key", "one_value"],
        labels=[
            "ordered pairs",
            "one attribute per key: count exact",
            "all attributes in one value (004)",
        ],
        align=["r", "r", "r"],
    )
    def _bag():
        leaves = list(product(range(4), repeat=4))
        keys = odd_primes(4, start_after=4)
        schema = Schema({q: 1 for q in keys})
        mem = {a: AdicMemory.build(dict(zip(keys, a)), schema) for a in leaves}
        per_key = one_value = 0
        for a in leaves:
            for b in leaves:
                count = sum(x == y for x, y in zip(a, b))
                ag = mem[a].agreement_with(mem[b])
                per_key += sum(ag[q] == 1 for q in keys) == count
                one_value += _prefix(a, b, 4) == count
        total = len(leaves) ** 2
        assert per_key == total  # P1
        assert Fraction(one_value, total) == Fraction(121, 256)  # P1 (004's encoding)
        yield row(
            pairs=total, per_key=f"{per_key}/{total}", one_value=f"{one_value}/{total}"
        )
        yield finding(
            "P1",
            "with one attribute per key the shared-attribute count is exact for "
            "every pair; 004's boundary was the encoding (all attributes in one "
            "value), not the memory",
        )

    @verified_section("P2–P3 — bag and tree together, against MAP-I")
    @table(
        headers=["m", "exact", "ex_bits", "map_acc", "map_bits", "same_acc"],
        labels=[
            "attributes m",
            "exact: every depth",
            "exact bits",
            "MAP (n=10,000)",
            "MAP bits",
            "MAP same bits",
        ],
        align=["r"] * 6,
        legend={
            "map_acc": "per-attribute depth after clean-up against that attribute's 27 leaves in both records"
        },
    )
    def _combined():
        leaves = list(product(range(B), repeat=K))
        for m in (4, 16, 64):
            keys = odd_primes(m, start_after=4)
            schema = Schema({q: K for q in keys})
            ok = tot = 0
            recs = []
            for _ in range(20):
                a = [rng.choice(leaves) for _ in keys]
                b = []
                for p in a:
                    j = rng.randrange(K + 1)
                    if j == K:
                        b.append(p)
                    else:
                        alt = rng.choice([c for c in range(B) if c != p[j]])
                        b.append(
                            tuple(
                                list(p[:j])
                                + [alt]
                                + [rng.randrange(B) for _ in range(K - j - 1)]
                            )
                        )
                A = AdicMemory.build(
                    {q: encode_path(p, q) for q, p in zip(keys, a)}, schema
                )
                Bm = AdicMemory.build(
                    {q: encode_path(p, q) for q, p in zip(keys, b)}, schema
                )
                ag = A.agreement_with(Bm)
                ok += sum(ag[q] == _prefix(x, y, K) for q, x, y in zip(keys, a, b))
                tot += m
                recs.append((a, b, A.bits()))
            ex_bits = max(r[2] for r in recs)

            def map_acc(n_of):
                nr = np.random.default_rng(SEED + m)
                hits = width = 0
                for a, b, bits in recs:
                    n = n_of(bits)
                    M = _Map(m, n, nr)
                    RA, RB = M.record(a), M.record(b)
                    width = max(width, (2 * int(np.abs(RA).max()) + 1).bit_length())
                    for r in range(m):
                        H = np.stack([M.h(r, leaf) for leaf in leaves])
                        la = leaves[int((H @ (M.roles[r] * RA)).argmax())]
                        lb = leaves[int((H @ (M.roles[r] * RB)).argmax())]
                        hits += _prefix(la, lb, K) == _prefix(a[r], b[r], K)
                return hits, width

            big, width = map_acc(lambda b: N_BIG)
            same, _ = map_acc(lambda b: max(8, b // width))
            map_bits = N_BIG * width
            assert ok == tot  # P2
            assert 100 * big >= 99 * tot and 2 * same < tot  # P2
            assert 10 * ex_bits < map_bits  # P3
            yield row(
                m=m,
                exact=f"{ok}/{tot}",
                ex_bits=ex_bits,
                map_acc=_pct(big, tot),
                map_bits=map_bits,
                same_acc=_pct(same, tot),
            )
        yield finding(
            "P2–P3",
            "one subtraction gives every attribute's depth of agreement, exactly, "
            "covering bag (shared concepts) and tree (shared ancestry) at once; "
            "MAP-I matches it only at n = 10,000 with a clean-up per role",
        )

    @verified_section("P4 — frequent concepts on small primes is Huffman-like")
    @table(
        headers=["order", "bits", "vs_random"],
        labels=["prime assignment", "fraction-mode bits (2,000 records)", "÷ random"],
        align=["l", "r", "r"],
        legend={"order": "frequency: most frequent attribute → smallest prime"},
    )
    def _huffman():
        attrs, records = 1000, 2000
        primes = odd_primes(attrs, start_after=4)
        present = [
            [i for i in range(attrs) if rng.randrange(i + 1) == 0]
            for _ in range(records)
        ]
        paths = [
            {i: tuple(rng.randrange(1, 4) for _ in range(K)) for i in rec}
            for rec in present
        ]
        shuffled = list(range(attrs))
        rng.shuffle(shuffled)
        orders = {
            "frequency": list(range(attrs)),
            "random": shuffled,
            "reversed": list(reversed(range(attrs))),
        }
        sizes = {}
        for name, order in orders.items():
            total = 0
            for rec in paths:
                F = sum(
                    (
                        Fraction(
                            encode_path(p, primes[order[i]]), primes[order[i]] ** K
                        )
                        for i, p in rec.items()
                    ),
                    Fraction(0),
                )
                F -= F.numerator // F.denominator
                total += F.numerator.bit_length() + F.denominator.bit_length()
            sizes[name] = total
        assert 100 * sizes["frequency"] <= 75 * sizes["random"]  # P4
        assert sizes["reversed"] == max(sizes.values())  # P4
        for name, bits in sizes.items():
            h = 100 * bits // sizes["random"]
            yield row(order=name, bits=bits, vs_random=f"{h // 100}.{h % 100:02d}×")
        yield finding(
            "P4",
            "giving frequent concepts the smallest primes cuts the size of sparse "
            "records to about 0.6× a random assignment: frequent concepts get the "
            "cheapest keys, as a Huffman code gives frequent symbols the shortest words",
        )

    _bag()
    _combined()
    _huffman()


if __name__ == "__main__":
    run()
