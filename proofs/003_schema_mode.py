"""
003 — Schema mode: with a predictable key set, store N alone

Promoted from exploration 041 (explorations/). Library: rhind.memory.

A memory is F = N/D with D = ∏ keys (proof 001 stores both). When the key
set is known from a rule, as for a record whose roles are always the first
m primes above the value range,
D can be recomputed and only N stored:

    encode  N = Σ v_q · (D/q)  mod D        (values 0 ≤ v < V < every q;
    decode  F = N/D,  v_q = get(q) or 0      0 = empty role)

This is the integer form, the Chinese-remainder secure lock. It gives up
reading absence from the memory itself (that moves to the schema); this
proof measures what it buys, and whether the operations survive.

Predictions, on record BEFORE running (exploration 041 measured them):
  P1  Round trip is exact for full records of m = 10, 100, 1,000 roles,
      values 0 ≤ v < 1,000, 200 records each.
  P2  N alone against the packed size m·⌈log₂ V⌉ bits: ≤ 1.02× at m = 10,
      ≤ 1.06× at m = 100, ≤ 1.25× at m = 1,000. Fraction mode (N and D)
      costs ≥ 1.95× schema mode at every m.
  P3  Merge of two records with disjoint supports (every role filled in at
      most one of them) is (N₁ + N₂) mod D and decodes to their union; the
      value query holding(x) on the rebuilt F is exact, empty roles included.
      (Revised 2026-10-03 after a cold review: the first version merged two
      full records, which only checks per-role addition mod q, a different
      modulus per role, and can leave the value range: not a meaningful merge.)
  P4  For sparse key sets (K keys of U = 20,000, by dictionary position) the
      cheapest key-set encoding among D, Elias-γ gaps of the positions and a
      U-bit bitmap is: D at K = 10; γ gaps at K = 100 … 3,000; the bitmap at
      K = 10,000.

Exact integers and Fractions throughout.
"""

import random
from fractions import Fraction
from math import prod

from proofreport import finding, proof_report, row, table, verified_section
from rhind import ExactMemory, odd_primes

SEED = 41
V = 1000
FLOOR_PER = (V - 1).bit_length()  # ⌈log₂ 1,000⌉ = 10
MS = (10, 100, 1000)
RECORDS = 200
U = 20000
KS = (10, 100, 300, 1000, 3000, 10000)


def _encode(values, keys, D):
    return sum(v * (D // q) for v, q in zip(values, keys)) % D


def _decode(N, keys, D):
    mem = ExactMemory(Fraction(N, D))
    return [mem.get(q) or 0 for q in keys]


def _gamma(g):
    return 2 * (g.bit_length() - 1) + 1


def _times(a, b):
    """a / b as a two-decimal string, by integer arithmetic (rounded down)."""
    h = 100 * a // b
    return f"{h // 100}.{h % 100:02d}×"


@proof_report(
    title="003 — Schema mode: with a predictable key set, store N alone",
    source=__file__,
)
def run():
    rng = random.Random(SEED)

    @verified_section("P1–P3 — full records: round trip, size, operations")
    @table(
        headers=[
            "m",
            "round_trip",
            "n_bits",
            "floor",
            "ratio",
            "frac_bits",
            "frac_ratio",
            "merge",
            "holding",
        ],
        labels=[
            "roles m",
            "round trip",
            "N bits (max)",
            "packed",
            "÷ packed",
            "fraction mode bits",
            "÷ schema",
            "merge (disjoint) exact",
            "holding exact",
        ],
        align=["r", "r", "r", "r", "r", "r", "r", "l", "l"],
        legend={
            "floor": "packed size m·⌈log₂ V⌉ bits, V = 1,000",
            "frac_bits": "N and D stored, as in proof 001",
            "holding": "every x = 1, 38, 75, …; records include empty roles",
        },
    )
    def _records():
        for m in MS:
            keys = odd_primes(m, start_after=V)
            D = prod(keys)
            bag = ExactMemory(Fraction(sum(D // q for q in keys), D))
            ok, worst = 0, 0
            for _ in range(RECORDS):
                vals = [rng.randrange(V) for _ in keys]
                N = _encode(vals, keys, D)
                ok += _decode(N, keys, D) == vals
                worst = max(worst, N.bit_length())
            assert ok == RECORDS  # P1
            floor = m * FLOOR_PER
            bound = {10: 102, 100: 106, 1000: 125}[m]
            assert 100 * worst <= bound * floor  # P2
            frac = worst + D.bit_length()
            assert 100 * frac >= 195 * worst  # P2
            a = [rng.randrange(V) for _ in keys]
            side = [rng.randrange(2) for _ in keys]  # disjoint supports
            a1 = [v if s else 0 for v, s in zip(a, side)]
            a2 = [0 if s else v for v, s in zip(a, side)]
            merged = _decode((_encode(a1, keys, D) + _encode(a2, keys, D)) % D, keys, D)
            merge_ok = merged == a
            mem = ExactMemory(Fraction(_encode(a, keys, D), D))
            hold_ok = all(
                mem.holding(x, bag) == prod(q for v, q in zip(a, keys) if v == x)
                for x in range(1, V, 37)
            )
            assert merge_ok and hold_ok  # P3
            yield row(
                m=m,
                round_trip=f"{ok}/{RECORDS}",
                n_bits=worst,
                floor=floor,
                ratio=_times(worst, floor),
                frac_bits=frac,
                frac_ratio=_times(frac, worst),
                merge="yes",
                holding="yes",
            )
        yield finding(
            "P1–P3",
            "with the key set known, N alone round-trips every record at 1.01× "
            "the packed size m·⌈log₂ V⌉ for 10 roles and 1.20× for 1,000, half of "
            "fraction mode; merge of disjoint records and the value query survive",
        )

    @verified_section("P4 — sparse key sets: the cheapest encoding of the keys")
    @table(
        headers=["K", "d_bits", "gamma_bits", "bitmap_bits", "best"],
        labels=["keys K", "D", "γ gaps", "bitmap", "cheapest"],
        align=["r", "r", "r", "r", "l"],
        legend={
            "d_bits": "the product of the keys, as fraction mode stores it",
            "gamma_bits": "Elias-γ codes of the gaps between dictionary positions",
            "bitmap_bits": f"one presence bit per dictionary entry (U = {U:,})",
        },
    )
    def _sparse():
        universe = odd_primes(U, start_after=V)
        expected = {
            10: "D",
            100: "γ gaps",
            300: "γ gaps",
            1000: "γ gaps",
            3000: "γ gaps",
            10000: "bitmap",
        }
        for K in KS:
            pos = sorted(rng.sample(range(U), K))
            d_bits = prod(universe[i] for i in pos).bit_length()
            gaps = [pos[0] + 1] + [b - a for a, b in zip(pos, pos[1:])]
            g_bits = sum(_gamma(g) for g in gaps)
            enc = {"D": d_bits, "γ gaps": g_bits, "bitmap": U}
            best = min(enc, key=enc.get)
            assert best == expected[K]  # P4
            yield row(K=K, d_bits=d_bits, gamma_bits=g_bits, bitmap_bits=U, best=best)
        yield finding(
            "P4",
            "D is the cheapest key-set encoding only for very sparse memories "
            "(10 keys of 20,000); a gap code wins from about 100 keys, a bitmap "
            "when nearly half the dictionary is present",
        )

    _records()
    _sparse()


if __name__ == "__main__":
    run()
