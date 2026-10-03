"""
042 — Graded nearness: q-adic agreement depth against a VSA's similarity.

The exact memory answers equality only (proofs 001–003). rhind.adic gives
each prime key a precision k and reads nearness q-adically: one subtraction
reports, for every key, how many trailing base-q digits its value shares
with a probe. With hierarchical items (encode_path: root choice = last
digit), that depth is the number of shared ancestor levels.

Setup. A taxonomy of k = 4 levels, branching 4 (256 leaves). A record has m
roles; role r is the prime q_r (the primes from 5 up), holding a leaf
encoded in base q_r. Probes are built with a PRESCRIBED shared depth
j ∈ {0,…,4}, uniformly, so guessing one depth scores 20%.
  Q1  role-wise nearness to a probe item: for every role, the shared depth
      between its item and the probe item.
      exact: agreement_with(probe memory), one subtraction for all roles.
      MAP-I: h(path) = Σ_levels P(prefix) (one random ±1 vector per
      distinct prefix), record R = Σ role ⊙ h(item); estimate
      depth = clip(round(h(probe) · (role ⊙ R) / n)).
  Q2  record against record, role-wise: the shared depth of the two
      records' items at every role.
      exact: agreement_with, one subtraction.
      MAP-I (first run): round((role ⊙ R_A) · (role ⊙ R_B) / n).
      MAP-I (added after the first run, see P3): clean up role ⊙ R_A and
      role ⊙ R_B to their nearest leaves (argmax of h(leaf) · u over all
      256 leaves), then the shared depth of the two leaves.
  Q3  the boundary: nearness that is NOT a shared prefix. Leaves as 4
      independent attributes (4 values each); similarity = number of shared
      attributes. q-adic depth sees only the shared PREFIX.

Noise estimates for MAP-I (entries of h have variance k; each other role
adds a random term): Q1 σ ≈ k·√(n·m), so z = n/(2σ) = √n/(2k√m) = 12.5/√m
at n = 10,000. Q2 is dominated by noise×noise, σ ≈ k·√n·(m − 1), so
z ≈ 12.5/(m − 1).

Predictions, on record BEFORE the first run:
  P1  exact Q1 and Q2 depths are correct for every role of every trial, at
      m = 3, 10, 30, 100.
  P2  MAP-I Q1 at n = 10,000: ≥ 99% for m ≤ 10, ≥ 95% at m = 30, 70–85% at
      m = 100. At the exact record's bits: < 50% at every m.
  P3  MAP-I Q2 at n = 10,000: ≥ 99% at m = 3, 75–90% at m = 10, < 50% at
      m = 30 and m = 100.
  P3' (written AFTER the first run, BEFORE running the clean-up baseline):
      the margin between the true leaf (score ≈ n·k) and a sibling sharing
      k − 1 levels is n, against noise ≈ k·√(n·m) per score, so
      z ≈ 100/(5.7·√m): ≥ 99% for m ≤ 10, ≥ 90% at m = 30, 60–90% at
      m = 100 (both records must clean up right); < 50% at the same bits.
  P4  Q3 over ALL ordered pairs of the 256 attribute leaves: q-adic depth
      equals the shared-attribute count for exactly 121/256 of pairs (the
      pairs whose shared attributes form a prefix:
      Σ_j (1/4)^j (3/4)^(4−j) = 121/256). A MAP-I attribute bag
      (Σ attribute vectors) recovers the count for ≥ 99% of pairs at
      n = 10,000.
  Expected reading: exact graded nearness on trees at a small fraction of
  the bits, holistic for every role at once; nothing for non-tree
  similarity, which is where a VSA's bag similarity has no rival here.

Exact integers and Fractions; numpy only as an int64 engine for MAP-I.

Results (2026-10-03, ~2 min). Accuracy = role-wise depths exactly right;
uniform prescribed depths, so one fixed guess scores 20%.

    m  exact Q1/Q2   bits   µs   MAP n=10⁴: Q1  Q2 naive  Q2 clean-up   same bits: Q1  Q2 clean-up
    3  120/120 both    35    3            100%     32%        100%                 28%      26%
   10  400/400        161    7            100%     19%        100%                 31%      25%
   30  1200/1200      664   16             98%     21%        100%                 35%      29%
  100  4000/4000    2,982   82             81%     19%         99%                 35%      27%

  Q3: q-adic depth = shared-attribute count for 30,976/65,536 pairs, exactly
      121/256; MAP-I attribute bag 5,000/5,000.

  P1 HELD: every exact depth right, Q1 and Q2, at every m; one subtraction
     per query (82 µs for 100 roles).
  P2 HELD: MAP-I Q1 100/100/98/81% at n = 10,000 (predicted ≥ 99, ≥ 99,
     ≥ 95, 70–85); at the exact record's bits 28–35%.
  P3 FAILED, and the fault was the baseline, not MAP: unbinding both
     records and taking the dot product gives (role ⊙ R_A)·(role ⊙ R_B) =
     R_A · R_B, because role ⊙ role = 1. It is the WHOLE-record similarity,
     identical for every role (19–32%, near the 20% base rate). Role-wise
     comparison in a VSA needs a clean-up first, so the baseline was
     corrected (P3'), the naive column kept as a record.
  P3' FAILED on the pessimistic side: clean-up scored 100/100/100/99%, not
     60–90% at m = 100. The model treated each leaf's score noise as
     independent; but the true leaf and its sibling share k − 1 prefix
     vectors, so their noise is common-mode and only the one differing
     prefix counts: σ_diff ≈ √(2nk(m−1)) ≈ 2,800 against a margin of
     n = 10,000 (z ≈ 3.6). Same-bits clean-up: 25–29%, as predicted.
  P4 HELD exactly: 121/256 of all pairs; the attribute bag got every one.
Reading: for tree-shaped nearness, the exact memory gives every role's
depth from one subtraction at a few thousand bits; MAP-I needs n = 10,000
(≈ 90,000+ bits) and a 256-leaf clean-up per role to match it, and its
direct probe query (Q1) degrades with m. For similarity that is not a
shared prefix, q-adic depth is right only when the shared attributes happen
to form a prefix (121/256), and a VSA bag is right every time: that is the
boundary, and it is structural (the level order IS the model), not noise.
"""

import random
import time
from itertools import product

import numpy as np

from rhind import AdicMemory, Schema, encode_path, odd_primes

SEED = 42
K, B = 4, 4
MS = (3, 10, 30, 100)
TRIALS = 40  # records per m (each gives m role estimates)
CLEAN_TRIALS = 10  # records per m for the clean-up baseline (256 leaves each)
N_BIG = 10000
LEAVES = list(product(range(B), repeat=K))


def probe_path(path, j, rng):
    """A leaf sharing exactly j leading levels with `path`."""
    if j == K:
        return list(path)
    out = list(path[:j]) + [rng.choice([c for c in range(B) if c != path[j]])]
    return out + [rng.randrange(B) for _ in range(K - j - 1)]


def shared(a, b):
    j = 0
    while j < K and a[j] == b[j]:
        j += 1
    return j


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

    def h(self, path):
        return sum(self.v(("p", tuple(path[: i + 1]))) for i in range(K))

    def record(self, paths):
        return sum(self.roles[r] * self.h(p) for r, p in enumerate(paths))


def est(dot, n):
    return max(0, min(K, (2 * int(dot) + n) // (2 * n)))  # round(dot/n), clipped


def main():
    rng = random.Random(SEED)
    for m in MS:
        keys = odd_primes(m, start_after=4)  # bases ≥ 5 > branching
        schema = Schema({q: K for q in keys})
        e1 = e2 = tot = 0
        us = 0
        recs = []
        for _ in range(TRIALS):
            paths = [rng.choice(LEAVES) for _ in keys]
            js = [rng.randrange(K + 1) for _ in keys]
            probes = [probe_path(p, j, rng) for p, j in zip(paths, js)]
            other = [probe_path(p, rng.randrange(K + 1), rng) for p in paths]
            mem = AdicMemory.build(
                {q: encode_path(p, q) for q, p in zip(keys, paths)}, schema
            )
            pm = AdicMemory.build(
                {q: encode_path(p, q) for q, p in zip(keys, probes)}, schema
            )
            om = AdicMemory.build(
                {q: encode_path(p, q) for q, p in zip(keys, other)}, schema
            )
            t0 = time.perf_counter_ns()
            a1 = mem.agreement_with(pm)
            us += (time.perf_counter_ns() - t0) // 1000
            a2 = mem.agreement_with(om)
            e1 += sum(a1[q] == j for q, j in zip(keys, js))
            e2 += sum(a2[q] == shared(p, o) for q, p, o in zip(keys, paths, other))
            tot += m
            recs.append((paths, probes, other, mem.bits()))
        bits = max(r[3] for r in recs)
        line = f"m={m:>3}: exact Q1 {e1}/{tot}, Q2 {e2}/{tot}, {bits} bits, {us // TRIALS} µs/query"
        for label, n in (("n=10,000", N_BIG), ("same bits", None)):
            nr = np.random.default_rng(SEED + m)
            hits1 = hits2 = 0
            width = None
            for paths, probes, other, b in recs:
                nn = n or max(8, b // 8)  # refined below once the width is known
                if n is None and width is not None:
                    nn = max(8, b // width)
                M = Map(m, nn, nr)
                R = M.record(paths)
                Ro = M.record(other)
                w = (2 * int(np.abs(R).max()) + 1).bit_length()
                width = w if width is None else max(width, w)
                for r, (p, pr, o) in enumerate(zip(paths, probes, other)):
                    u = M.roles[r] * R
                    hits1 += est(M.h(pr) @ u, nn) == shared(p, pr)
                    hits2 += est((M.roles[r] * Ro) @ u, nn) == shared(p, o)
            line += f" | MAP {label}: Q1 {100 * hits1 // tot}%, Q2 naive {100 * hits2 // tot}%"
            # Q2 with clean-up to the nearest leaf (P3')
            hits3 = 0
            sub = recs[:CLEAN_TRIALS]
            for paths, probes, other, b in sub:
                nn = n or max(8, b // width)
                M = Map(m, nn, nr)
                H = np.stack([M.h(leaf) for leaf in LEAVES])  # 256 × n
                UA = M.roles * M.record(paths)
                UB = M.roles * M.record(other)
                la = (H @ UA.T).argmax(axis=0)
                lb = (H @ UB.T).argmax(axis=0)
                hits3 += sum(
                    shared(LEAVES[int(x)], LEAVES[int(y)]) == shared(p, o)
                    for x, y, p, o in zip(la, lb, paths, other)
                )
            line += f", Q2 clean-up {100 * hits3 // (m * len(sub))}%"
        print(line)

    # Q3: non-tree similarity, exhaustive
    q = 5
    attr_match = sum(
        shared(a, b) == sum(x == y for x, y in zip(a, b))
        for a in LEAVES
        for b in LEAVES
    )
    total = len(LEAVES) ** 2
    nr = np.random.default_rng(SEED)
    av = {
        (i, c): nr.choice(np.array([-1, 1], dtype=np.int64), size=N_BIG)
        for i in range(K)
        for c in range(B)
    }
    bag = {a: sum(av[(i, c)] for i, c in enumerate(a)) for a in LEAVES}
    sample = [(rng.choice(LEAVES), rng.choice(LEAVES)) for _ in range(5000)]
    bag_ok = sum(
        est(bag[a] @ bag[b], N_BIG) == sum(x == y for x, y in zip(a, b))
        for a, b in sample
    )
    print(
        f"Q3: q-adic depth = shared-attribute count for {attr_match}/{total} pairs"
        f" (121/256 = {121 * total // 256}/{total}); MAP-I attribute bag {bag_ok}/5000"
    )


if __name__ == "__main__":
    main()
