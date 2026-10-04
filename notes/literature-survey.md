# Exact VSA: literature survey (2026-10-02, revised 2026-10-04)

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

## 6. Graded nearness (proofs 004, 005), added 2026-10-03

Claim: with keys at q-adic precision, one subtraction returns every key's
depth of agreement (shared trailing base-q digits); with concepts as keys
and hierarchies as digits, that covers shared concepts and shared ancestry
at once.

**Verdict for the ultrametric: known in a different form.** Encoding a
hierarchy as p-adic digit strings, with longest-common-prefix (Baire)
distance as the hierarchical metric, is established. Murtagh (2016) codes
clustering dendrograms this way and uses the p-adic norm as the sparsity
criterion; Martins (2025) builds classification, regression and
representation learning over ℚ_p, encoding Quillian semantic networks as
compact p-adic linear networks. Neither involves superposition, a
key–value memory or the CRT.

**Verdict for reading it inside a superposed memory: apparently new.**
The per-key depth comes from the exponent of each prime in one reduced
denominator, den(F − P), the same denominator-drop mechanism as the value
query of §3, extended from equality to graded agreement. As with §3, it is
short once stated.

**Concepts as keys with frequent concepts on small primes (005, P4): known
in a different form.** That frequent symbols should get the cheapest codes
is Huffman's principle (and the rearrangement inequality); banana-lab's
proof 128 used the same frequency order for gcd similarity.

## 7. After two cold reviews (2026-10-03, 2026-10-04)

Two independent reviews and a prior-art sweep changed several verdicts
above. Where this section and an earlier one disagree, this one is current.

**CRT records predate the secure lock.** Davida, Wells & Kam (ACM TODS
1981) store a database record as one integer and read field i as C mod dᵢ.
That is schema mode exactly. Chang uses one CRT integer as an ordered
minimal perfect hash (CACM 1984) and as a key–lock matrix (BIT 1986). Wu,
Lee & Hsu (ICDE 2004) label XML trees with primes and keep sibling order in
CRT integers. Garner (1959) is the residue number system itself. Verdict
for the memory's integer form: **known**.

**The structure is the primary decomposition of ℚ/ℤ** (Fuchs, *Infinite
Abelian Groups*). Proposition 1 and the re-binding observation are that
decomposition stated for this memory. Verdict: **known**.

**Holistic queries are not unique to the fraction.** A packed record
answers "which roles hold x" and "which roles agree" with a constant number
of whole-word operations (Lamport 1975; Knuth, TAOCP 4A), and graded depth
the same way. Proof 006 measured the first two: the packed record is
faster and smaller on fixed records. Verdict for "holistic queries as
arithmetic": **known in a different form**. It is not the contribution.

**Exact superposition is old.** Correlation-matrix memories (Kohonen 1972;
Anderson 1972) and tensor-product representations (Smolensky 1990) are
exact with orthonormal keys, at one dimension per key, and they re-bind
linearly. Invertible Bloom lookup tables (Goodrich & Mitzenmacher 2011;
Eppstein et al. 2011) superpose key–value pairs exactly with high
probability, with + and − for insert, delete and difference, more cheaply.

**Re-binding.** The old verdict, "known (textbook Hom)", stands for the
lemma, but the paper's first framing ("exactness and holistic transport
cannot coexist") was wrong. A packed record and an orthonormal linear
memory are exact and transport additively. The correct statement is a
trade-off of this design: the coprime components that make D readable
admit no additive map between them.

**Why primes.** Pairwise-coprime composite keys are also closed under
addition and readable per key. What primes buy is that D is exactly the
product of the keys present.

**What remains apparently new** is the reduced fraction as a superposed
memory with a **self-describing key set**: D names the keys present, so
memories over open or sparse key sets detect absence without a schema and
merge by addition. The denominator queries and the measurements come with
it. FHRR on 4th roots of unity is the modular composite representation
(Snaider & Franklin 2014) with r = 4, without bundle quantisation.

## Summary

| Claim | Verdict |
|---|---|
| Memory storage and recall (001) | known (CRT records: Davida et al. 1981; secure lock 1989) |
| Schema mode (003) | known (Davida et al. 1981) |
| Self-describing key set: D names the keys present; absence and merge without a schema | apparently new as a superposed memory |
| Beats MAP-I at equal bits (001) | holds, and is expected from capacity theory; FHRR no better per bit; Deng–Raviv 50–8,265× our bits, but noise-tolerant |
| holding / agreeing / analogy via the denominator (002) | known in a different form: a packed record does them with word operations (006) |
| MAP-I with the same two-step procedure (002) | matches analogy and the agreeing set at n = 10,000 |
| No additive re-binding (002) | known lemma (Hom); a trade-off of this design, not of exactness |
| Graded nearness: p-adic hierarchy encoding (004) | known in a different form (Murtagh 2016; Martins 2025) |
| Graded nearness: every key's depth from one denominator (004, 005) | apparently new, shallow; a packed record would also do it |
| Frequent concepts on small primes (005) | known in a different form (Huffman) |
| Cost against ordinary structures (006) | no advantage measured on fixed records |
| Set sync | known (CPI; IBLT); we tie neither |

Bottom line (revised 2026-10-04): the algebra is old, and so is the integer
form of the memory. The claim that survives two reviews is narrow: the
reduced fraction as an exact superposed memory whose denominator names its
keys. That self-describing key set lets memories over open or sparse key
sets detect absence without a schema and merge by addition. The paper says
so, and states plainly what the memory is not.

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
- [Murtagh, Sparse p-adic data coding (arXiv 1604.06961)](https://research.gold.ac.uk/18816/1/1604.06961v1.pdf)
- [Martins, Learning with the p-adics (arXiv 2512.22692)](https://arxiv.org/abs/2512.22692)
- Davida, Wells & Kam, "A database encryption system with subkeys", ACM TODS 6(2), 1981, doi:10.1145/319566.319580
- Chang, "The study of an ordered minimal perfect hashing scheme", CACM 27(4), 1984, doi:10.1145/358027.358051
- Chang, "On the design of a key-lock-pair mechanism…", BIT 26(4), 1986, doi:10.1007/BF01935048
- Wu, Lee & Hsu, "A prime number labeling scheme for dynamic ordered XML trees", ICDE 2004
- Garner, "The residue number system", IRE Trans. Electronic Computers EC-8(2), 1959
- Goodrich & Mitzenmacher, "Invertible Bloom lookup tables", Allerton 2011, doi:10.1109/allerton.2011.6120248
- Eppstein, Goodrich, Uyeda & Varghese, "What's the difference?", SIGCOMM 2011, doi:10.1145/2018436.2018462
- Kohonen, "Correlation matrix memories", IEEE Trans. Computers C-21(4), 1972, doi:10.1109/TC.1972.5008975
- Anderson, "A simple neural network generating an interactive memory", Mathematical Biosciences 14, 1972
- Smolensky, "Tensor product variable binding…", Artificial Intelligence 46, 1990
- Lamport, "Multiple byte processing with full-word instructions", CACM 18(8), 1975
- Snaider & Franklin, "Modular composite representation", Cognitive Computation 6(3), 2014, doi:10.1007/s12559-013-9243-y
- Fuchs, *Infinite Abelian Groups*, vol. I, Academic Press, 1970
