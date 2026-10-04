"""
004 — Graded nearness: q-adic agreement depth, exact and holistic

Promoted from exploration 042 (explorations/). Library: rhind.adic
(Schema, AdicMemory, encode_path).

Each prime key q carries a precision k; a value is an element of ℤ/q^k,
stored as v/q^k. Two values agree to depth j when their last j base-q
digits are equal. For a record F and a probe P on the same schema, the
q-part of den(F − P) is q^(k − depth), so ONE subtraction gives every
role's depth. With hierarchical items (encode_path: the root's choice is
the last digit) the depth is the number of shared ancestor levels.

Setup: a taxonomy of k = 4 levels, branching 4 (256 leaves); a record of m
roles, role r the prime q_r (from 5 up) holding a leaf in base q_r. Probe
depths are prescribed uniformly in {0,…,4}, so a fixed guess scores 20%.
  Q1  role-wise depth to a probe item.     exact: agreement_with(probe)
      MAP-I: h(path) = Σ_levels P(prefix); R = Σ role ⊙ h(item);
      depth = clip(round(h(probe) · (role ⊙ R) / n)).
  Q2  role-wise depth between two records. exact: agreement_with(other)
      MAP-I: clean up role ⊙ R_A and role ⊙ R_B to their nearest leaves
      (256-leaf argmax), then the depth between the two leaves.
  Q3  similarity that is not a shared prefix, INSIDE ONE VALUE: leaves as 4
      independent attributes packed into one value; similarity = number of
      shared attributes. (One attribute per key recovers that count exactly;
      that is proof 005.)

Predictions, on record BEFORE running (exploration 042 measured them):
  P1  Exact Q1 and Q2 depths are right for every role of every record, at
      m = 3, 10, 30, 100; the exact record is under a tenth of MAP-I's bits
      at n = 10,000.
  P2  MAP-I Q1 at n = 10,000: ≥ 99% for m ≤ 10, ≥ 95% at m = 30, 70–90% at
      m = 100. At the exact record's bits: < 50% at every m.
      (Revised 2026-10-04 after a second cold review: the 90% ceiling at
      m = 100 is no longer asserted. A ceiling on a baseline makes the proof
      fail when the baseline does better, which says nothing against the
      exact memory; the floors stay.)
  P3  Comparing two records role-wise WITHOUT clean-up is impossible in
      MAP-I: (role ⊙ R_A) · (role ⊙ R_B) = R_A · R_B for every role, since
      role ⊙ role = 1. Asserted as an identity on every record.
  P4  MAP-I Q2 with clean-up at n = 10,000: ≥ 95% at every m. At the exact
      record's bits: < 50%.
  P5  Q3 over all 65,536 ordered pairs: the depth of ONE value equals the
      shared-attribute count for exactly 121/256 of them (the pairs whose
      shared attributes form a prefix, Σ_j (1/4)^j (3/4)^(4−j)); a MAP-I
      attribute bag at n = 10,000 recovers the count for ≥ 99% of 5,000
      pairs. This bounds nearness within a value, not within a record:
      proof 005 puts each attribute on its own key and gets every pair.

Exact integers and Fractions; numpy only as an int64 engine for MAP-I.
Timings are measurements, in whole microseconds.
"""

import random
import time
from fractions import Fraction
from itertools import product

import numpy as np

from proofreport import finding, proof_report, row, table, verified_section
from rhind import AdicMemory, Schema, encode_path, odd_primes

SEED = 42
K, B = 4, 4
MS = (3, 10, 30, 100)
TRIALS = 40
CLEAN_TRIALS = 10
N_BIG = 10000
LEAVES = list(product(range(B), repeat=K))


def _probe(path, j, rng):
    if j == K:
        return list(path)
    out = list(path[:j]) + [rng.choice([c for c in range(B) if c != path[j]])]
    return out + [rng.randrange(B) for _ in range(K - j - 1)]


def _shared(a, b):
    j = 0
    while j < K and a[j] == b[j]:
        j += 1
    return j


def _est(dot, n):
    return max(0, min(K, (2 * int(dot) + n) // (2 * n)))


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

    def h(self, path):
        return sum(self.v(("p", tuple(path[: i + 1]))) for i in range(K))

    def record(self, paths):
        return sum(self.roles[r] * self.h(p) for r, p in enumerate(paths))


def _pct(a, b):
    return f"{100 * a // b}%"


@proof_report(
    title="004 — Graded nearness: q-adic agreement depth, exact and holistic",
    source=__file__,
)
def run():
    rng = random.Random(SEED)

    @verified_section("P1–P4 — role-wise graded nearness against MAP-I")
    @table(
        headers=[
            "m",
            "ex_q1",
            "ex_q2",
            "ex_bits",
            "ex_us",
            "map_bits",
            "map_q1",
            "map_q2",
            "same_q1",
            "same_q2",
        ],
        labels=[
            "roles m",
            "exact Q1",
            "exact Q2",
            "exact bits",
            "exact µs",
            "MAP bits (n=10,000)",
            "MAP Q1",
            "MAP Q2 (clean-up)",
            "same bits: Q1",
            "same bits: Q2",
        ],
        align=["r"] * 10,
        legend={
            "ex_q1": "roles whose depth to the probe is right",
            "ex_us": "one agreement_with call for all roles",
            "map_q2": f"clean-up to the nearest of 256 leaves; {CLEAN_TRIALS} records per m",
            "same_q1": "MAP-I with n chosen so its counters use the exact record's bits",
        },
    )
    def _roles():
        for m in MS:
            keys = odd_primes(m, start_after=B)
            schema = Schema({q: K for q in keys})
            ok1 = ok2 = tot = us = 0
            recs = []
            for _ in range(TRIALS):
                paths = [rng.choice(LEAVES) for _ in keys]
                js = [rng.randrange(K + 1) for _ in keys]
                probes = [_probe(p, j, rng) for p, j in zip(paths, js)]
                other = [_probe(p, rng.randrange(K + 1), rng) for p in paths]
                enc = lambda ps: AdicMemory.build(
                    {q: encode_path(p, q) for q, p in zip(keys, ps)}, schema
                )
                mem, pm, om = enc(paths), enc(probes), enc(other)
                t0 = time.perf_counter_ns()
                a1 = mem.agreement_with(pm)
                us += (time.perf_counter_ns() - t0) // 1000
                a2 = mem.agreement_with(om)
                ok1 += sum(a1[q] == j for q, j in zip(keys, js))
                ok2 += sum(
                    a2[q] == _shared(p, o) for q, p, o in zip(keys, paths, other)
                )
                tot += m
                recs.append((paths, probes, other, mem.bits()))
            assert ok1 == tot and ok2 == tot  # P1
            ex_bits = max(r[3] for r in recs)

            def map_run(n_of):
                nr = np.random.default_rng(SEED + m)
                h1 = width = 0
                for paths, probes, other, b in recs:
                    n = n_of(b)
                    M = _Map(m, n, nr)
                    R, Ro = M.record(paths), M.record(other)
                    width = max(width, (2 * int(np.abs(R).max()) + 1).bit_length())
                    for r, (p, pr) in enumerate(zip(paths, probes)):
                        u = M.roles[r] * R
                        h1 += _est(M.h(pr) @ u, n) == _shared(p, pr)
                        # P3: without clean-up, the role cancels out
                        assert int(u @ (M.roles[r] * Ro)) == int(R @ Ro)
                h2 = 0
                for paths, probes, other, b in recs[:CLEAN_TRIALS]:
                    n = n_of(b)
                    M = _Map(m, n, nr)
                    H = np.stack([M.h(leaf) for leaf in LEAVES])
                    la = (H @ (M.roles * M.record(paths)).T).argmax(axis=0)
                    lb = (H @ (M.roles * M.record(other)).T).argmax(axis=0)
                    h2 += sum(
                        _shared(LEAVES[int(x)], LEAVES[int(y)]) == _shared(p, o)
                        for x, y, p, o in zip(la, lb, paths, other)
                    )
                return h1, h2, width

            b1, b2, width = map_run(lambda b: N_BIG)
            map_bits = N_BIG * width
            s1, s2, _ = map_run(lambda b: max(8, b // width))
            clean_tot = m * CLEAN_TRIALS
            assert 10 * ex_bits < map_bits  # P1
            lo = {3: 99, 10: 99, 30: 95, 100: 70}[m]
            assert lo * tot <= 100 * b1  # P2
            assert 2 * s1 < tot  # P2
            assert 100 * b2 >= 95 * clean_tot  # P4
            assert 2 * s2 < clean_tot  # P4
            yield row(
                m=m,
                ex_q1=f"{ok1}/{tot}",
                ex_q2=f"{ok2}/{tot}",
                ex_bits=ex_bits,
                ex_us=us // TRIALS,
                map_bits=map_bits,
                map_q1=_pct(b1, tot),
                map_q2=_pct(b2, clean_tot),
                same_q1=_pct(s1, tot),
                same_q2=_pct(s2, clean_tot),
            )
        yield finding(
            "P1–P4",
            "every role's depth is exact from one subtraction, at under a tenth "
            "of MAP-I's bits; MAP-I needs n = 10,000 and, to compare records "
            "role-wise, a clean-up, because without one the role cancels and "
            "only the whole-record similarity R_A · R_B remains",
        )

    @verified_section("P5 — inside one value, nearness is a shared prefix")
    @table(
        headers=["pairs", "prefix_ok", "fraction", "bag_ok"],
        labels=[
            "ordered pairs",
            "one value: depth = shared attributes",
            "as a fraction",
            "MAP-I bag (n=10,000)",
        ],
        align=["r", "r", "r", "r"],
        legend={"bag_ok": "Σ of attribute vectors; 5,000 random pairs"},
    )
    def _boundary():
        hit = sum(
            _shared(a, b) == sum(x == y for x, y in zip(a, b))
            for a in LEAVES
            for b in LEAVES
        )
        total = len(LEAVES) ** 2
        frac = Fraction(hit, total)
        assert frac == Fraction(121, 256)  # P5
        nr = np.random.default_rng(SEED)
        av = {
            (i, c): nr.choice(np.array([-1, 1], dtype=np.int64), size=N_BIG)
            for i in range(K)
            for c in range(B)
        }
        bag = {a: sum(av[(i, c)] for i, c in enumerate(a)) for a in LEAVES}
        pairs = [(rng.choice(LEAVES), rng.choice(LEAVES)) for _ in range(5000)]
        ok = sum(
            _est(bag[a] @ bag[b], N_BIG) == sum(x == y for x, y in zip(a, b))
            for a, b in pairs
        )
        assert 100 * ok >= 99 * len(pairs)  # P5
        yield row(
            pairs=total,
            prefix_ok=hit,
            fraction=f"{frac.numerator}/{frac.denominator}",
            bag_ok=f"{ok}/{len(pairs)}",
        )
        yield finding(
            "P5",
            "inside ONE value, q-adic depth sees only the shared prefix: packing "
            "four attributes into one value matches the shared-attribute count "
            "for exactly 121/256 of pairs; one attribute per key matches every "
            "pair (proof 005)",
        )

    _roles()
    _boundary()


if __name__ == "__main__":
    run()
