# rhind

Exact vector-symbolic memory from partial fractions.

A vector symbolic architecture (VSA) stores key → value facts by superposing
vectors, and pays for it with noise. `rhind` gives the same interface
exactly, with one reduced fraction:

    F = Σ v_q / q  (mod 1)  =  N / D

Keys are distinct primes q, and a value is a residue 1 ≤ v < q.

- **Recall** is one modular inversion: v = N · (D/q)⁻¹ mod q.
- **Absence** is q ∤ D, so there are no false recalls.
- **Merge and delete** are + and −.
- **Holistic queries** take one subtraction each, because the denominator *is* the key set. They cover every key holding a value, analogy, and the roles on which two records agree.
- **Re-binding** provably cannot be holistic: Hom(ℤ/p, ℤ/q) = 0.

```python
from rhind import ExactMemory

mem = ExactMemory.build({1009: 42, 1013: 7})   # key prime → value
mem.get(1009)     # 42
mem.get(1019)     # None: 1019 does not divide the denominator
mem.bits()        # size of N and D together
```

The library is pure Python with no dependencies; everything is exact
integer arithmetic.

## Evidence

The claims are made by executable proofs. Each proof is a script that
asserts predictions written down before its first run. It writes a report
(the receipt) and a data file only if every assertion holds.

| proof | claim |
|---|---|
| `proofs/001_exact_memory_vs_noisy_vsa.py` | Exact recall at ≈ 1.3× the information floor. At equal bits, MAP-I and FHRR both fail. The exact VSA of Deng & Raviv needs 50–8,000× the bits. |
| `proofs/002_exact_holistic_operations.py` | Value queries, analogy and role agreement are exact. Re-binding must read the value. |
| `proofs/003_schema_mode.py` | With a known key set, store N alone: 1.01× the floor for a 10-role record, half the fraction form. Merge and value queries survive. |

The paper draft in `papers/exact-vsa/` reads every table from those data
files, so rerunning the proofs and recompiling regenerates it.

## Reproduce

Inside the [devenv](https://devenv.sh) shell:

```sh
rhind_tests     # library tests
rhind_proofs    # all proofs → reports/ (receipts + data files)
rhind_paper     # papers/exact-vsa/main.pdf
```

## Layout

```
src/rhind/          the library: memory, prime dictionary, primes
src/proofreport/    proof-as-code machinery (reports, hashes, data files)
proofs/             the proofs
reports/            their receipts and data files
.ledger/index.jsonl one line per commit: which proofs were re-run, and why
scripts/            the pre-commit hook that appends to the ledger
tests/              library tests
papers/exact-vsa/   the paper (Typst)
notes/              literature survey with verdicts per claim
explorations/       the explorations the proofs were promoted from
```

## Provenance and name

The work began in a private research lab repository (banana-lab) and was
extracted here, history-free, once it was clear the result does not depend
on anything else there.

The name comes from the Rhind Mathematical Papyrus. Its 2/n table splits
fractions into sums of distinct unit fractions. The key bag Σ 1/q here is
such an Egyptian fraction, and recall is the scribes' problem in reverse:
recovering the parts from the whole.

## Licence

Apache License 2.0 (see `LICENSE` and `NOTICE`).
