"""
036 — Exact associative memory: does "algebra + exactness" buy anything that
a noisy VSA or a plain dictionary cannot?

Record carried over from banana-lab (where the work began); proof and
library names are updated, the reasoning and results are as written then.

NAMING (2026-10-02): "MAP-B" in this record is MAP-I in Schlegel et al.'s
taxonomy (bipolar atoms, integer bundles, no thresholding). Current proofs
(001, 002) use MAP-I; this record keeps its original wording.

PROMOTED 2026-10-02 → proofs/001 (claims) and rhind.memory
(library, tests/vsa/test_memory.py). Kept here as the original exploration record.

Task: K facts key → value superposed into ONE stored object; recall the value
of a present key, report absent keys as absent; support merge and delete.
Universe: 20,000 keys, 1,000 values, assignments random (seeded).

Contenders (all exact integer arithmetic; numpy only as an int64 array engine):
  OURS   memory = Σ v/q = N/D, q = the key's dictionary prime (primes above
         the value range, so every value fits below its key). Recall:
         v = N·(D/q)⁻¹ mod q. Absent: q ∤ D. Merge = add, delete = subtract.
         Bits: bit_length(N) + bit_length(D).
  MAP-B  bipolar VSA (Gayler's multiply–add–permute): random ±1 vectors, bind
         = elementwise product, bundle = integer sum, recall = key ⊙ memory,
         then clean-up by integer dot product against the 1,000 value vectors;
         reported "present" only if the best score ≥ n/2. Two sizes: n matched
         to OURS' bits (n · bits per counter = OURS' bits), and n = 10,000.
  DICT   an ideal packed table: K · (⌈log₂ 20000⌉ + ⌈log₂ 1000⌉) bits. The
         information floor for an exact store of these facts.

Measured per K ∈ {10, 30, 100, 300, 1000, 3000, 10000}: recall on up to 500
present keys, false recalls on 500 absent keys, bits, mean query time; and
for OURS a random sequence of 2,000 inserts / deletes / merges checked
against a memory rebuilt from scratch.

Predictions, on record BEFORE the first run:
  P1  OURS: recall 100% and false recalls 0 at every K; bits 1.2–1.6× DICT
      (it stores N as well as D, each ~ Σ log₂ q).
  P2  MAP-B at OURS' bit budget: accuracy falls below 50% from K ≈ 30
      (capacity ~ n/14 needs n ≫ what those bits buy). At n = 10,000: ~100%
      up to K ≈ 500, degrading beyond; false recalls nonzero once K is large.
  P3  Query time: OURS grows linearly with K (each recall is a big-int mod over
      the whole memory) and is slower than MAP-B's clean-up from roughly
      K = 3,000; DICT is O(1).
  P4  OURS stays exact under any sequence of insert / delete / merge.
  Expected overall reading: OURS is an exact dictionary with an arithmetic
  interface, about DICT's size, and no capability a dictionary lacks. The
  open question is whether any operation is uniquely cheap in it.

Results (2026-10-02, ~3 min; artifact 036_exact_associative_memory.json).
Recall = present keys answered correctly; false = absent keys answered.

      K   OURS recall/false  bits      query  | DICT    | MAP-B bit-matched     | MAP-B n=10,000
     10   10/10    0/500       299     1 µs   |    250  | 1/10    500/500  37 µs | 10/10    0/500   7 ms
    100   100/100  0/500     3,181     1 µs   |  2,500  | 10/100  500/500       | 100/100  0/500   7 ms
    300   300/300  0/500     9,740     2 µs   |  7,500  | 31/300  500/500       | 293/300 420/500  7 ms
  1,000   500/500  0/500    32,546     6 µs   | 25,000  | 43/500  500/500  2 ms | 241/500 500/500  7 ms
  3,000   500/500  0/500    97,401    18 µs   | 75,000  | 32/500  500/500  5 ms | 40/500  500/500  7 ms
 10,000   500/500  0/500   324,958    62 µs   |250,000  | 20/500  500/500 15 ms | (not run)

  P1 HELD: OURS recalled every present key and no absent key at every K, at
     1.20–1.30× the ideal packed table.
  P2 HELD, and worse for MAP than predicted: at OURS' bit budget MAP-B fails
     from K = 10 (1/10), not 30. At n = 10,000 (≈ 50–90 kbit) it is perfect to
     K = 100, starts false recalls by K = 300, and collapses by K = 1,000. (The
     n/2 presence threshold is crude, but recall itself also collapses.)
  P3 FAILED: OURS is the FASTEST to query: 62 µs at K = 10,000 against 7–15 ms
     for MAP-B's clean-up (n × 1,000 dot products). Big-int mod over the whole
     memory is linear in K but runs in C. DICT is O(1) and was not timed.
  P4 HELD: 2,000 random inserts / deletes / merges, then the memory equals
     one rebuilt from scratch, and all 2,302 facts recall.
Reading: as an exact VSA, this dominates a standard noisy VSA (MAP-B) at
every size and every bit budget: exact recall, no false recalls, smaller,
faster. Against a dictionary it is ~1.25× the information floor, with merge
and delete as + and −, and no capability a dictionary lacks. What noisy VSAs
keep and this does not: graceful degradation (one flipped bit here corrupts
recall, it doesn't add noise) and similarity between composite structures.

Usage: python exploration/036-exact-associative-memory.py
"""

import json
import random
import time
from fractions import Fraction
from math import prod
from pathlib import Path

import numpy as np

from rhind import PrimeDictionary

HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"
U, V = 20000, 1000
KS = (10, 30, 100, 300, 1000, 3000, 10000)


def now() -> int:
    return time.perf_counter_ns()


# ── OURS ──────────────────────────────────────────────────────────────────────


class ExactMemory:
    """Σ v/q (mod 1), held as one reduced Fraction N/D, D = ∏ keys present.

    Recall only reads N mod q, so the integer part is irrelevant and the memory
    lives in Q/Z. Merge and delete are + and − of Fractions; a key whose value
    becomes 0 mod q drops out of D by reduction, with no bookkeeping."""

    def __init__(self, F: Fraction = Fraction(0)):
        self.F = F - (F.numerator // F.denominator)

    @classmethod
    def build(cls, facts: dict) -> "ExactMemory":
        D = prod(facts) if facts else 1
        N = sum(v * (D // q) for q, v in facts.items())
        return cls(Fraction(N % D, D) if D > 1 else Fraction(0))

    def get(self, q: int):
        N, D = self.F.numerator, self.F.denominator
        if D % q:
            return None
        return N % q * pow((D // q) % q, -1, q) % q or None

    def merge(self, other: "ExactMemory") -> "ExactMemory":
        return ExactMemory(self.F + other.F)

    def delete(self, other: "ExactMemory") -> "ExactMemory":
        return ExactMemory(self.F - other.F)

    def bits(self) -> int:
        return self.F.numerator.bit_length() + self.F.denominator.bit_length()


# ── MAP-B ─────────────────────────────────────────────────────────────────────


def map_run(facts_idx, absent_idx, n, rng_np, values_mat_cache={}):
    """facts_idx: [(key_index, value)]; returns recall, false recalls, bits, query ns."""
    used = sorted(
        {k for k, _ in facts_idx} | set(absent_idx)
    )  # only the keys this run touches
    row_of = {k: i for i, k in enumerate(used)}
    rows = rng_np.choice(np.array([-1, 1], dtype=np.int8), size=(len(used), n))
    key_vecs = {k: rows[row_of[k]] for k in used}
    val_vecs = rng_np.choice(np.array([-1, 1], dtype=np.int8), size=(V, n))
    mem = np.zeros(n, dtype=np.int64)
    for k, v in facts_idx:
        mem += key_vecs[k].astype(np.int64) * val_vecs[v]
    span = int(np.abs(mem).max()) if len(facts_idx) else 0
    bits_per = (2 * span + 1).bit_length()
    vv = val_vecs.astype(np.int64)

    def query(k):
        scores = vv @ (key_vecs[k].astype(np.int64) * mem)
        best = int(scores.argmax())
        return best if scores[best] * 2 >= n else None

    probe = facts_idx[:500]
    t0 = now()
    ok = sum(query(k) == v for k, v in probe)
    t = (now() - t0) // max(1, len(probe))
    false = sum(query(k) is not None for k in absent_idx)
    return {
        "recall": f"{ok}/{len(probe)}",
        "false_recalls": f"{false}/{len(absent_idx)}",
        "bits": n * bits_per,
        "query_us": t // 1000,
    }


def main() -> None:
    rng = random.Random(36)
    rng_np = np.random.default_rng(36)
    dic = PrimeDictionary(range(U), start_after=V)  # every key prime > every value
    dict_bits_per = (U - 1).bit_length() + (V - 1).bit_length()
    out = {"universe keys": U, "values": V, "rows": []}

    for K in KS:
        keys = rng.sample(range(U), K)
        absent = rng.sample([k for k in range(U) if k not in set(keys)], 500)
        facts_idx = [(k, rng.randrange(1, V)) for k in keys]
        facts = {dic.prime[k]: v for k, v in facts_idx}

        t0 = now()
        mem = ExactMemory.build(facts)
        build_ms = (now() - t0) // 10**6
        probe = facts_idx[:500]
        t0 = now()
        ok = sum(mem.get(dic.prime[k]) == v for k, v in probe)
        q_ns = (now() - t0) // len(probe)
        false = sum(mem.get(dic.prime[k]) is not None for k in absent)
        ours = {
            "recall": f"{ok}/{len(probe)}",
            "false_recalls": f"{false}/500",
            "bits": mem.bits(),
            "query_us": q_ns // 1000,
            "build_ms": build_ms,
        }

        n_match = max(8, mem.bits() // max(1, (2 * K + 1).bit_length()))
        row = {
            "K": K,
            "ours": ours,
            "dict_bits": K * dict_bits_per,
            "map_matched": dict(map_run(facts_idx, absent, n_match, rng_np), n=n_match),
        }
        if K <= 3000:
            row["map_10000"] = map_run(facts_idx, absent, 10000, rng_np)
        out["rows"].append(row)
        print(json.dumps(row), flush=True)

    # P4: exactness under a random operation sequence (OURS)
    truth, mem = {}, ExactMemory()
    for step in range(2000):
        op = rng.random()
        if op < 0.5 or not truth:  # insert a new fact
            q = rng.choice(dic.primes)
            if q in truth:
                continue
            v = rng.randrange(1, V)
            truth[q] = v
            mem = mem.merge(ExactMemory.build({q: v}))
        elif op < 0.8:  # delete an existing fact
            q = rng.choice(sorted(truth))
            mem = mem.delete(ExactMemory.build({q: truth.pop(q)}))
        else:  # merge a batch of new facts
            batch = {}
            for q in rng.sample(dic.primes, 5):
                if q not in truth:
                    batch[q] = rng.randrange(1, V)
            truth.update(batch)
            mem = mem.merge(ExactMemory.build(batch))
    rebuilt = ExactMemory.build(truth)
    out["P4 ops"] = 2000
    out["P4 final memory equals rebuild"] = mem.F == rebuilt.F
    out["P4 every fact recalls"] = all(mem.get(q) == v for q, v in truth.items())
    out["P4 facts at end"] = len(truth)
    print("P4", out["P4 final memory equals rebuild"], len(truth), flush=True)
    (ART / "036_exact_associative_memory.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
