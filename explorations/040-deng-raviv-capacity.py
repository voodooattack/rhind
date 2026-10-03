"""
040 — Deng & Raviv's exact VSA against ExactMemory: bits for K facts.

Record carried over from banana-lab (where the work began); proof and
library names are updated, the reasoning and results are as written then.

PROMOTED 2026-10-02 → proofs/001 (P7). Kept here as the
original exploration record.

Deng & Raviv, "Efficient Vector Symbolic Architectures from Histogram
Recovery" (arXiv 2511.01838) is the closest published exact VSA. Atoms are
Reed–Solomon codewords over F_N (N = p^m) mapped through a Hadamard code to
vectors of p-th roots of unity, length n = N². Each attribute (here: key,
value) owns its own block of the RS message, so a bound key⊗value pair is a
codeword of dimension K = ⌈log_N U⌉ + ⌈log_N V⌉. A bundle of u distinct
codewords is recovered exactly (histogram recovery) when, from their
formula (10),

    u ≤ min{ ⌊d/(d+1) · (N−s)² / ((N−e_g)(K−1))⌋ , ⌊(N−s−r(s−e_g)−1)/(K−1)⌋ }.

Their best case is no noise: s = r = e_g = 0, and d = N−1, which makes both
terms equal: u ≤ ⌊(N−1)/(K−1)⌋. That is the bound used here, which is
generous to them.

Storage of a bundle: each of the n entries is a sum of u p-th roots of
unity, i.e. a histogram of u items over p roots. Charged at its information
content, ⌈log₂ C(u+p−1, p−1)⌉ bits per entry, which is also generous (it is
less than any counter layout). For each u we search every prime power
N = p^m ≤ 2^14 for the cheapest bundle that holds u pairs.

Same universe as proof 001: 20,000 keys, 1,000 values. ExactMemory bits
are measured on random facts, as in 001.

Predictions, on record BEFORE the first run (back of the envelope:
n = N² ≥ (u(K−1)+1)², so their bits grow at least quadratically in u, while
ExactMemory grows linearly):
  P1  At K = 10 facts, Deng–Raviv needs ≥ 30× ExactMemory's bits.
  P2  The ratio grows roughly linearly in K and is in the thousands by
      K = 3,000.
  P3  The cheapest N is binary (p = 2) for large K, where a ±1 entry
      summed u times costs only ⌈log₂(u+1)⌉ bits.
All integer arithmetic.

Results (2026-10-02, < 1 s):

      K   exact bits        DR bits    ratio   field N = p^m   RS dim
     10          325         16,384      50×   2^6  = 64        5
     30          985         81,920      83×   2^7  = 128       5
    100        3,236      1,835,008     567×   2^9  = 512       4
    300        9,836      9,437,184     959×   2^10 = 1024      3
  1,000       32,544     41,943,040   1,288×   2^11 = 2048      3
  3,000       97,434    805,306,368   8,265×   2^13 = 8192      3

  P1 HELD: 50× at K = 10.
  P2 HELD: thousands by K = 3,000 (8,265×). The growth is linear in K
     overall, but in steps: N must be a power of p, so every doubling of N
     quadruples n = N², and the ratio jumps whenever K crosses (N−1)/(K_rs−1).
  P3 HELD: p = 2 is cheapest at every K, not just large ones.
Reading: even granted no noise and information-theoretic storage, their
bundle costs n = N² entries with N ≳ K·(K_rs − 1), so bits ~ K²·log K
against ExactMemory's ~32·K. What it buys is real and we lack: tolerance of
s wrong histograms at ℓ₁ distance r, i.e. noise. The two are not
competitors for the same job: exact-and-fragile at the information floor,
or exact-under-noise at a quadratic premium.

"""

import random
from math import comb

from rhind import ExactMemory, PrimeDictionary

SEED = 40
U, V = 20000, 1000
KS = (10, 30, 100, 300, 1000, 3000)
N_MAX = 1 << 14


def _primes(limit):
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i * i :: i] = bytearray(len(sieve[i * i :: i]))
    return [i for i in range(limit + 1) if sieve[i]]


def _blocks(N, size):
    k, c = 1, N
    while c < size:
        k, c = k + 1, c * N
    return k


def _fields():
    for p in _primes(N_MAX):
        N, m = p, 1
        while N <= N_MAX:
            K = _blocks(N, U) + _blocks(N, V)
            yield p, m, N, K
            N, m = N * p, m + 1


def deng_raviv_bits(u):
    best = None
    for p, m, N, K in _fields():
        if (N - 1) // (K - 1) < u:
            continue
        per = (comb(u + p - 1, p - 1) - 1).bit_length()
        bits = N * N * per
        if best is None or bits < best[0]:
            best = (bits, p, m, N, K, per)
    return best


def main():
    rng = random.Random(SEED)
    dic = PrimeDictionary(range(U), start_after=V)
    print(
        f"{'K':>5} {'exact bits':>11} {'DR bits':>14} {'ratio':>8}  p  m      N  K_rs  bits/entry"
    )
    rows = []
    for K in KS:
        facts = {dic.prime[k]: rng.randrange(1, V) for k in rng.sample(range(U), K)}
        ex = ExactMemory.build(facts).bits()
        bits, p, m, N, Krs, per = deng_raviv_bits(K)
        ratio = bits // ex
        rows.append((K, ex, bits, ratio, p))
        print(
            f"{K:>5} {ex:>11,} {bits:>14,} {ratio:>7,}×  {p:>2} {m:>2} {N:>6} {Krs:>5} {per:>11}"
        )
    assert rows[0][3] >= 30, "P1"
    assert rows[-1][3] >= 1000, "P2"
    return rows


if __name__ == "__main__":
    main()
