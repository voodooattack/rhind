# rhind

[![DOI](https://zenodo.org/badge/1402661301.svg)](https://doi.org/10.5281/zenodo.23132905)

An exact superposed key–value memory in one rational, and its
self-describing key set.

A vector symbolic architecture (VSA) stores key → value facts by
superposing vectors, and pays for that with noise. `rhind` superposes facts
exactly, in one reduced fraction:

    F = Σ v_q / q  (mod 1)  =  N / D

Keys are distinct primes q, and a value is a residue 1 ≤ v < q.

- **Recall** reads v = N · (D/q)⁻¹ mod q.
- **Absence** is q ∤ D: there are no false recalls for prime queries.
- **Merge and delete** are + and −. Values at a shared key add mod q.
- **The key set describes itself.** D is exactly the product of the keys
  present. A memory over an open or sparse set of keys therefore detects
  absence without a schema, and merges with any other memory by addition.
- **Holistic queries** read the denominator: which roles hold a value,
  analogy, the roles on which two records agree, and, with prime-power
  keys, every role's depth of agreement.
- **No additive re-binding.** The coprime components that make D readable
  admit no additive map between them, since Hom(ℤ/p, ℤ/q) = 0. Moving a
  value means reading it out and writing it back.

```python
from rhind import ExactMemory

mem = ExactMemory.build({1009: 42, 1013: 7})   # key prime → value
mem.get(1009)     # 42
mem.get(1019)     # None: 1019 does not divide the denominator
mem.bits()        # size of N and D together
```

The library is pure Python with no dependencies; all arithmetic is exact
integer arithmetic.

## What it is not

It is not a faster or smaller data structure. On fixed records, a packed
record (one integer of fields, queried with word operations) is smaller,
and it and a hash map are faster at every operation measured (proof 006).
It is not a full VSA: it has no binding of atoms into new atoms, no
nesting and no sequences. It has no noise tolerance. Its integer form is
classical (CRT-encoded records, 1981). What the fraction adds is the
self-describing key set.

## Evidence

Claims are made by executable proofs. Each proof is a script whose
assertions encode its predictions. It writes a report and a data file only
if every assertion holds. Most thresholds were set after an exploratory
pilot. Where a prediction failed on the way, the docstring records the
original wording and the revision.

| proof | what it shows |
|---|---|
| `proofs/001_exact_memory_vs_noisy_vsa.py` | Exact recall at ≈ 1.3× an ordered packed table (1.5–2.3× the floor for an unordered set). At the same bits, MAP-I and FHRR fail. The exact VSA of Deng & Raviv needs 50–8,000× the bits, in exchange for noise tolerance. |
| `proofs/002_exact_holistic_operations.py` | Analogy, agreeing roles and re-binding are exact. MAP-I matches them at n = 10,000 when given the same two-step procedure, at 29–612× the bits. No additive map moves a value between keys. |
| `proofs/003_schema_mode.py` | With a fixed key set, store N alone: 1.01–1.20× the packed size, half the fraction form. |
| `proofs/004_graded_nearness.py` | Keys at q-adic precision: one subtraction yields every role's depth of agreement. |
| `proofs/005_concepts_and_hierarchies.py` | Concepts as keys, hierarchies as digits: shared concepts and shared ancestry together. |
| `proofs/006_classical_baselines.py` | Against a packed record and a hash map, no cost advantage anywhere measured. |

The paper in `papers/exact-vsa/` reads every table and quoted number from
those data files. Rerunning the proofs and recompiling regenerates it.

## Reproduce the paper

You need [devenv](https://devenv.sh) (Nix). From the repository root:

```sh
devenv shell
rhind_tests     # library tests (pytest)
rhind_proofs    # every proof → reports/ (reports + data files)
rhind_paper     # papers/exact-vsa/main.pdf (Typst)
```

The proofs refuse to write reports outside the devenv shell, so every
report is tied to a pinned environment. Proof 001 takes a couple of minutes;
the rest take seconds.

## Layout

```
src/rhind/          the library: memory, q-adic memory, prime dictionary, primes
src/proofreport/    proof harness (reports, hashes, data files)
proofs/             the proofs
reports/            their reports and data files
tests/              library tests
papers/exact-vsa/   the paper (Typst) and bibliography
notes/              literature survey; the two cold reviews and their checks
explorations/       the explorations the proofs were promoted from
.ledger/index.jsonl one line per commit: which proofs were re-run, and why
scripts/            the pre-commit hook that appends to the ledger
```

## Provenance and name

The work began in a private research repository (banana-lab) and was
extracted here, without history, once it was clear that the result does
not depend on anything else there. The explorations keep their original
numbers.

The name comes from the Rhind Mathematical Papyrus. Its 2/n table splits
fractions into sums of distinct unit fractions. The key bag Σ 1/q here is
such an Egyptian fraction, and recall is the scribes' problem in reverse:
recovering the parts from the whole.

## Cite

Archived on Zenodo: [doi:10.5281/zenodo.23132905](https://doi.org/10.5281/zenodo.23132905)
(this DOI always resolves to the latest version). See also `CITATION.cff`,
or the "Cite this repository" box on GitHub.

## Licence

Apache License 2.0 (see `LICENSE` and `NOTICE`).
