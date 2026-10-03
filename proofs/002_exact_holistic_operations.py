"""
002 — Exact holistic operations, and why re-binding cannot be one

Promoted from exploration 037 (explorations/). Library: rhind.memory
(ExactMemory.key_bag / holding / analogy / agreeing / rebind).

VSAs are used for operations on whole structures: analogy through a mapping
vector, graded similarity between composite records, re-binding a role. A
record here is F = Σ v/q over role primes, with its key bag S = Σ 1/q.
  holding(x)   D / den(F − x·S): subtracting x from every value at once makes
               exactly the roles holding x vanish from the denominator
  analogy      "the x of A": the role holding x in B, then A's value there
  agreeing     lcm(D_A, D_B) / den(F_A − F_B): equal values cancel
  rebind       read, then write
Compared with MAP-I (bipolar atoms, integer bundles; named MAP-B here
before 2026-10-02): analogy = clean-up(x ⊙ A ⊙ B); agreeing
count = round(A·B / n); re-binding = read with clean-up, then rewrite. Kanerva
records scaled: m roles, 100 fillers per role, analogy pairs share no filler.

Predictions, on record BEFORE running (exploration 037 measured P1–P4):
  P1  Every exact operation is correct in every trial at every m.
  P2  MAP-I analogy at n = 10,000: ≥ 95% for m ≤ 10, < 50% at m = 100.
      MAP-I at the exact records' bits: < 50% at every m.
  P3  MAP-I exact agreeing-role count at n = 10,000: ≥ 95% for m ≤ 10,
      < 60% at m = 100.
  P4  MAP-I re-binding at n = 10,000: ≥ 95% at every m.
  P5  No additive map moves a value between keys: for primes p ≠ q every
      additive φ: ℤ/p → ℤ/q is zero, since φ(1) = c needs p·c ≡ 0 (mod q).
      So an exact memory, whose key-q value lives in ℤ/q, has no holistic
      re-binding; it must read. (VSAs re-bind linearly because all their roles
      share one group, which is also why they are noisy.) Checked exhaustively
      for all prime pairs below 200.

Exact integers and Fractions; numpy only as an int64 engine for MAP-I. The
plot receives integers.

"""

import random
from fractions import Fraction

import numpy as np

from proofreport import (
    finding,
    plot,
    point,
    proof_report,
    row,
    table,
    verified_section,
)
from rhind import ExactMemory, odd_primes

SEED = 130
VF = 100
MS = (3, 10, 30, 100)
TRIALS = 100


class _Map:
    def __init__(self, m, n, rng):
        self.n = n
        self.roles = rng.choice(
            np.array([-1, 1], dtype=np.int8), size=(m + 1, n)
        ).astype(np.int64)
        self.fill = rng.choice(
            np.array([-1, 1], dtype=np.int8), size=(m * VF, n)
        ).astype(np.int64)

    def record(self, fs):
        return sum(self.roles[r] * self.fill[f] for r, f in enumerate(fs))

    def cleanup(self, v):
        return int((self.fill @ v).argmax())


@proof_report(
    title="002 — Exact holistic operations, and why re-binding cannot be one",
    source=__file__,
)
def run():
    rng = random.Random(SEED)
    rng_np = np.random.default_rng(SEED)
    curve = []

    @verified_section("P1–P4 — analogy, agreeing roles and re-binding against MAP-I")
    @table(
        headers=[
            "m",
            "ex",
            "ex_bits",
            "an",
            "ag",
            "rb",
            "map_bits",
            "an_m",
            "ag_m",
            "rb_m",
        ],
        labels=[
            "roles m",
            "exact: all three ops",
            "exact bits",
            "MAP 10k: analogy",
            "MAP 10k: agreeing count",
            "MAP 10k: re-binding",
            "MAP 10k bits",
            "MAP same bits: analogy",
            "same bits: agreeing",
            "same bits: re-binding",
        ],
        align=["r"] * 10,
        legend={
            "ex": f"correct operations of {3 * TRIALS} (analogy, agreeing roles, re-binding)",
            "an": f"correct of {TRIALS}; analogy pairs share no filler (Kanerva's setting)",
        },
    )
    def _rows():
        for m in MS:
            roles = odd_primes(m + 1, start_after=m * VF + 1)
            bag = ExactMemory.key_bag(roles[:m])

            def make():
                return [r * VF + rng.randrange(VF) for r in range(m)]

            def ex(fs):
                return ExactMemory.build({roles[r]: f + 1 for r, f in enumerate(fs)})

            disjoint, similar = [], []
            for _ in range(TRIALS):
                a = make()
                disjoint += [
                    a,
                    [
                        r * VF + (a[r] - r * VF + 1 + rng.randrange(VF - 1)) % VF
                        for r in range(m)
                    ],
                ]
                b = make()
                for r in rng.sample(range(m), rng.randint(0, m)):
                    b[r] = a[r]
                similar += [a, b]
            ok = 0
            for t in range(TRIALS):
                fa, fb = disjoint[2 * t], disjoint[2 * t + 1]
                r = rng.randrange(m)
                ok += ex(fa).analogy(ex(fb), fb[r] + 1, bag) == fa[r] + 1
                ga, gb = similar[2 * t], similar[2 * t + 1]
                want = 1
                for i in range(m):
                    if ga[i] == gb[i]:
                        want *= roles[i]
                ok += ex(ga).agreeing(ex(gb)) == want
                moved = ex(fa).rebind(roles[r], roles[m])
                ok += moved.get(roles[m]) == fa[r] + 1 and roles[r] not in moved
            assert ok == 3 * TRIALS  # P1
            ex_bits = sum(ex(fs).bits() for fs in disjoint) // len(disjoint)

            res = {}
            for label, n in (
                ("10k", 10000),
                ("same", max(8, ex_bits // (2 * m + 1).bit_length())),
            ):
                M = _Map(m, n, rng_np)
                dv = [M.record(fs) for fs in disjoint]
                sv = [M.record(fs) for fs in similar]
                an = ag = rb = 0
                for t in range(TRIALS):
                    fa, fb = disjoint[2 * t], disjoint[2 * t + 1]
                    r = rng.randrange(m)
                    A, B = dv[2 * t], dv[2 * t + 1]
                    an += M.cleanup(M.fill[fb[r]] * (A * B)) == fa[r]
                    ga, gb = similar[2 * t], similar[2 * t + 1]
                    ag += round(int(sv[2 * t] @ sv[2 * t + 1]) / n) == sum(
                        ga[i] == gb[i] for i in range(m)
                    )
                    f = M.cleanup(M.roles[r] * A)
                    moved = A - M.roles[r] * M.fill[f] + M.roles[m] * M.fill[f]
                    rb += M.cleanup(M.roles[m] * moved) == fa[r]
                res[label] = (an, ag, rb, n * (2 * m + 1).bit_length())
            an, ag, rb, mbits = res["10k"]
            if m <= 10:
                assert 100 * an >= 95 * TRIALS and 100 * ag >= 95 * TRIALS  # P2, P3
            if m == 100:
                assert 2 * an < TRIALS and 100 * ag < 60 * TRIALS  # P2, P3
            assert 100 * rb >= 95 * TRIALS  # P4
            assert 2 * res["same"][0] < TRIALS  # P2
            curve.append(
                (m, 1000, 1000 * an // TRIALS, 1000 * res["same"][0] // TRIALS)
            )
            yield row(
                m=m,
                ex=f"{ok}/{3 * TRIALS}",
                ex_bits=ex_bits,
                an=an,
                ag=ag,
                rb=rb,
                map_bits=mbits,
                an_m=res["same"][0],
                ag_m=res["same"][1],
                rb_m=res["same"][2],
            )
        yield finding(
            "P1–P4",
            "every exact operation correct at every m, at a small fraction of MAP-I's "
            "storage; MAP-I's analogy and agreeing counts degrade with record size",
        )

    @verified_section("P5 — no additive map moves a value between keys")
    @table(
        headers=["bound", "pairs", "nonzero"],
        labels=[
            "primes below",
            "ordered pairs (p, q), p ≠ q",
            "additive maps ℤ/p → ℤ/q other than 0",
        ],
        align=["r", "r", "r"],
    )
    def _hom():
        """An additive φ: ℤ/p → ℤ/q is determined by c = φ(1) and needs
        p·c ≡ 0 (mod q). Counting the admissible nonzero c for every pair:"""
        ps = odd_primes(46)  # odd primes below 200
        ps = [2] + [p for p in ps if p < 200]
        nonzero = sum(
            1 for p in ps for q in ps if p != q for c in range(1, q) if p * c % q == 0
        )
        pairs = len(ps) * (len(ps) - 1)
        assert nonzero == 0  # P5
        yield row(bound=200, pairs=pairs, nonzero=nonzero)
        yield finding(
            "P5",
            "every additive map between distinct prime keys is zero, so re-binding "
            "must read the value out to ℤ: there is no holistic exact form",
        )

    @verified_section("Analogy as records grow")
    @plot(
        kind="line",
        title="Analogy accuracy (per mille) against roles per record",
        xlabel="roles per record m",
        ylabel="correct analogies, per mille",
    )
    def _curve():
        """The exact analogy is correct at every size by construction. MAP-I's
        mapping vector A ⊙ B carries m² cross terms, so its signal-to-noise
        falls like √n/m: fine at n = 10,000 for small records, gone by m = 100,
        and never usable at the exact records' storage."""
        for m, ex, ten, same in curve:
            yield point(m, exact=ex, **{"MAP n=10,000": ten, "MAP same bits": same})

    _rows()
    _hom()
    _curve()


if __name__ == "__main__":
    run()
