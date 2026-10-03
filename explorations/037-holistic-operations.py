"""
037 — Holistic operations: exact versions of what VSAs are used for.

Record carried over from banana-lab (where the work began); proof and
library names are updated, the reasoning and results are as written then.

NAMING (2026-10-02): "MAP-B" in this record is MAP-I in Schlegel et al.'s
taxonomy (bipolar atoms, integer bundles, no thresholding). Current proofs
(001, 002) use MAP-I; this record keeps its original wording.

PROMOTED 2026-10-02 → proofs/002 (claims) and rhind.memory
(ExactMemory.key_bag / holding / analogy / agreeing / rebind; tests/vsa/test_memory.py).
Kept here as the original exploration record.

A VSA's selling point is not lookup but operations on WHOLE structures:
analogy through a mapping vector, graded similarity between composite
records, re-binding. This tests exact counterparts built on ExactMemory
against MAP-B's own operations.

Records (Kanerva's country records, scaled): R records, each with m roles;
role r draws fillers from its own vocabulary of 100 (no filler appears under
two roles). Exact: role = prime > every filler id; a record is
F = Σ (filler+1)/q_role, with its key bag S = Σ 1/q_role (the same roles for
every record, so one S serves all).

The derived exact operations (identity checked on 2,000 random records
before this file was written: den(F − x·S) = ∏{q : v_q ≠ x}):
  roles holding x     D / den(F − x·S)      (subtract x from every value at
                                              once; the matches vanish)
  analogy             "the x of A": the role of x in B, then read A there
  agreeing roles      lcm(D_A, D_B) / den(F_A − F_B)   (equal values cancel)
  re-binding          read v at q_old, then F − v/q_old + v/q_new (baseline;
                      no holistic form known: that is the GP question, 038)
MAP-B (n-dim ±1): record = Σ role ⊙ filler (integer sum).
  analogy             M = A ⊙ B; answer = clean-up(x ⊙ M) over all fillers.
                      Measured on pairs sharing no filler (Kanerva's setting) and,
                      separately, on the similarity pairs, which share some.
  agreeing roles      round(A·B / n)
  re-binding          read f = clean-up(role_old ⊙ A), then A − role_old⊙f + role_new⊙f;
                      success = the moved filler is recalled at role_new
Sizes: n = 10,000, and n matched to the exact record's bits.

Predictions, on record BEFORE the first run (derived noise levels):
  P1  Exact: analogy, agreeing-role count and re-binding are correct in every
      trial at every m.
  P2  MAP-B analogy at n = 10,000: M has m² cross terms, so signal-to-noise is
      ~√n/m: ≥ 95% at m ≤ 10, < 50% at m = 100. At matched bits it fails
      (< 50%) from m = 10.
  P3  MAP-B agreeing-role count (exactly right) at n = 10,000: count noise
      ~ m/√n: ~100% at m ≤ 10, about half or worse at m = 100.
  P4  MAP-B re-binding at n = 10,000 succeeds at every m ≤ 100 (one read with
      noise ~√(n·m) and one write); at matched bits it fails from m = 10.
  P5  Size: an exact record costs ~2·m·log₂ q bits; MAP-B at n = 10,000 costs
      n·log₂(2m+1) bits, i.e. 10–100× more for these m.

Results (2026-10-02, 200 trials per cell; artifact 037_holistic_operations.json):

   m  │ EXACT analogy / agree / rebind │ MAP n=10,000: analogy  agree  rebind │ shared-filler analogy: MAP │ bits exact : MAP
   3  │ 200 / 200 / 200                │ 200  200  200                        │ 164                        │    48 : 30,000
  10  │ 200 / 200 / 200                │ 200  200  200                        │ 131                        │   200 : 50,000
  30  │ 200 / 200 / 200                │  81  174  200                        │ 108                        │   695 : 60,000
 100  │ 200 / 200 / 200                │   1   64  200                        │  87                        │ 2,668 : 80,000
  MAP-B at matched bits failed every operation at every m (analogy 0–8/200).
  Exact ops cost 2–28 µs each.

  P1 HELD: every exact operation correct in every trial at every m,
     including analogy on pairs that share fillers.
  P2 HELD: MAP analogy 100% at m ≤ 10, 40% at m = 30, 0.5% at m = 100;
     fails at matched bits.
  P3 HELD: MAP's exact agreeing-role count 100% at m ≤ 10, 87% at m = 30,
     32% at m = 100.
  P4 HELD: MAP re-binding 100% at every m with n = 10,000; fails at matched bits.
  P5 HELD in direction, larger than predicted: MAP at n = 10,000 is 30–625×
     the exact record (predicted 10–100×).
  Design note: the first run let analogy pairs share fillers (they were the
     similarity pairs), and MAP's analogy sat near 50% at every m. Shared
     fillers put identity terms (role⊙f⊙role⊙f = 𝟏) into M = A ⊙ B, which pull
     the answer toward the query itself. The standard measurement (pairs
     sharing no filler) is now separate, and the shared case is its own column.
     The exact analogy is unaffected by sharing.
Reading: the holistic operations VSAs are used for (analogy through a
mapping, graded similarity between records, re-binding) all have EXACT
counterparts here, correct at every size, at a small fraction of the
storage, where MAP-B's degrade with record size (analogy collapses by
m = 100 at n = 10,000). The one with no holistic exact form yet is
re-binding, which here reads then writes. Exploration 038 asks GP for one.

Usage: python exploration/037-holistic-operations.py
"""

import json
import random
import time
from fractions import Fraction
from math import gcd, prod
from pathlib import Path

import numpy as np

from rhind import ExactMemory, odd_primes

HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"
VF = 100  # fillers per role
MS = (3, 10, 30, 100)
TRIALS = 200


def den(F: Fraction) -> int:
    return (F - (F.numerator // F.denominator)).denominator


# ── exact ─────────────────────────────────────────────────────────────────────


def roles_holding(rec: ExactMemory, S: Fraction, x: int) -> int:
    return rec.D // den(rec.F - x * S)


def agreeing(a: ExactMemory, b: ExactMemory) -> int:
    l = a.D // gcd(a.D, b.D) * b.D
    return l // den(a.F - b.F)


def rebind(rec: ExactMemory, q_old: int, q_new: int) -> ExactMemory:
    v = rec.get(q_old)
    return ExactMemory(rec.F - Fraction(v, q_old) + Fraction(v, q_new))


# ── MAP-B ─────────────────────────────────────────────────────────────────────


class Map:
    def __init__(self, m: int, n: int, rng):
        self.n = n
        self.roles = rng.choice(
            np.array([-1, 1], dtype=np.int8), size=(m + 1, n)
        ).astype(np.int64)
        self.fill = rng.choice(
            np.array([-1, 1], dtype=np.int8), size=(m * VF, n)
        ).astype(np.int64)

    def record(self, fillers):  # fillers: global ids, one per role
        return sum(self.roles[r] * self.fill[f] for r, f in enumerate(fillers))

    def cleanup(self, v):
        return int((self.fill @ v).argmax())


def main() -> None:
    rng = random.Random(37)
    rng_np = np.random.default_rng(37)
    out = {"rows": []}
    for m in MS:
        roles = odd_primes(
            m + 1, start_after=m * VF + 1
        )  # +1: a spare role for re-binding
        S = sum((Fraction(1, q) for q in roles[:m]), Fraction(0))

        def make():
            return [r * VF + rng.randrange(VF) for r in range(m)]

        def exact(fs):
            return ExactMemory.build({roles[r]: f + 1 for r, f in enumerate(fs)})

        disjoint = []  # analogy pairs sharing no filler (Kanerva's setting)
        for _ in range(TRIALS):
            a = make()
            b = [
                r * VF + (a[r] - r * VF + 1 + rng.randrange(VF - 1)) % VF
                for r in range(m)
            ]
            disjoint += [a, b]
        dex = [exact(fs) for fs in disjoint]
        recs = [make() for _ in range(2 * TRIALS)]
        # make some pairs agree on a random subset of roles
        for t in range(TRIALS):
            a, b = recs[2 * t], recs[2 * t + 1]
            for r in rng.sample(range(m), rng.randint(0, m)):
                b[r] = a[r]
        ex = [exact(fs) for fs in recs]
        ex_bits = sum(e.bits() for e in ex) // len(ex)

        res = {"m": m, "exact record bits": ex_bits}
        # exact operations
        an = an_sh = sim = rb = 0
        t0 = time.perf_counter_ns()
        for t in range(TRIALS):
            A, B, fa, fb = (
                dex[2 * t],
                dex[2 * t + 1],
                disjoint[2 * t],
                disjoint[2 * t + 1],
            )
            r = rng.randrange(m)
            q = roles_holding(B, S, fb[r] + 1)
            an += q == roles[r] and A.get(q) == fa[r] + 1
            A, B, fa, fb = ex[2 * t], ex[2 * t + 1], recs[2 * t], recs[2 * t + 1]
            q = roles_holding(B, S, fb[r] + 1)
            an_sh += q == roles[r] and A.get(q) == fa[r] + 1
            sim += agreeing(A, B) == prod(roles[i] for i in range(m) if fa[i] == fb[i])
            moved = rebind(A, roles[r], roles[m])
            rb += (
                moved.get(roles[m]) == fa[r] + 1
                and roles[r] not in moved
                and all(moved.get(roles[i]) == fa[i] + 1 for i in range(m) if i != r)
            )
        res["exact"] = {
            "analogy": f"{an}/{TRIALS}",
            "analogy, pairs sharing fillers": f"{an_sh}/{TRIALS}",
            "agreeing roles": f"{sim}/{TRIALS}",
            "re-binding": f"{rb}/{TRIALS}",
            "us per op": (time.perf_counter_ns() - t0) // (4000 * TRIALS),
        }

        for label, n in (
            ("map n=10000", 10000),
            ("map matched bits", max(8, ex_bits // (2 * m + 1).bit_length())),
        ):
            M = Map(m, n, rng_np)
            vecs = [M.record(fs) for fs in recs]
            dvecs = [M.record(fs) for fs in disjoint]
            res[label + " bits"] = n * (2 * m + 1).bit_length()
            an = an_sh = sim = rb = 0
            for t in range(TRIALS):
                A, B, fa, fb = (
                    dvecs[2 * t],
                    dvecs[2 * t + 1],
                    disjoint[2 * t],
                    disjoint[2 * t + 1],
                )
                r = rng.randrange(m)
                an += M.cleanup(M.fill[fb[r]] * (A * B)) == fa[r]
                A, B, fa, fb = (
                    vecs[2 * t],
                    vecs[2 * t + 1],
                    recs[2 * t],
                    recs[2 * t + 1],
                )
                an_sh += M.cleanup(M.fill[fb[r]] * (A * B)) == fa[r]
                sim += round(int(A @ B) / n) == sum(fa[i] == fb[i] for i in range(m))
                f = M.cleanup(M.roles[r] * A)
                moved = A - M.roles[r] * M.fill[f] + M.roles[m] * M.fill[f]
                rb += M.cleanup(M.roles[m] * moved) == fa[r]
            res[label] = {
                "n": n,
                "analogy": f"{an}/{TRIALS}",
                "analogy, pairs sharing fillers": f"{an_sh}/{TRIALS}",
                "agreeing roles": f"{sim}/{TRIALS}",
                "re-binding": f"{rb}/{TRIALS}",
            }
        out["rows"].append(res)
        print(json.dumps(res), flush=True)
    (ART / "037_holistic_operations.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
