"""
001 — An exact associative memory beats a noisy VSA at every size and budget

Promoted from exploration 036 (explorations/). Library: rhind.memory (ExactMemory).

K facts key → value are superposed into one exact rational, Σ v/q = N/D
(q: the key's prime; values 1 ≤ v < q). Recall reads v = N·(D/q)⁻¹ mod q;
an absent key is absent because q ∤ D. Merge and delete are + and −.
Compared with MAP-I, the standard bipolar VSA with integer bundles (random
±1 vectors, bind by elementwise product, bundle by integer sum; "MAP-I" in
Schlegel et al.'s taxonomy, where MAP-B would threshold the bundle to ±1;
named MAP-B here before 2026-10-02), clean-up by integer dot product
against the value vectors, "present" when the best score ≥ n/2), at two
sizes: n matched to the exact memory's bits, and n = 10,000. And with the
ideal packed table, K·(⌈log₂ keys⌉ + ⌈log₂ values⌉) bits (an ordered table:
not the information floor, see P1b). Universe: 20,000 keys, 1,000 values.

Predictions, on record BEFORE running (exploration 036 measured them):
  P1  ExactMemory recalls every present key and no absent key at every K,
      at ≈ 1.3× the ideal packed table (036: 1.20–1.30; asserted ≤ 1.35).
  P2  MAP-I at the same bits fails from the smallest K; at n = 10,000 it is
      perfect to K = 100, false-recalls by K = 300, and collapses by 1,000.
  P3  ExactMemory queries in microseconds at every K here, faster than
      MAP-I's clean-up (milliseconds).
  P4  Any sequence of inserts, deletes and merges leaves the memory equal to
      one rebuilt from scratch.

Added 2026-10-03 after a cold review (its check c02 computed these): the
packed table is not the information floor. K facts as an unordered set of
keys from U, each with one of V − 1 values, need ⌈log₂(C(U, K)·(V−1)^K)⌉
bits; packing in key order wastes about log₂ K! of them.
  P1b ExactMemory against that set floor: 1.4–1.6× at K = 10, rising with K
      (never falling from one K to the next), below 2.5× at K = 3,000. The
      memory spends ≈ 2 log₂ q per fact; the floor per fact shrinks as K
      grows.

Added 2026-10-02 (the literature survey asked for the strongest dense VSA,
FHRR, next to MAP-I). FHRR: random phasors, bind by elementwise product
(phases add), bundle by sum, clean-up by the real part of the inner product.
Phases here are the 4th roots of unity, so every component is a Gaussian
integer and nothing needs a cosine. That loses nothing: for a uniform phase
on m ≥ 3 points (and for the continuous circle) the real part has mean 0
and variance exactly 1/2, so the noise each stored fact adds to a clean-up
score is the same for m = 4 as for continuous FHRR. Against MAP (variance
1) that halves the noise per dimension, but each component costs two
counters instead of one.

Predictions, on record BEFORE the FHRR runs (from that variance argument,
and the 036 numbers as calibration: clean-up succeeds while
n > ≈3.2·√(noise variance), the max of 1,000 wrong candidates):
  P5  FHRR at the exact memory's bits fails from the smallest K, like
      MAP-I: half the dimensions, each twice as clean, is no gain per bit.
  P6  FHRR at n = 10,000 holds about twice the facts MAP-I does: perfect
      recall to K = 300, ≈ 90% at K = 1,000 (MAP-I ≈ 50%), below half by
      K = 3,000; false recalls a few percent at K = 300, most by K = 1,000.

Added 2026-10-02 from exploration 040 (which measured it): Deng & Raviv's
exact VSA (arXiv 2511.01838). Reed–Solomon codewords over F_N, N = p^m,
through a Hadamard code to n = N² roots of unity; key and value own their
own RS blocks, so a bound pair has RS dimension k = ⌈log_N U⌉ + ⌈log_N V⌉.
Their formula (10) in its noiseless best case (s = r = e_g = 0, d = N−1)
recovers u ≤ ⌊(N−1)/(k−1)⌋ superposed pairs. A bundle entry, a sum of u
p-th roots of unity, is charged only its information content,
⌈log₂ C(u+p−1, p−1)⌉ bits; the cheapest prime power N ≤ 2^14 is taken.
Both choices favour them.
  P7  Deng–Raviv needs ≥ 30× the exact memory's bits at the smallest K and
      thousands of times by K = 3,000 (n = N² with N ≳ K·(k−1): bits grow
      ~ K² log K against the exact memory's linear growth). What that buys,
      noise tolerance, is outside this comparison.

Exact integers and Fractions; numpy is used only as an int64 array engine
for MAP-I. The plot receives integers. Timings are measurements, reported in
whole microseconds.

"""

import random
import time
from math import comb

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
from rhind import ExactMemory, PrimeDictionary

SEED = 129
_RE = np.array([1, 0, -1, 0], dtype=np.int64)  # ζ^p = _RE[p] + i·_IM[p], ζ = i
_IM = np.array([0, 1, 0, -1], dtype=np.int64)
U, V = 20000, 1000
KS = (10, 30, 100, 300, 1000, 3000)
PROBES = 300


def _map(facts_idx, absent, n, rng_np):
    used = sorted({k for k, _ in facts_idx} | set(absent))
    rows = rng_np.choice(np.array([-1, 1], dtype=np.int8), size=(len(used), n)).astype(
        np.int64
    )
    kv = {k: rows[i] for i, k in enumerate(used)}
    vals = rng_np.choice(np.array([-1, 1], dtype=np.int8), size=(V, n)).astype(np.int64)
    mem = np.zeros(n, dtype=np.int64)
    for k, v in facts_idx:
        mem += kv[k] * vals[v]
    bits = n * (2 * int(np.abs(mem).max()) + 1).bit_length()

    def ask(k):
        s = vals @ (kv[k] * mem)
        b = int(s.argmax())
        return b if 2 * int(s[b]) >= n else None

    probe = facts_idx[:PROBES]
    t0 = time.perf_counter_ns()
    ok = sum(ask(k) == v for k, v in probe)
    us = (time.perf_counter_ns() - t0) // (1000 * len(probe))
    false = sum(ask(k) is not None for k in absent)
    return ok, len(probe), false, bits, us


def _fhrr(facts_idx, absent, n, rng_np):
    """FHRR on the 4th roots of unity, exact in Gaussian integers.

    A vector is its phase indices p ∈ ℤ/4 (component ζ^p). Binding adds
    phases, the memory is Σ ζ^(k+v) kept as integer (re, im), and the
    clean-up score of value c for key k is Re Σ_j mem_j·ζ^-(k_j + c_j).
    """
    used = sorted({k for k, _ in facts_idx} | set(absent))
    kp = {k: rng_np.integers(0, 4, size=n, dtype=np.int64) for k in used}
    vp = rng_np.integers(0, 4, size=(V, n), dtype=np.int64)
    re = np.zeros(n, dtype=np.int64)
    im = np.zeros(n, dtype=np.int64)
    for k, v in facts_idx:
        ph = (kp[k] + vp[v]) & 3
        re += _RE[ph]
        im += _IM[ph]
    peak = max(int(np.abs(re).max()), int(np.abs(im).max()))
    bits = 2 * n * (2 * peak + 1).bit_length()
    # Re((a+ib)·(c−id)) = ac + bd, with c + id = ζ^c for each candidate value.
    cd = np.concatenate([_RE[vp], _IM[vp]], axis=1)
    del vp

    def ask(k):
        c, d = _RE[kp[k]], _IM[kp[k]]
        a2 = re * c + im * d  # mem · ζ^-k, real part
        b2 = im * c - re * d  # and imaginary part
        s = cd @ np.concatenate([a2, b2])
        b = int(s.argmax())
        return b if 2 * int(s[b]) >= n else None

    probe = facts_idx[:PROBES]
    t0 = time.perf_counter_ns()
    ok = sum(ask(k) == v for k, v in probe)
    us = (time.perf_counter_ns() - t0) // (1000 * len(probe))
    false = sum(ask(k) is not None for k in absent)
    return ok, len(probe), false, bits, us


def _prime_powers(limit):
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, limit + 1):
        if sieve[i]:
            sieve[i * i :: i] = bytearray(len(sieve[i * i :: i]))
            N, m = i, 1
            while N <= limit:
                yield i, m, N
                N, m = N * i, m + 1


def _rs_blocks(N, size):
    k, c = 1, N
    while c < size:
        k, c = k + 1, c * N
    return k


def _deng_raviv_bits(u, n_max=1 << 14):
    """Cheapest Deng–Raviv bundle holding u key⊗value pairs, noiseless bound."""
    best = None
    for p, m, N in _prime_powers(n_max):
        k = _rs_blocks(N, U) + _rs_blocks(N, V)
        if (N - 1) // (k - 1) < u:
            continue
        bits = N * N * (comb(u + p - 1, p - 1) - 1).bit_length()
        if best is None or bits < best[0]:
            best = (bits, p, m, k)
    return best


@proof_report(
    title="001 — An exact associative memory beats a noisy VSA at every size and budget",
    source=__file__,
)
def run():
    rng = random.Random(SEED)
    rng_np = np.random.default_rng(SEED)
    dic = PrimeDictionary(range(U), start_after=V)
    floor_per = (U - 1).bit_length() + (V - 1).bit_length()
    curve = []
    cases = (
        []
    )  # (K, facts_idx, absent, exact bits, MAP same-bits recall, MAP 10k recall)

    @verified_section(
        "P1–P3 — recall, false recalls, size and speed against MAP-I, the packed table and the set floor"
    )
    @table(
        headers=[
            "K",
            "ex_recall",
            "ex_false",
            "ex_bits",
            "ratio",
            "set_ratio",
            "ex_us",
            "m_recall",
            "m_false",
            "m_us",
            "t_recall",
            "t_false",
        ],
        labels=[
            "facts K",
            "exact: recall",
            "exact: false",
            "exact: bits",
            "÷ packed",
            "÷ set floor",
            "exact: µs",
            "MAP same bits: recall",
            "MAP same bits: false",
            "MAP: µs",
            "MAP n=10,000: recall",
            "MAP n=10,000: false",
        ],
        align=["r"] * 12,
        legend={
            "ratio": "exact memory bits ÷ ideal packed table K·(15 + 10) bits",
            "set_ratio": "exact memory bits ÷ ⌈log₂(C(U, K)·(V−1)^K)⌉, the floor for an unordered set of K facts",
            "ex_false": f"absent keys answered, of {PROBES}",
            "m_recall": "MAP-I with n chosen so its counters use the exact memory's bits",
        },
    )
    def _rows():
        last_set = [0]
        for K in KS:
            keys = rng.sample(range(U), K)
            kset = set(keys)
            absent = [k for k in rng.sample(range(U), PROBES + K) if k not in kset][
                :PROBES
            ]
            facts_idx = [(k, rng.randrange(1, V)) for k in keys]
            mem = ExactMemory.build({dic.prime[k]: v for k, v in facts_idx})
            probe = facts_idx[:PROBES]
            t0 = time.perf_counter_ns()
            ok = sum(mem.get(dic.prime[k]) == v for k, v in probe)
            us = (time.perf_counter_ns() - t0) // (1000 * len(probe))
            false = sum(mem.get(dic.prime[k]) is not None for k in absent)
            assert ok == len(probe) and false == 0  # P1
            ratio = 100 * mem.bits() // (K * floor_per)
            assert 100 <= ratio <= 135, ratio  # P1
            set_floor = (comb(U, K) * (V - 1) ** K - 1).bit_length()
            set_ratio = 100 * mem.bits() // set_floor
            if K == KS[0]:
                assert 140 <= set_ratio <= 160, set_ratio  # P1b
            assert set_ratio < 250 and set_ratio >= last_set[0], set_ratio  # P1b
            last_set[0] = set_ratio
            n = max(8, mem.bits() // (2 * K + 1).bit_length())
            mo, mn, mf, _, mus = _map(facts_idx, absent, n, rng_np)
            assert 2 * mo < mn  # P2
            to, tn, tf = (
                _map(facts_idx, absent, 10000, rng_np)[:3]
                if K <= 1000
                else (None, None, None)
            )
            if to is not None and K <= 100:
                assert to == tn  # P2
            if to is not None and K >= 1000:
                assert 2 * to < tn  # P2
            assert us < mus  # P3
            cases.append((K, facts_idx, absent, mem.bits(), (mo, mn), (to, tn)))
            curve.append(
                (
                    K,
                    1000 * ok // len(probe),
                    1000 * mo // mn,
                    None if to is None else 1000 * to // tn,
                )
            )
            yield row(
                K=K,
                ex_recall=f"{ok}/{len(probe)}",
                ex_false=false,
                ex_bits=mem.bits(),
                ratio=f"{ratio // 100}.{ratio % 100:02d}×",
                set_ratio=f"{set_ratio // 100}.{set_ratio % 100:02d}×",
                ex_us=us,
                m_recall=f"{mo}/{mn}",
                m_false=mf,
                m_us=mus,
                t_recall="—" if to is None else f"{to}/{tn}",
                t_false="—" if tf is None else tf,
            )
        yield finding(
            "P1–P3",
            "exact recall and zero false recalls at every K, at ≈ 1.3× the packed "
            "table (1.5–2.3× the set floor, rising with K) and microsecond queries; MAP-I fails at the same bits from the "
            "smallest K and, at n = 10,000, collapses by K = 1,000",
        )

    fcurve = {}

    @verified_section("P5–P6 — FHRR, the strongest dense VSA, on the same facts")
    @table(
        headers=[
            "K",
            "f_n",
            "f_recall",
            "f_false",
            "m_recall",
            "t_recall",
            "t_false",
            "tm_recall",
            "f_us",
        ],
        labels=[
            "facts K",
            "FHRR same bits: n",
            "FHRR same bits: recall",
            "FHRR same bits: false",
            "MAP same bits: recall",
            "FHRR n=10,000: recall",
            "FHRR n=10,000: false",
            "MAP n=10,000: recall",
            "FHRR: µs",
        ],
        align=["r"] * 9,
        legend={
            "f_n": "dimensions FHRR can afford at the exact memory's bits (two counters each)",
            "f_false": f"absent keys answered, of {PROBES}",
            "tm_recall": "from the P1–P3 table, same facts",
        },
    )
    def _fhrr_rows():
        rng_f = np.random.default_rng(SEED + 1)
        for K, facts_idx, absent, ex_bits, (mo, mn), (to, tn) in cases:
            n = max(8, ex_bits // (2 * (2 * K + 1).bit_length()))
            fo, fn, ff, _, fus = _fhrr(facts_idx, absent, n, rng_f)
            assert 2 * fo < fn  # P5
            go, gn, gf, _, _ = _fhrr(facts_idx, absent, 10000, rng_f)
            if K <= 300:
                assert go == gn  # P6
            if K == 1000:
                assert go * tn > to * gn  # P6: beats MAP-I on the same facts
            if K >= 3000:
                assert 2 * go < gn  # P6
            fcurve[K] = (1000 * fo // fn, 1000 * go // gn)
            yield row(
                K=K,
                f_n=n,
                f_recall=f"{fo}/{fn}",
                f_false=ff,
                m_recall=f"{mo}/{mn}",
                t_recall=f"{go}/{gn}",
                t_false=gf,
                tm_recall="—" if to is None else f"{to}/{tn}",
                f_us=fus,
            )
        yield finding(
            "P5–P6",
            "FHRR is no better than MAP-I per bit (half the dimensions, each "
            "twice as clean) and fails at the exact memory's bits from the "
            "smallest K; at n = 10,000 it holds about twice the facts MAP-I "
            "does, and still collapses while the exact memory stays exact",
        )

    @verified_section("P7 — Deng & Raviv's exact VSA: bits for the same facts")
    @table(
        headers=["K", "ex_bits", "dr_bits", "ratio", "field", "k"],
        labels=[
            "facts K",
            "exact memory: bits",
            "Deng–Raviv: bits",
            "÷ exact",
            "field N",
            "RS dimension",
        ],
        align=["r"] * 6,
        legend={
            "dr_bits": "cheapest N = p^m ≤ 2^14 at their noiseless bound, entries charged their information content",
            "k": "⌈log_N 20,000⌉ + ⌈log_N 1,000⌉",
        },
    )
    def _dr_rows():
        ratios = []
        for K, _, _, ex_bits, _, _ in cases:
            bits, p, m, k = _deng_raviv_bits(K)
            ratios.append(bits // ex_bits)
            yield row(
                K=K,
                ex_bits=ex_bits,
                dr_bits=bits,
                ratio=f"{bits // ex_bits:,}×",
                field=f"{p}^{m}",
                k=k,
            )
        assert ratios[0] >= 30  # P7
        assert ratios[-1] >= 1000  # P7
        assert all(a <= b for a, b in zip(ratios, ratios[1:]))  # P7: the gap only grows
        yield finding(
            "P7",
            "the closest published exact VSA needs 50× the exact memory's bits "
            "at 10 facts and thousands of times at 3,000, even at its noiseless "
            "bound with information-content storage; its premium buys noise "
            "tolerance, which the exact memory does not have",
        )

    @verified_section("P4 — exact under any sequence of inserts, deletes and merges")
    @table(
        headers=["ops", "facts", "equal", "recall"],
        labels=[
            "operations",
            "facts at the end",
            "equals a rebuild",
            "every fact recalls",
        ],
        align=["r", "r", "l", "l"],
    )
    def _ops():
        truth, mem = {}, ExactMemory()
        ops = 2000
        for _ in range(ops):
            r = rng.random()
            if r < 0.5 or not truth:
                q = rng.choice(dic.primes)
                if q not in truth:
                    truth[q] = rng.randrange(1, V)
                    mem += ExactMemory.build({q: truth[q]})
            elif r < 0.8:
                q = rng.choice(sorted(truth))
                mem -= ExactMemory.build({q: truth.pop(q)})
            else:
                batch = {
                    q: rng.randrange(1, V)
                    for q in rng.sample(dic.primes, 5)
                    if q not in truth
                }
                truth.update(batch)
                mem += ExactMemory.build(batch)
        equal = mem == ExactMemory.build(truth)
        recall = all(mem.get(q) == v for q, v in truth.items())
        assert equal and recall  # P4
        yield row(ops=ops, facts=len(truth), equal="yes", recall="yes")

    @verified_section("Recall as the memory fills")
    @plot(
        kind="line",
        title="Recall (per mille) against facts stored",
        xlabel="facts K",
        ylabel="present keys recalled, per mille",
    )
    def _curve():
        """The exact memory stays at 1000 by construction. MAP-I at the same
        bits never gets close; at n = 10,000 (many times the bits) it holds to
        K ≈ 100 and then falls away. FHRR at n = 10,000 holds about twice as
        long and falls away the same way."""
        for K, ex, m, t in curve:
            vals = {"exact": ex, "MAP same bits": m}
            if t is not None:
                vals["MAP n=10,000"] = t
            if K in fcurve:
                vals["FHRR same bits"], vals["FHRR n=10,000"] = fcurve[K]
            yield point(K, **vals)

    _rows()
    _fhrr_rows()
    _dr_rows()
    _ops()
    _curve()


if __name__ == "__main__":
    run()
