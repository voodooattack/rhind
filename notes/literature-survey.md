# Exact VSA: literature survey (2026-10-02)

Carried over from banana-lab, where the work began. Proof numbers are
rhind's (001 = exact memory, 002 = holistic operations); explorations 036,
037 and 040 are in `explorations/`.

Naming: our bipolar baseline sums bundles as integers, which is MAP-I in
Schlegel et al.'s taxonomy (MAP-B would threshold the bundle back to ±1).
It was called MAP-B in explorations 036, 037 and the first versions of 001/002, and is
renamed MAP-I everywhere current.

Scope: where proofs 001–002 and `rhind.memory.ExactMemory` sit
against published work. Each claim gets one of three verdicts:

- **known**: the same object and result are published;
- **known in a different form**: the mathematics is published under another
  framing, and our contribution is the framing or the interface;
- **apparently new**: no prior art found in this survey. That is a statement
  about this search, not a proof of novelty.

## 1. The memory itself (proof 001)

Claim: `F = Σ v/q mod 1` stores a key→value map exactly; recall is
`N·(D/q)⁻¹ mod q`; an absent key is detected by `q ∤ D`.

**Verdict: known in a different form.**

Why: the numerator satisfies `N ≡ v·(D/q) (mod q)` for every stored q. So N is
a CRT solution of the system `X ≡ v·(D/q) (mod q)`, which is the
*secure-lock / CRT broadcast* construction up to a fixed unit per slot. That
construction is old:

- Chiou & Chen (1989), "secure lock" for broadcast;
- Intel patent US5712800 (1997), broadcast key distribution. One integer X with
  `X ≡ K'(i) mod p(i)`, and receiver i reads `X mod p(i)`;
- a long line of CRT group-key-management papers since.

Partial fractions ↔ CRT is textbook (the same isomorphism, ℚ/ℤ split over
prime denominators).

What the fraction form adds over the integer CRT form, and does not appear in
that literature as far as this search found:

- **The denominator carries the key set.** `D` is the product of stored keys,
  so membership is divisibility and absent keys are *detected*. The
  broadcast schemes want the opposite: a non-member gets garbage it cannot
  distinguish from a value.
- **Merge and delete are + and − on the rationals.** A CRT integer is only
  defined mod its own modulus, so merging two of them needs a CRT step. The
  fraction is self-describing, so the + is the whole operation.

Prime-product sets (membership by divisibility, ∪/∩ by lcm/gcd) are the
Gödel-numbering trick and are folklore.

## 2. Exact vs noisy VSAs (proof 001's comparison)

Claim: an exact VSA dominates MAP-I at every bit budget tested.

**Verdict: the result is correct, but the baseline is the weakest one available.**

The relevant prior art:

- **Residue Hyperdimensional Computing.** Kymn, Kleyko, Frady, Bybee, Kanerva,
  Sommer and Olshausen, "Computing With Residue Numbers in High-Dimensional
  Representation", *Neural Computation* 37(1):1–37 (2025), arXiv 2311.04872.
  - Integers are encoded as phasor vectors, one root-of-unity frequency per
    modulus, combined by Hadamard product.
  - + and × on the codes are exact.
  - Similarity and decoding are not: decoding is a resonator network with a
    capacity limit.
  - It encodes *numbers*, not key→value memories. Same CRT idea, different
    object.
- **Hanley, Tomkins-Flanagan & Kelly**, "Hey Pentti, We Did (More of) It!: A
  Vector-Symbolic Lisp With Residue Arithmetic" (arXiv 2511.08767, Nov 2025). It
  builds structures on top of RHC/FHRR. Still a high-dimensional, noisy
  representation.
- **Deng & Raviv**, "Efficient Vector Symbolic Architectures from Histogram
  Recovery" (arXiv 2511.01838, revised Apr 2026).
  - Concatenated Reed–Solomon + Hadamard codes give quasi-orthogonal codewords.
  - Recovery of a superposition is a list-decoding ("histogram recovery")
    problem with a formal guarantee, up to a bound on how many items are
    superposed.
  - This is the closest "exact VSA" in the literature.
  - The trade is the mirror image of ours. They have bounded capacity and
    tolerate noise. We have unbounded capacity and tolerate zero noise:
    one flipped bit of F corrupts everything.
- **Thaine & Penn**, EACL 2021. They pack an embedding vector into one integer
  by CRT, with exact recovery. A numeric vector, not a memory.

The baselines used by the field are surveyed by Kleyko et al. (ACM CSUR 2022,
parts I/II) and Schlegel et al. (2022). They are MAP-B/C/I, BSC, HRR, FHRR,
VTB, MBAT and sparse block codes, with capacity theory from Frady, Kleyko &
Sommer (2018).

Consequence for 001, and the follow-up (2026-10-02): 001 now runs FHRR on
the same facts (P5–P6). Phases are the 4th roots of unity, so the arithmetic
is exact Gaussian integers. That costs nothing: the real part of a uniform
phase has variance 1/2 for any m ≥ 3 and for the continuous circle alike.
Predictions made before the run all held:

- **At matched bits, FHRR equals MAP-I almost row for row** (e.g. 29/300 vs
  30/300 at K = 300). Half the dimensions, each twice as clean, nets zero per
  bit. So MAP-I was not a strawman: per bit, the strongest dense VSA is no
  better.
- **At n = 10,000, FHRR holds about twice the facts MAP-I does.** It recalls
  259/300 at K = 1,000 (MAP-I 123/300), and drops to 91/300 at K = 3,000.

The Deng & Raviv comparison is exploration 040. It takes their formula
(10) in its noiseless best case, u ≤ ⌊(N−1)/(K−1)⌋, and charges their
bundle only its information content. Their vectors have n = N² entries with
N ≳ (facts)·(K−1), so bits grow ~ K² log K. Ours grow ~ 32·K. In the same
universe as 001 they need 50× our bits at 10 facts and 8,265× at 3,000.

What their premium buys is noise tolerance, which we do not have. So the
fair statement is that these are two exact designs at opposite corners:
information-floor and fragile, or noise-tolerant at a quadratic cost.

## 3. Holistic operations (proof 002)

Claims:

- `holding(x) = D / den(F − x·S)` returns every key whose value is x, in one
  subtraction;
- analogy ("dollar of Mexico") is exact;
- `agreeing = lcm / den(F_A − F_B)`.

**Verdict for the operations: apparently new as constructions.**

The mechanism is that subtracting x·S zeroes exactly the terms with `v = x`,
and zeroed terms drop out of the denominator. Neither the CRT broadcast nor
the VSA literature found here uses the denominator drop as a query. That
said, the trick is a few lines long, and a number theorist would call it
obvious once it is stated. "New" here means "unpublished as far as we found",
not "deep".

**Verdict for exact analogy: known in a different form.**

Kanerva (2010) poses the task holistically and solves it approximately.
Plate's HRR and the surveys treat analogy as approximate clean-up. Exactness
itself is not new: any dictionary with a reverse index answers the question
exactly. What is ours is that the answer comes from the same arithmetic
object, with no reverse index stored.

## 4. Re-binding impossibility (proof 002, P5)

Claim: Hom(ℤ/p, ℤ/q) = 0 for distinct primes, so any exact re-binding must
read the value.

**Verdict: known.**

The homomorphism fact is textbook. Noisy VSAs also re-bind by unbind-then-bind,
which reads the value. The useful thing 002 records is that the reading is
*forced*, not an implementation choice. That is worth keeping as a remark,
not as a result.

## 5. Set reconciliation (a rejected direction)

Tested in a banana-lab exploration (not carried over) and rejected, correctly.

- Minsky, Trachtenberg & Zippel (IEEE Trans. IT 2003) already do this
  optimally by characteristic-polynomial interpolation.
- Our `S = Σ 1/q` is the integer analogue of the logarithmic derivative
  `χ'/χ = Σ 1/(z − a)` of their characteristic polynomial. Our tie at
  744 vs 737 bits is what that analogy predicts.

## Summary

| Claim | Verdict |
|---|---|
| Memory storage and recall (001) | known in a different form (CRT secure lock) |
| Absent-key detection, merge/delete as ± | apparently new framing of known math |
| Beats MAP-I (001) | holds; FHRR no better per bit (001); Deng–Raviv 50–8,265× our bits, but noise-tolerant (040) |
| holding / agreeing via denominator drop (002) | apparently new, shallow |
| Exact analogy (002) | known in a different form (dictionary + reverse index) |
| Re-binding must read (002) | known (textbook Hom) |
| Set sync | known (CPI); we tie it |

Bottom line: the lab has an exact, self-describing CRT dictionary whose VSA
operations are rational arithmetic. The algebra is old. The interface,
meaning denominator-as-key-set and the holistic queries via the denominator
drop, is the unpublished part. A paper-shaped claim would be "exact VSA
semantics for free from partial fractions", benchmarked against MAP-I and
FHRR (proof 001) and Deng & Raviv (exploration 040).

## Sources

- [Kymn et al., Residue Hyperdimensional Computing (arXiv 2311.04872)](https://arxiv.org/abs/2311.04872)
- [A Vector-Symbolic Lisp with residue arithmetic (arXiv 2511.08767)](https://arxiv.org/abs/2511.08767)
- [Deng & Raviv, Efficient VSAs from Histogram Recovery (arXiv 2511.01838)](https://arxiv.org/abs/2511.01838)
- Thaine & Penn, "The Chinese Remainder Theorem for Compact, Task-Precise, Efficient and Secure Word Embeddings", EACL 2021 (link not verified)
- [US5712800, Broadcast key distribution using CRT](https://patents.google.com/patent/US5712800)
- [CRT-based group key management (ACM SE 2007)](https://dl.acm.org/doi/10.1145/1233341.1233389)
- [Kanerva 2010, "What's the Dollar of Mexico?"](https://redwood.berkeley.edu/wp-content/uploads/2020/05/kanerva2010what.pdf)
- [Kleyko et al., HDC/VSA survey part II (ACM CSUR)](https://dl.acm.org/doi/10.1145/3558000)
- [Schlegel et al., A comparison of VSAs](https://link.springer.com/article/10.1007/s10462-021-10110-3)
- [Minsky, Trachtenberg & Zippel, set reconciliation (ADS)](https://ui.adsabs.harvard.edu/abs/2003ITIT...49.2213M/abstract)
