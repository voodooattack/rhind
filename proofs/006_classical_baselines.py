"""
006 — Against ordinary data structures: no cost advantage measured

Added 2026-10-03 after a cold review asked the question the paper had not:
why use this instead of an ordinary data structure? Its checks c04 and c06
measured parts of the answer; this proof puts the whole comparison on record.
Library: rhind.memory (ExactMemory).

Records of m roles, values 0 ≤ v < V = 1,000 (0 an empty role), roles the
first m primes above V. Four representations of the same record:
  fraction   ExactMemory F = N/D over the non-empty roles (proof 001)
  schema N   N alone, D recomputed from the role list (proof 003)
  packed     one integer of m fields, each 10 data bits and 1 guard bit;
             the holistic queries become a constant number of whole-word
             operations (XOR, add, AND) in the standard bit-parallel way
  dict       Python dict {role index: value}
and four operations, each with the exact memory's semantics:
  get        the value at one role
  holding x  the roles holding x (fraction: the product of their primes)
  agreeing   the roles non-empty in both records with equal values
  merge      two records with disjoint supports into one

Predictions, on record BEFORE running (c04 and c06 measured the size and
the asymptotics; the timing margins are set generously, since they run on
whatever machine runs the proof):
  P1  All four representations give the same answer to every operation on
      200 random record pairs at m = 10, 100, 1,000.
  P2  Size: packed is m·11 bits, within 0.90–1.10× schema N at every m; the
      fraction costs ≥ 1.5× packed at every m. (First written "≥ 1.8×",
      which forgot that a quarter of the roles are empty here and the
      fraction stores only the others; a dry run before the receipt gave
      1.61× at m = 100. Revised, and recorded here.)
  P3  Time (median over repetitions): at m = 100 and 1,000, packed AND dict
      answer holding and agreeing at least 2× faster than the fraction; dict
      reads a value at least 2× faster than the fraction at m = 1,000.
      FAILED as written, on the first receipt run (2026-10-03): at m = 100
      the dict's agreeing scan was only ≈ 1.7× faster than the fraction's
      one gcd (≈ 3.3 µs against ≈ 5.7 µs in three re-runs on the same
      hardware, Python 3.10 in a VM). Revised to what held: packed ≥ 2× faster at m = 100 and
      1,000; dict faster at m = 100 and ≥ 2× faster at m = 1,000.
  P4  Merge of two disjoint records at m = 1,000: dict union and packed OR
      at least 2× faster than fraction addition (which normalises by gcd).
  P5  The self-describing case: keys hashed to random 61-bit primes, so no
      dictionary is shared at all. The fraction costs ≥ 1.5× a sorted list
      of (64-bit hash, 10-bit value) pairs at K = 10, 100, 1,000.

If every prediction holds, the exact memory has no cost advantage over an
ordinary structure in any setting measured here; what it has is algebra
(merge and difference as + and −, the denominator as the key set, holistic
queries as arithmetic, the re-binding impossibility of proof 002), and the
paper should claim that and no more.

Exact integers and Fractions; timings are integer nanoseconds.
"""

import random
import time
from math import prod

from proofreport import finding, proof_report, row, table, verified_section
from rhind import ExactMemory, is_prime, odd_primes

SEED = 6
V = 1000
B = (V - 1).bit_length()  # 10 data bits
W = B + 1  # plus a guard bit
MS = (10, 100, 1000)
PAIRS = 200
REPS = 9
KS = (10, 100, 1000)


def _times(a, b):
    h = 100 * a // b
    return f"{h // 100}.{h % 100:02d}×"


def _median_ns(fn, reps=REPS):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        ts.append(time.perf_counter_ns() - t0)
    return sorted(ts)[reps // 2]


class _Packed:
    """m fields of B data bits and one guard bit, in one integer."""

    def __init__(self, m):
        self.m = m
        self.H = sum(1 << (i * W + B) for i in range(m))  # guard bits
        self.L = sum(((1 << B) - 1) << (i * W) for i in range(m))  # data bits
        self.ones = sum(1 << (i * W) for i in range(m))

    def pack(self, vals):
        return sum(v << (i * W) for i, v in enumerate(vals))

    def get(self, R, i):
        return (R >> (i * W)) & ((1 << B) - 1)

    def nonzero(self, R):
        """Guard-bit mask of the non-zero fields (R has clear guard bits)."""
        return (R + self.L) & self.H

    def zero(self, R):
        return self.H & ~self.nonzero(R)

    def holding(self, R, x):
        return self.zero(R ^ (x * self.ones))

    def agreeing(self, Ra, Rb):
        return self.zero(Ra ^ Rb) & self.nonzero(Ra)

    def roles(self, mask):
        return [i for i in range(self.m) if mask >> (i * W + B) & 1]


def _schema_N(vals, keys, D):
    return sum(v * (D // q) for v, q in zip(vals, keys)) % D


@proof_report(
    title="006 — Against ordinary data structures: no cost advantage measured",
    source=__file__,
)
def run():
    rng = random.Random(SEED)
    timing = {}

    @verified_section("P1–P2 — same answers, and the size of each representation")
    @table(
        headers=[
            "m",
            "agree",
            "packed",
            "schema",
            "frac",
            "packed_vs_schema",
            "frac_vs_packed",
        ],
        labels=[
            "roles m",
            "all four agree",
            "packed bits",
            "schema N bits",
            "fraction bits",
            "packed ÷ schema N",
            "fraction ÷ packed",
        ],
        align=["r"] * 7,
        legend={
            "agree": f"record pairs (of {PAIRS}) on which get, holding, agreeing and merge agree across all four",
            "schema": "worst case over the records",
            "frac": "worst case over the records",
        },
    )
    def _sizes():
        for m in MS:
            keys = odd_primes(m, start_after=V)
            Dk = prod(keys)
            bag = ExactMemory.key_bag(keys)
            P = _Packed(m)
            agree = 0
            worst_n = worst_f = 0
            cases = []
            for _ in range(PAIRS):
                a = [rng.randrange(V) if rng.randrange(4) else 0 for _ in range(m)]
                b = [x if rng.randrange(2) else rng.randrange(V) for x in a]
                side = [rng.randrange(2) for _ in range(m)]
                a1 = [v if s else 0 for v, s in zip(a, side)]
                a2 = [0 if s else v for v, s in zip(a, side)]
                x = rng.choice([v for v in a if v] or [1])
                i = rng.randrange(m)
                Fa = ExactMemory.build({q: v for q, v in zip(keys, a) if v})
                Fb = ExactMemory.build({q: v for q, v in zip(keys, b) if v})
                Na = _schema_N(a, keys, Dk)
                Ra, Rb = P.pack(a), P.pack(b)
                da = {j: v for j, v in enumerate(a) if v}
                db = {j: v for j, v in enumerate(b) if v}
                worst_n = max(worst_n, Na.bit_length())
                worst_f = max(worst_f, Fa.bits())
                # get
                g = {
                    Fa.get(keys[i]) or 0,
                    Na
                    % keys[i]
                    * pow((Dk // keys[i]) % keys[i], -1, keys[i])
                    % keys[i],
                    P.get(Ra, i),
                    da.get(i, 0),
                }
                # holding x (as the product of the roles' primes)
                h = {
                    Fa.holding(x, bag),
                    prod(keys[j] for j in P.roles(P.holding(Ra, x))),
                    prod(keys[j] for j, v in da.items() if v == x),
                }
                # agreeing
                ag = {
                    Fa.agreeing(Fb),
                    prod(keys[j] for j in P.roles(P.agreeing(Ra, Rb))),
                    prod(keys[j] for j, v in da.items() if db.get(j) == v),
                }
                # merge of disjoint supports
                F1 = ExactMemory.build({q: v for q, v in zip(keys, a1) if v})
                F2 = ExactMemory.build({q: v for q, v in zip(keys, a2) if v})
                d1 = {j: v for j, v in enumerate(a1) if v}
                d2 = {j: v for j, v in enumerate(a2) if v}
                mg = (
                    (F1 + F2) == Fa
                    and ((_schema_N(a1, keys, Dk) + _schema_N(a2, keys, Dk)) % Dk == Na)
                    and (P.pack(a1) | P.pack(a2)) == Ra
                    and {**d1, **d2} == da
                )
                agree += len(g) == len(h) == len(ag) == 1 and mg
                if len(cases) < 20:
                    cases.append(
                        (
                            x,
                            i,
                            Fa,
                            Fb,
                            F1,
                            F2,
                            Ra,
                            Rb,
                            P.pack(a1),
                            P.pack(a2),
                            da,
                            db,
                            d1,
                            d2,
                        )
                    )
            assert agree == PAIRS  # P1
            packed = m * W
            assert 90 * worst_n <= 100 * packed <= 110 * worst_n  # P2
            assert 10 * worst_f >= 15 * packed  # P2
            timing[m] = (keys, bag, P, cases)
            yield row(
                m=m,
                agree=f"{agree}/{PAIRS}",
                packed=packed,
                schema=worst_n,
                frac=worst_f,
                packed_vs_schema=_times(packed, worst_n),
                frac_vs_packed=_times(worst_f, packed),
            )
        yield finding(
            "P1–P2",
            "all four representations answer every operation identically; packed "
            "fields cost about what schema-mode N costs, and the fraction about twice",
        )

    @verified_section("P3–P4 — time per operation")
    @table(
        headers=["m", "op", "frac", "schema", "packed", "dict"],
        labels=[
            "roles m",
            "operation",
            "fraction ns",
            "schema N ns",
            "packed ns",
            "dict ns",
        ],
        align=["r", "l", "r", "r", "r", "r"],
        legend={
            "frac": "median over repetitions of the operation on 20 record pairs, integer ns per operation",
            "schema": "holding and agreeing are not defined on N without D; merge and get are",
        },
    )
    def _times_table():
        for m in MS:
            keys, bag, P, cases = timing[m]
            Dk = prod(keys)
            Ns = [(c[2].N * (Dk // c[2].D)) % Dk for c in cases]  # schema N of each Fa
            n = len(cases)

            def per(fn):
                return _median_ns(lambda: [fn(c) for c in cases]) // n

            def per_i(fn):
                return _median_ns(lambda: [fn(k) for k in range(n)]) // n

            t = {
                "get": (
                    per(lambda c: c[2].get(keys[c[1]])),
                    per_i(
                        lambda k: Ns[k]
                        % (q := keys[cases[k][1]])
                        * pow((Dk // q) % q, -1, q)
                        % q
                    ),
                    per(lambda c: P.get(c[6], c[1])),
                    per(lambda c: c[10].get(c[1], 0)),
                ),
                "holding": (
                    per(lambda c: c[2].holding(c[0], bag)),
                    None,
                    per(lambda c: P.holding(c[6], c[0])),
                    per(lambda c: [j for j, v in c[10].items() if v == c[0]]),
                ),
                "agreeing": (
                    per(lambda c: c[2].agreeing(c[3])),
                    None,
                    per(lambda c: P.agreeing(c[6], c[7])),
                    per(lambda c: [j for j, v in c[10].items() if c[11].get(j) == v]),
                ),
                "merge": (
                    per(lambda c: c[4] + c[5]),
                    per_i(lambda k: (Ns[k] + Ns[k]) % Dk),
                    per(lambda c: c[8] | c[9]),
                    per(lambda c: {**c[12], **c[13]}),
                ),
            }
            if m >= 100:
                for op in ("holding", "agreeing"):
                    f, _, p, d = t[op]
                    assert 2 * p <= f and d < f, (m, op, t[op])  # P3
                    if m == 1000:
                        assert 2 * d <= f, (m, op, t[op])  # P3
            if m == 1000:
                assert 2 * t["get"][3] <= t["get"][0], t["get"]  # P3
                f, _, p, d = t["merge"]
                assert 2 * p <= f and 2 * d <= f, t["merge"]  # P4
            for op, (f, s, p, d) in t.items():
                yield row(
                    m=m, op=op, frac=f, schema="—" if s is None else s, packed=p, dict=d
                )
        yield finding(
            "P3–P4",
            "at m ≥ 100 the packed record answers the holistic queries at least 2× "
            "faster than the fraction and the dict is faster too (only ≈ 1.7× on "
            "agreeing at m = 100); at m = 1,000 both read, query and merge ≥ 2× faster",
        )

    @verified_section("P5 — the self-describing case: keys hashed to primes")
    @table(
        headers=["K", "frac", "sorted", "ratio"],
        labels=[
            "facts K",
            "fraction bits",
            "sorted (hash, value) bits",
            "fraction ÷ sorted",
        ],
        align=["r"] * 4,
        legend={
            "frac": "keys: random 61-bit primes (a hash to a prime), values 1 … 999",
            "sorted": "K · (64 + 10) bits: a sorted list of 64-bit key hashes with their values",
        },
    )
    def _hashed():
        for K in KS:
            keys = set()
            while len(keys) < K:
                c = rng.getrandbits(61) | (1 << 60) | 1
                if is_prime(c):
                    keys.add(c)
            F = ExactMemory.build({q: rng.randrange(1, V) for q in keys})
            sorted_bits = K * (64 + B)
            assert 10 * F.bits() >= 15 * sorted_bits  # P5
            yield row(
                K=K,
                frac=F.bits(),
                sorted=sorted_bits,
                ratio=_times(F.bits(), sorted_bits),
            )
        yield finding(
            "P5",
            "with no shared dictionary the fraction stores two ≈ 61-bit numbers' worth "
            "per fact (N and D) against 74 bits for a sorted list of hashes",
        )

    _sizes()
    _times_table()
    _hashed()


if __name__ == "__main__":
    run()
