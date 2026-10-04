# Second cold review — narrowed paper (2026-10-04)

One fresh reviewer, with no access to the first review. It read the narrowed paper, the proofs, the receipts and the library. Check scripts are in `checks/`; run them with `PYTHONPATH=../../src` from this folder. Items 5 and 12 were spot-checked independently.

**Verdict: ready to post after a focused revision.** Items 1–5 must be fixed first. All of them are text changes; no proof needs re-running.

**What passed:**
- Every number in the prose matches the data JSON.
- Props 1–3 hold, with 0 mismatches over 3,000 randomised trials (edge cases included).
- 121/256 is exact.
- The FHRR variance argument is correct.
- Table 3 reproduces.
- The enumerative-code claim holds.

## Must fix

1. **Re-binding boundary overstated** (§4.2, abstract, contributions, conclusion). Prop. 4 is true. But "exactness and holistic transport cannot be had together" and "the shared group … makes it noisy" are false in general:
   - a packed record, (ℤ/2^w)^m, is exact and moves fields additively (checked in 20,000 trials);
   - orthonormal-key linear memories (TPR) are exact and re-bind linearly;
   - noise comes from quasi-orthogonal codes with fewer dimensions than atoms, not from the shared group.

   The real trade-off is narrower. Reading the key set from the denominator needs components of coprime order. Additive transport needs a nonzero Hom between components. In this memory you can't have both. Also, the paper defines "holistic" as additive, but its own den(·) queries are not additive. Pick one definition and apply it everywhere. Call Prop. 4 a lemma or observation.
2. **Novelty against the packed record.** The packed record does holding and agreeing with a constant number of word operations, and graded depth too (XOR, then count trailing zero groups per field; not measured). So "holistic queries and graded nearness as arithmetic" is not what the fraction adds. What it adds uniquely:
   - a self-describing, open or sparse key set (the denominator);
   - absence without a schema;
   - merge by addition across arbitrary key sets.

   "One subtraction gives every depth" also hides an m-fold readout. Narrow the abstract and contributions accordingly. Add a packed graded-nearness baseline, or concede in the text that it would win. Cite Lamport 1975 (CACM, multiple byte processing with full-word instructions) and Knuth TAOCP 4A (broadword computing).
3. **Missing prior art: exact superposed memories with orthonormal keys.** Smolensky 1990, tensor product representations (Artificial Intelligence 46); Kohonen 1972, correlation matrix memories (IEEE Trans. Computers); Anderson 1972 (Mathematical Biosciences). Also worth adding: Kleyko et al. 2023 (Neural Computation, decoding compositional structure) and Frady–Kleyko–Sommer 2022 (sparse block codes, IEEE TNNLS).
4. **Abstract overclaim.** It says MAP-I "matches every exact holistic answer". Graded-depth MAP is 98% / 81%, and holding was never run on MAP. Change to "every analogy and agreeing-set answer (Table 4)".
5. **"Why primes" is wrong.** Pairwise-coprime composite keys ARE closed under addition: ⊕ℤ/mᵢ embeds in ℚ/ℤ, and per-key reads by gcd work (0 mismatches in 20,000 trials). 4/15 + 1/15 still reads back 5 at key 15. What primes actually buy is that every nonzero value is a unit, so D is exactly the product of the present keys, and lcm/den is a product of keys. What breaks a memory is keys that share a factor. Binding p and q into pq fails for the same reason: pq shares factors with p and q.

## Minor

6. **Abstract cost sentence.**
   - The 1,113 vs 234,831 ns figures are packed vs fraction; the hash map is 17,896 ns.
   - "In fewer bits" is false against schema N at m = 10 and 100.
   - "Value query" should read "which roles hold x".
   - "In any setting" needs the same qualification.
7. **Table 10 caption.** "Undefined on N" is wrong: schema mode rebuilds F and then costs the same as the fraction. Say it wasn't timed.
8. **Graded mode.**
   - Absence is unreadable: value 0 looks the same as empty, and a value divisible by q lowers the exponent. The text should say so.
   - Tables 7 and 8 count N bits only; label them.
   - Base-q digits holding base-4 choices waste bits (≈ 36 bits per role for 8 bits of information; a packed record would use ≈ 800 bits against 2,982 at m = 100). So "a tenth of MAP's bits" is measured against an inefficient code.
9. **Equal-bits baselines** use the worst-case counter width, so they get only 69–87% of the exact memory's bits. Say "at most the same bits", or use the realised width.
10. **Deng–Raviv.** The N ≤ 2^14 cap never binds, so it is neutral rather than favourable to them. Cite their eq. (10).
11. **FHRR wording.** "The strongest dense VSA" should become "a strong dense VSA". The MCR identification needs a qualifier: MCR quantises its bundle to ℤ/r (reviewer's confidence: moderate).
12. **Library bug: `is_prime`.** The claimed bound (3.3·10²⁴) is wrong. ψ₁₂ = 318665857834031151167461 = 399165290221 × 798330580441 passes, which gives a false positive in a memory. Fix: add base 41, which makes it exact below 3.317·10²⁴. Confirmed independently.
13. **Library: `project()`** accepts composite or duplicate keys and produces an invalid memory.
14. **001/P4** runs one sequence (singular), and its merges never share keys.
15. **Recall cost wording** is inconsistent (one inversion vs one multiplication); it also needs (D/q) mod q.
16. **Ultrametric:** define d = 0 for equal values. 17. **Notation:** R is used twice, and "den" is never defined.
18. **Repo tone and reproducibility.**
   - Ship `proofreport`, or the reproducibility paragraph can't be honoured.
   - Proof titles and reports overclaim (001 "beats … at every size and budget"; reports say they "certify all claims").
   - Docstrings use private jargon (structural primes, banana-lab, exploration numbers).
19. **Asides.** The library-bug aside should become a footnote. Two-sided assertion windows on baselines (e.g. 004/P2 caps MAP at ≤ 90%) need justifying or removing.

## Keep
- The explicit non-claims and §5.8's negative result.
- The two-step MAP procedure and the admission about it.
- The set floor.
- The placement against CRT records and the primary decomposition.
- The lcm correction.
- 121/256 and the one-attribute-per-key resolution.
- Data-driven numbers and recorded prediction revisions.
