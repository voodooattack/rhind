# Cold review — exact-vsa paper (2026-10-03)

Two independent reviewers, neither with any context from the sessions that wrote the paper:

- **Referee**: read `main.typ` (current), the proofs, receipts and library; tried to break claims with exact-arithmetic scripts in `checks/` (run with `PYTHONPATH=../../src` from this folder).
- **Prior-art sweep**: web search; every citation below was verified to exist (Crossref / arXiv / opened page).

Spot-checked independently afterwards: the Prop. 2 counterexample (F = 5/11 + 5/13, R = {11}, x = 5 → den = 13, formula says 1) and the MAP two-step numbers (`checks/c05_out.txt`) both hold.

**Verdict: preprint after major fixes.** The fixes are mostly rewording, scoping and fair baselines — not new theory.

---

## A. Correctness — must fix

| # | Where | Problem | Fix |
|---|---|---|---|
| A1 | Prop. 2 (main.typ ~l.268) | False when a stored key outside the bag holds x: its term x/q stays (the −x/q is absent off R). | Condition the product on "q ∉ R or v_q ≠ x" and say "keys of R holding x", or assume Q ⊆ R. |
| A2 | Analogy text (~l.291) | Uses D_B / den(...) — the exact error the lcm paragraph above it warns about. B = {11:5, 13:7}, bag {11,13,17} → 11/17. Also undefined (returns None) when x occurs at ≥ 2 roles. | Use lcm(D_B, D_R); state "x occurs exactly once". |
| A3 | ~l.219 merge/conflict | gcd(D_A, D_B) > 1 means *share* a key, not *disagree*. A + A doubles values; values summing to q silently delete the key; delete needs the exact value. Proof 003 P3 "merge exact" tested full random records, so it verified per-key addition mod q — semantically meaningless there. | Say "share a key"; merge = per-key addition mod q, meaningful only for disjoint supports; delete = read-then-subtract; retest merge on disjoint supports. |
| A4 | ~l.323 ultrametric | Equality should be "at least min(i, j)"; depth isn't the metric, q^(−depth) is. | Reword. |
| A5 | "information floor" (abstract, Size §, conclusion, proof 001 P1) | K(⌈log₂U⌉+⌈log₂V⌉) is an ordered, rounded table, not the floor. True floor ⌈log₂(C(U,K)·(V−1)^K)⌉ gives 1.47× (K=10) … 2.31× (K=3000), growing with K; → ~2× when U ≫ V. 1.3× is specific to U=20000, V=1000. Conclusion's "at the floor itself" for schema mode contradicts the 1.01–1.20× receipts. | Rename to "packed-table size" or report both; give the general ratio; drop "at the floor itself". |
| A6 | Library | `143 in M` is True and `get(143)` returns 142 for M = {11:5, 13:7}; `1 in M` True; `holding(16)` reports 11 (x < keys not enforced). | Guard queries with is_prime and range checks; make "no false positives" conditional on dictionary primes. |

## B. Claims vs evidence — major

- **B1. Holistic-op MAP baselines are strawmen.** Exact memory does analogy in two steps (find role, read value); MAP was forced into the one-shot mapping vector. Given the same two-step procedure, MAP is 100/100 at m = 30 and m = 100 (n = 10⁴), where the paper reports 43 and 0. Agreeing *set* via per-role clean-up is also 100/100. → Report both procedures; state the honest difference (m clean-ups and large n vs one bignum op plus factoring).
- **B2. "Why not an ordinary data structure?" is unanswered.** A packed SWAR record (m fields of b bits + guard bit) does holding, agreeing and q-adic depth with a constant number of word ops, linear time, no gcd — and agrees with rhind on all tests, at fewer bits (1,100 vs 2,077 fraction / 1,038 schema at m = 100; 900 vs 2,982 for depth). Sorted lists do merge/holding/agreeing by merge-join. → Add a classical-baselines table (packed record, sorted list/hash map, IBLT). State where the fraction form actually wins, e.g. self-describing sparse key sets over a huge universe, coordination-free commutative merge, one integer in transit; or make it an explicit non-claim.
- **B3. "One subtraction" hides a bignum gcd.** Quadratic in CPython. At K = 64,000: get ≈ 0.9 ms, but holding ≈ 1.9 s against ≈ 1.4 ms for a dict scan, and build ≈ 24 s (K big divisions). → State the cost per operation; use a product tree in `build`; scope Limitations' "linear" to `get` only.
- **B4. "VSA interface" is overstated.** No vectors; no general binding (a prime product is composite and breaks the memory); no nesting (values must be below every key); no permutation, so no sequences. → Retitle (e.g. "…with VSA-style holistic queries") and add a Limitations bullet.
- **B5. "No noise tolerance, absent by construction" is wrong structurally.** Redundant residue number systems and Chinese-remaindering-with-errors (Goldreich–Ron–Sudan) add noise tolerance to exactly this representation. That also undoes the "opposite corners" framing.

## C. Minor

- C1. "Predictions written before the first run": the proofs were promoted from explorations that measured them, so these are thresholds from pilots. Say so. Consider "executable experiments" over "proofs" in the paper's own wording.
- C2. The equal-bits MAP comparison is expected to fail by capacity theory. The counter width charges the worst case (≈ 25–30% fewer dimensions than needed). The n/2 threshold isn't calibrated. "Fastest to query" compares against VSA clean-up, not a dict.
- C3. Graded-nearness cost unreported: 2,982 bits for 800 bits of information (3.7×), and one gcd per key.
- C4. Sparse-set table: the enumerative bound ⌈log₂C(U,K)⌉ beats D at every K, including K = 10 (122 vs 156). "D wins at 10 keys" is an artefact of Elias-γ.
- C5. Deng–Raviv: holds, except K = 300 becomes 874× with ternary N = 3⁶ under their subcode convention. "Binary cheapest at every load" depends on the convention; footnote it.
- C6. Prop. 3: define "holistic" as "no ℤ-module operation". The 2,070-pair exhaustive check adds nothing, so drop or footnote it. Practical force is small, since read-then-write is cheap.
- C7. Presentation:
  - Propositions appear in the order 1, 2, 4, 3.
  - Symbol clashes: N, m and k each have more than one meaning.
  - "—" table cells are unexplained.
  - The PDF date shows 1980-01-01 (reproducible build); hard-code it.
  - No repository URL; `proofreport` isn't shipped, so nothing reruns.
  - 004 P5 and 005 P1 are by-construction facts; make them remarks.
  - Global filler numbering inflates the exact bits in the holistic experiment.

## D. Prior art

**Must cite.** These overlap schema mode and the "Relation to the secure lock" paragraph directly. The paper credits a later, less close source.
- Davida, Wells, Kam. "A database encryption system with subkeys." ACM TODS 6(2):312–328, 1981. doi:10.1145/319566.319580. A record stored as one CRT integer, field i read as C mod dᵢ. This is schema mode, 8 years before Chiou–Chen.
- Chang, C. C. "The study of an ordered minimal perfect hashing scheme." CACM 27(4):384–387, 1984. doi:10.1145/358027.358051. Prime-keyed key→value lookup in one CRT integer. (Optional: Jaeschke, "Reciprocal hashing," CACM 24(12), 1981.)
- Chang, C. C. "On the design of a Key-Lock-Pair mechanism in information protection systems." BIT 26(4):410–417, 1986. doi:10.1007/BF01935048.
- Wu, Lee, Hsu. "A Prime Number Labeling Scheme for Dynamic Ordered XML Trees." ICDE 2004. Prime labels with divisibility for ancestry, plus a CRT table for order. Bears on §5.7.

**Should cite.**
- Goodrich & Mitzenmacher, "Invertible Bloom Lookup Tables," Allerton 2011 (arXiv:1101.2245). Eppstein, Goodrich, Uyeda, Varghese, "What's the difference?", SIGCOMM 2011. Exact superposed key–value structures with + and − for insert, delete and difference: the obvious sibling.
- Power-sum / Reed–Solomon syndrome sketches. RRNS (Mandelbaum 1972/76). Goldreich–Ron–Sudan (STOC 1999 / IEEE TIT 2000). Guruswami–Sahai–Sudan 2000. Boneh 2000.
- Prüfer decomposition ℚ/ℤ ≅ ⊕ℤ(p^∞) (Fuchs, *Infinite Abelian Groups*). Props 1, 3 and 4 are this decomposition; saying so pre-empts "textbook".
- Preuveneers & Berbers, IEEE Intelligent Systems 23(2), 2008. Prime-product ontology subsumption; the "prime-product sets are classical" line needs a citation.
- Snaider & Franklin, "Modular Composite Representation," Cogn. Comput. 6(3), 2014. Angioli et al., arXiv:2511.09708. The FHRR-on-4th-roots baseline is MCR with r = 4.
- Gayler 2003 (arXiv:cs/0412059) for MAP/VSA; Plate for FHRR.
- Capacity: Clarkson–Ubaru–Yang (JAIR 2026, arXiv:2301.10352); Thomas–Dasgupta–Rosing (JAIR 2021).
- Frady et al. resonator networks (2020). Kleyko et al., Neural Comput. 35(7), 2023. Raviv, arXiv:2403.03278.
- Nickel & Kiela, Poincaré embeddings (2017), for the out-of-scope geometric nearness.
- Optional: Glashoff 2010 (Leibniz characteristic numbers); Tropashko 2005 / Hazel 2008 (rational encodings of hierarchies); Murtagh 2004.
- Cosmetic: the bib key `kymn2023residue` points to a 2025 entry.

**What survived as novel (prior-art reviewer's assessment):**
- The fraction form, where carrying D gives absence detection and merge-by-addition.
- Treating it explicitly as a VSA.
- Holistic queries by "subtract once, read the denominator".
- The re-binding impossibility.
- q-adic graded nearness inside a superposed memory.
- The equal-storage comparisons.

"Genuine if modest." "What is new is narrow" is accurate.

## E. Keep

- The candid secure-lock positioning and "What is new is narrow" (expand them with section D).
- "Why primes" with its counterexamples, and the prime-powers remark.
- The honest note on the lcm bug.
- The Deng–Raviv comparison: favourable to them and correctly modelled.
- The FHRR variance argument with an exact Gaussian-integer implementation.
- Numbers generated from data.
- Schema mode plus the sparse-set table as a self-limiting result.
- The bag-versus-tree separation (concepts as keys, hierarchies as digits): the cleanest idea in the second half.
