"""
041 — Schema mode: when the key set is predictable, store N alone.

PROMOTED 2026-10-03 → proofs/003 (claims). Kept here as the original
exploration record.

A memory is F = N/D with D = ∏ keys. Proof 001 stores both, and that is most
of its ≈ 1.3× overhead over the information floor. If the key set is known
from a rule (a record whose roles are always the first m primes above the
value range, i.e. the linear structural primes q = 2d + 3 from some d on),
D can be recomputed and only N stored:

    encode  N = Σ v_q · (D/q)  mod D          (values 0 ≤ v < V < every q)
    decode  F = N/D, v_q = F.get(q) or 0

This is the integer (CRT secure-lock) form. It gives up what the fraction
adds (absence read from the memory itself); the question is what it buys.

Predictions, on record BEFORE the first run (back of the envelope: N < D,
and ⌈log₂ q⌉ ≈ ⌈log₂ V⌉ while the keys stay near V):
  P1  Round trip is exact for full records of m = 10, 100, 1,000 roles,
      values 0 ≤ v < 1,000 (0 = empty role), 200 records each.
  P2  N alone, against the floor m·⌈log₂ V⌉ = 10m bits: ≤ 1.02× at m = 10,
      ≤ 1.06× at m = 100, ≤ 1.25× at m = 1,000 (keys drift up to ~13 bits).
      Fraction mode (N + D) costs ≈ 2× schema mode at every m.
  P3  Operations survive: merge is (N₁ + N₂) mod D and equals per-role
      (v₁ + v₂) mod q; holding(x) from the rebuilt F equals the true role set.
  P4  For SPARSE memories (K keys out of U = 20,000, by dictionary position),
      the cheapest encoding of the key set is: D itself at K = 10; Elias-γ
      gaps of the positions at K = 100 … 3,000; a U-bit presence bitmap at
      K = 10,000. (D costs ≈ 16–17 bits per key; γ of a gap g costs
      2⌊log₂ g⌋ + 1 with g ≈ U/K; the bitmap costs U/K bits per key.)

All integer arithmetic.

Results (2026-10-03, < 1 min):

     m   round trip   N bits   floor   ratio   N + D (fraction mode)
    10   200/200        101      100   1.01×   202  (2.00× schema)
   100   200/200      1,039    1,000   1.03×   2,078 (2.00×)
 1,000   200/200     12,090   10,000   1.20×   24,180 (2.00×)

     K        D    γ gaps   bitmap   cheapest
    10      156      194    20,000   D
   100    1,620    1,324    20,000   γ gaps
   300    4,854    3,176    20,000   γ gaps
 1,000   16,311    7,470    20,000   γ gaps
 3,000   48,744   14,184    20,000   γ gaps
10,000  162,632   22,738    20,000   bitmap

  P1 HELD at every m.
  P2 HELD: 1.01× / 1.03× / 1.20× the floor; fraction mode is 2.00× schema.
  P3 FAILED on the first run, then HELD after a LIBRARY fix. Merge held at
     every m. holding(x) was wrong for records with an empty role (value 0):
     an empty role contributes −x/q, so q stays in den(F − x·S), but it is
     not in the memory's own D, and D / den is then garbage. Proof 002 never
     met this (its records fill every role). ExactMemory.holding now divides
     lcm(D, D_bag) instead of D (same answer whenever the bag is the memory's
     own key bag; tests/test_memory.py has the empty-role case). Re-run:
     holding exact for every x tried at every m.
  P4 HELD exactly as predicted: D at K = 10, γ gaps from 100 to 3,000, the
     bitmap at 10,000.
Reading: with a predictable key set, schema mode reaches the information
floor for small records (1.01× at 10 roles) and halves fraction mode at
every size, keeping merge and the value query. For sparse memories, D is
the cheapest key-set encoding only when very sparse; from ~100 keys of
20,000 a gap code is cheaper. What schema mode gives up is reading absence
from the memory itself: that knowledge moves to the schema.
"""

import random
from fractions import Fraction
from math import prod

from rhind import ExactMemory, odd_primes

SEED = 41
V = 1000
FLOOR_PER = (V - 1).bit_length()  # 10
MS = (10, 100, 1000)
U = 20000
KS = (10, 100, 300, 1000, 3000, 10000)


def encode(values, keys, D):
    return sum(v * (D // q) for v, q in zip(values, keys)) % D


def decode(N, keys, D):
    mem = ExactMemory(Fraction(N, D))
    return [mem.get(q) or 0 for q in keys]


def gamma_bits(g):
    return 2 * (g.bit_length() - 1) + 1


def main():
    rng = random.Random(SEED)
    print("P1–P3: full records, schema mode")
    for m in MS:
        keys = odd_primes(m, start_after=V)
        D = prod(keys)
        S = Fraction(sum(D // q for q in keys), D)
        ok, nbits = 0, []
        for _ in range(200):
            vals = [rng.randrange(V) for _ in keys]
            N = encode(vals, keys, D)
            ok += decode(N, keys, D) == vals
            nbits.append(N.bit_length())
        # P3 merge and holding
        a = [rng.randrange(V) for _ in keys]
        b = [rng.randrange(V) for _ in keys]
        merged = decode((encode(a, keys, D) + encode(b, keys, D)) % D, keys, D)
        merge_ok = merged == [(x + y) % q for x, y, q in zip(a, b, keys)]
        F = Fraction(encode(a, keys, D), D)
        mem, bag = ExactMemory(F), ExactMemory(S)
        hold_ok = all(
            mem.holding(x, bag) == prod(q for v, q in zip(a, keys) if v == x)
            for x in range(1, V, 37)
        )
        worst = max(nbits)
        print(
            f"  m={m:>5}: round trip {ok}/200, N ≤ {worst} bits, floor {m * FLOOR_PER},"
            f" ratio {100 * worst // (m * FLOOR_PER) / 100:.2f}×, N+D ≈ {worst + D.bit_length()}"
            f" ({100 * (worst + D.bit_length()) // worst / 100:.2f}× schema), merge {merge_ok}, holding {hold_ok}"
        )

    print("P4: sparse key sets, cheapest encoding (bits)")
    universe = odd_primes(U, start_after=V)
    for K in KS:
        pos = sorted(rng.sample(range(U), K))
        Dbits = prod(universe[i] for i in pos).bit_length()
        gaps = [pos[0] + 1] + [b - a for a, b in zip(pos, pos[1:])]
        gbits = sum(gamma_bits(g) for g in gaps)
        enc = {"D": Dbits, "gamma gaps": gbits, "bitmap": U}
        best = min(enc, key=enc.get)
        print(f"  K={K:>6}: D {Dbits:>7}, γ gaps {gbits:>7}, bitmap {U:>6}  → {best}")


if __name__ == "__main__":
    main()
