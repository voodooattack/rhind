// Exact vector-symbolic memory from partial fractions — draft.
// Build from the repository root (data paths are root-relative):
//   typst compile --root . papers/exact-vsa/main.typ
// Every number in a table, and every number quoted in the prose through
// #cell(...), is read from the proofs' data files. Re-run the proofs and
// recompile; nothing is copied by hand.

#let d001 = json("/reports/001_exact_memory_vs_noisy_vsa_data.json")
#let d002 = json("/reports/002_exact_holistic_operations_data.json")
#let d003 = json("/reports/003_schema_mode_data.json")
#let d004 = json("/reports/004_graded_nearness_data.json")
#let d005 = json("/reports/005_concepts_and_hierarchies_data.json")

#let sec(d, prefix) = d.sections.find(s => s.title.starts-with(prefix))
#let at-k(s, key, value) = s.rows.find(r => r.at(key) == value)
#let cell(s, key, value, col) = [#at-k(s, key, value).at(col)]

// Thousands separators for integers; strings pass through.
#let fmt(v) = {
  if type(v) == int {
    let s = str(calc.abs(v))
    let out = ""
    let n = s.len()
    for (i, ch) in s.clusters().enumerate() {
      if i > 0 and calc.rem(n - i, 3) == 0 { out += "," }
      out += ch
    }
    if v < 0 { "−" + out } else { out }
  } else { str(v) }
}

#let datatable(s, cols, heads, caption) = figure(
  table(
    columns: cols.len(),
    align: (x, _) => if x == 0 { left } else { right },
    stroke: none,
    table.hline(),
    table.header(..heads.map(h => text(size: 8.5pt)[*#h*])),
    table.hline(stroke: 0.5pt),
    ..s.rows.map(r => cols.map(c => text(size: 8.5pt)[#fmt(r.at(c))])).flatten(),
    table.hline(),
  ),
  caption: caption,
  kind: table,
)

#let m1 = sec(d001, "P1–P3")
#let m5 = sec(d001, "P5–P6")
#let m7 = sec(d001, "P7")
#let m4 = sec(d001, "P4")
#let h1 = sec(d002, "P1–P4")
#let h5 = sec(d002, "P5")
#let s1 = sec(d003, "P1–P3")
#let s4 = sec(d003, "P4")
#let g1 = sec(d004, "P1–P4")
#let g5 = sec(d004, "P5")
#let c1 = sec(d005, "P1")
#let c2 = sec(d005, "P2–P3")
#let c4 = sec(d005, "P4")

#set document(title: "Exact Vector-Symbolic Memory from Partial Fractions", author: "Abdullah Ali")
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm), numbering: "1")
#set text(size: 10.5pt, lang: "en")
#set par(justify: true)
#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")
#show figure.where(kind: table): set figure.caption(position: top)

#let theorem(name, body) = block(width: 100%, inset: (y: 3pt))[*#name.* #emph(body)]
#let proof(body) = block(width: 100%, inset: (y: 2pt))[_Proof._ #body #h(1fr) $square$]

#align(center)[
  #text(size: 16pt, weight: "bold")[Exact Vector-Symbolic Memory from Partial Fractions]
  #v(4pt)
  Abdullah Ali \
  #text(size: 9pt)[Independent researcher · #link("mailto:voodooattack@gmail.com")[voodooattack\@gmail.com]]
  #v(2pt)
  #text(size: 9pt, fill: gray)[Draft — #datetime.today().display()]
]

#v(6pt)
#block(inset: (x: 1.2cm))[
  #set text(size: 9.5pt)
  *Abstract.* Vector symbolic architectures (VSAs) store key–value facts by
  superposing bound vectors, and pay for superposition with noise: recall
  degrades with load, and absent keys are answered with false positives. We
  show that a single reduced fraction gives the same interface exactly. Keys
  are distinct primes $q$, a value is a residue $1 <= v < q$, and a memory is
  $F = sum v_q \/ q mod 1$. Recall is one modular inversion, absence is
  non-divisibility of the denominator, and merge and delete are fraction
  addition and subtraction. The construction is the classical
  Chinese-remainder "secure lock" in partial-fraction form; what the fraction
  form adds is that the denominator _is_ the key set. That yields holistic
  queries that VSAs answer only approximately — every key holding a given
  value in one subtraction, exact analogy, and the set of agreeing roles of
  two records — and a proof that exact re-binding cannot be holistic,
  because $"Hom"(ZZ\/p, ZZ\/q) = 0$. The memory costs about 1.3× an
  ideally packed table (#cell(m1, "K", 10, "set_ratio") to #cell(m1, "K", 3000, "set_ratio") the information-theoretic
  minimum for an unordered set of facts), and when the key set is known in
  advance a numerator alone suffices, at #cell(s1, "m", 10, "ratio") the packed size of a ten-role record. At equal storage the strongest dense VSA (FHRR) is no
  better than a bipolar one, and the closest published exact VSA needs
  #cell(m7, "K", 10, "ratio") to #cell(m7, "K", 3000, "ratio") the bits, in exchange for noise tolerance that ours
  lacks. Every number is produced by executable proofs.
]

= Introduction

A VSA represents symbols as high-dimensional random vectors and composes
them with two operations: _binding_ (an invertible product, associating a key
with a value) and _bundling_ (a sum, superposing many facts in one vector)
@plate1995hrr @kanerva2009hd @kleyko2022survey1. Unbinding a key from a
bundle returns its value plus cross-talk from every other fact, and a
_clean-up_ against the codebook removes the noise while the load is low. The
capacity of this scheme is well understood @frady2018capacity: noise grows
with the number of stored facts, so recall degrades gracefully and false
recalls appear.

The attraction of VSAs is not lookup — a dictionary does that — but
operations on whole structures: analogy through a mapping vector
@kanerva2010dollar, similarity between composite records, re-binding a role.
This paper asks what those operations look like when the memory is exact.

Our answer uses rational numbers. Superposition is fraction addition; the
key of a fact is the prime in its denominator; the value is the residue in
its numerator. Because distinct primes are coprime, the partial-fraction
decomposition of the sum is unique, and every fact is recoverable.

*Contributions.*
- An exact key–value memory $F = sum v_q \/ q mod 1$ with one-step recall,
  detection of absent keys, and merge and delete as $+$ and $-$
  (@sec-memory). We identify it with the Chinese-remainder secure lock
  @chiou1989lock and state what the fraction form adds, why the keys must
  be prime, and a _schema mode_ that drops the denominator when the key set
  is predictable.
- Exact holistic operations: all keys holding a value, analogy, and agreeing
  roles, each by one subtraction and a denominator (@sec-holistic).
- A proof that no exact memory of this kind has a holistic re-binding
  (@sec-rebind).
- Graded nearness without noise: keys at $q$-adic precision, where one
  subtraction gives every role's depth of agreement with a probe or another
  record; with concepts as keys and hierarchies as digits it covers shared
  concepts and shared ancestry at once (@sec-graded).
- An empirical comparison at equal storage against a bipolar VSA, against
  FHRR, and against the exact VSA of Deng and Raviv
  @dengraviv2025histogram, with every number produced by an executable
  proof (@sec-experiments).

= Related work <sec-related>

*Noisy VSAs.* Holographic reduced representations @plate1995hrr,
multiply–add–permute (MAP) and its variants, Fourier HRR (FHRR) and others
are surveyed in @kleyko2022survey1 @kleyko2022survey2 and compared
empirically in @schlegel2022comparison. All trade exactness for a fixed
dimension; capacity theory is in @frady2018capacity. We compare against MAP-I
(integer bundling) and against FHRR.

*Residue VSAs.* Kymn et al. @kymn2023residue encode integers as phasor
vectors whose frequencies are roots of unity for a set of moduli, so that
addition and multiplication of encoded numbers are exact; decoding uses a
resonator network and similarity is approximate. A Lisp built on that
representation appears in @vsalisp2025. These encode _numbers_ by the
Chinese remainder theorem (CRT); we encode a _memory_ by it. Thaine and
Penn @thaine2021crt pack an embedding vector into one integer by the CRT.

*Exact VSAs.* Deng and Raviv @dengraviv2025histogram build VSA atoms from
concatenated Reed–Solomon and Hadamard codes and recover a superposition of
up to a bounded number of codewords by list decoding, with formal
guarantees and tolerance to noise. It is the closest published exact VSA;
@sec-dr compares sizes.

*CRT broadcasting.* Chiou and Chen's secure lock @chiou1989lock, and later
CRT key distribution @intel1998patent, broadcast one integer $X$ with
$X equiv k_i (mod p_i)$ so that receiver $i$ reads its key as $X mod p_i$.
Our numerator is such an $X$ (@sec-memory). The goals differ: a broadcast
lock must give non-members garbage, while our memory must _detect_ absent
keys, which the fraction's denominator does.

*Set reconciliation.* Minsky, Trachtenberg and Zippel
@minsky2003reconciliation reconcile sets through rational functions of
their characteristic polynomials. Our key bag $S = sum 1\/q$ is the integer
analogue of the logarithmic derivative $chi'\/chi = sum 1\/(z - a)$ of a
characteristic polynomial $chi$.

*p-adic and ultrametric representations.* Encoding a hierarchy as p-adic
digit strings, so that shared ancestry becomes a long common prefix and the
Baire metric $r^(-beta)$ measures it, is established: Murtagh
@murtagh2016padic uses it for clustering dendrograms and replaces sparsity
by the p-adic norm, and Martins @martins2025padics develops classification,
regression and representation learning over $QQ_p$, including Quillian
semantic networks as compact p-adic linear networks. Our graded nearness
(@sec-graded) uses the same ultrametric. What differs is where it is read:
inside a superposed memory, where one subtraction returns the depth for
every key at once. Neither line of work involves superposition or a
key–value memory.

= The memory <sec-memory>

Fix a set of _keys_: distinct primes. A _fact_ is a pair $(q, v)$ with $q$ a
key and $1 <= v < q$. A memory holding facts $\{(q, v_q) : q in Q\}$ is

$ F = sum_(q in Q) v_q / q mod 1 = N / D, quad gcd(N, D) = 1, quad 0 <= N < D. $ <eq-memory>

#theorem("Proposition 1 (structure and recall)")[
  $D = product_(q in Q) q$, and for each $q in Q$,
  $v_q equiv N dot (D\/q)^(-1) (mod q)$.
]
#proof[
  Multiplying @eq-memory by $P = product_(q in Q) q$ gives
  $F P equiv sum_q v_q (P\/q) (mod P)$. Modulo a fixed $q in Q$, every term
  but one contains the factor $q$, leaving $v_q (P\/q)$, which is nonzero
  because $q divides.not v_q$ and $q divides.not P\/q$. So no $q$ divides the
  numerator of $F P \/ P$, the fraction is already reduced, $D = P$, and
  $N equiv v_q (D\/q) (mod q)$; $D\/q$ is invertible modulo $q$.
]

Recall is therefore one multiplication and one reduction modulo $q$.
A key $p$ is _absent_ exactly when $p divides.not D$, so the memory answers
"not stored" without false positives. Facts are added and removed by
$F plus.minus v\/q$, and a fact is removed by subtracting its exact value,
so deletion is read-then-subtract. Two memories over disjoint keys merge by
$F_A + F_B$. Merge is per-key addition modulo $q$, not a union: at a shared
key the values add ($A + A$ doubles every value, and values summing to $q$
remove the key), so $gcd(D_A, D_B) > 1$ flags keys the two memories
_share_; which of those hold equal values is the agreeing-roles query of
@sec-holistic.
Projecting onto a subset $R subset Q$ is one CRT step.

*Why primes.* Memories over prime keys form the group
$plus.o.big_q ZZ\/q$, so every sum and difference is again a valid
memory: values at a shared key add modulo $q$, and a value reaching $0$
removes its key cleanly. Pairwise-coprime composite keys do not have this
closure. With the key $15$, two admissible facts sum to an inadmissible
one, $4\/15 + 1\/15 = 1\/3$, and the key collapses into a phantom key $3$;
a non-unit value $5\/15 = 1\/3$ does the same directly. Keys sharing a
factor alias outright: $1\/6 + 1\/10 = 4\/15 = 2\/3 + 3\/5$, so two
different memories have the same fraction. What fails is a key mixing
different primes. A prime power is sound ($5\/25 = 1\/5$ keeps the prime
$5$ and records how many base-$5$ digits of the value are zero); that is
the starting point of graded nearness (@sec-graded). Elsewhere we use
prime keys.

*Size.* $N < D$, so the memory takes at most $2 log_2 D = 2 sum_q log_2 q$
bits. With keys the primes above the value range, this is about
#cell(m1, "K", 1000, "ratio") the size of an ideally packed table of
$K (ceil(log_2 U) + ceil(log_2 V))$ bits (@tab-map). That table is ordered;
an unordered set of $K$ facts needs only
$ceil(log_2 (binom(U, K) (V - 1)^K))$ bits, and against that floor the
memory costs #cell(m1, "K", 10, "set_ratio") at $K = 10$, rising to #cell(m1, "K", 3000, "set_ratio") at
$K = "3,000"$: it spends about $2 log_2 q$ bits per fact, while the floor per
fact shrinks as $K$ grows.

*Relation to the secure lock.* Proposition 1 says $N$ solves the system
$X equiv v_q (D\/q) (mod q)$: the CRT broadcast integer of
@chiou1989lock, with each slot scaled by the unit $D\/q$. Two properties
come from carrying the fraction rather than the integer. The modulus
travels with the value, so merge is plain addition rather than a CRT
recombination; and membership is read from $D$.

*Schema mode.* Most of the overhead above is $D$ itself: $N$ and $D$ have
about the same length. When the key set is known in advance — a record
whose roles are always the same primes, for instance the first $m$ primes
above the value range — $D$ can be recomputed and only $N$ stored. That is
the secure-lock integer again, and it gives up reading absence from the
memory: that knowledge moves to the schema. In exchange the record costs
#cell(s1, "m", 10, "ratio") the packed size $m ceil(log_2 V)$ at $m = 10$ roles and
#cell(s1, "m", 1000, "ratio") at $m = "1,000"$, half of the fraction form,
while merge of records with disjoint supports ($N_1 + N_2 mod D$) and the value query of @sec-holistic still
work (@sec-schema). For sparse memories over a known dictionary, $D$ is
itself a key-set encoding, and the cheapest one only when very sparse
(@tab-sparse).

= Holistic operations <sec-holistic>

Let $S = sum_(q in R) 1\/q$ be the _key bag_ of a set of roles $R$, with
denominator $D_R = product_(q in R) q$. For records that share a schema of
roles, one $S$ serves them all, including records that leave some roles
empty ($v_q = 0$ for $q in R without Q$).

#theorem("Proposition 2 (value query)")[
  For an integer $x$ with $1 <= x < min R$,
  $"den"(F - x S) = product q$ over $q in Q union R$ except the keys
  $q in R$ with $v_q = x$.
  Hence the keys of $R$ holding $x$ are the prime factors of
  $"lcm"(D, D_R) \/ "den"(F - x S)$.
]
#proof[
  $F - x S equiv sum_(q in Q union R) (v_q - x [q in R])\/q$, with $v_q = 0$
  off $Q$. For $q in R$ the term vanishes when $v_q = x$; otherwise
  $0 < |v_q - x| < q$ because $x < q$. For $q in Q without R$ the term is
  $v_q\/q$ with $0 < v_q < q$, whatever $x$ is: a stored key outside $R$
  is never reported. Each surviving term has exact denominator $q$, and
  by the argument of Proposition 1 the denominator of the sum is the
  product of those $q$.
]

An empty role keeps its prime in $"den"(F - x S)$ through the term $-x\/q$,
although that prime is not in $D$; dividing $D$ alone is then wrong, which
is why the statement uses $"lcm"(D, D_R)$. (Our first schema-mode
experiment found exactly this error in an earlier version of the library.)

One subtraction thus subtracts $x$ from every value at once, and the matches
drop out of the denominator. Two operations follow directly.

*Analogy* — "what is the dollar of Mexico?" @kanerva2010dollar. Given
records $A$ (Mexico) and $B$ (USA) over the same roles, the role of $x$
(dollar) in $B$ is $"lcm"(D_B, D_R) \/ "den"(F_B - x S)$ (Proposition 2;
the lcm matters when $B$ leaves a role empty); the answer is $A$'s value at
that role (Proposition 1). The analogy is defined when $x$ sits at exactly
one role of $B$: the quotient is then a single prime, and otherwise it is
$1$ or a product, which the query reports as no answer. In a VSA the same query unbinds through a mapping
vector $A dot.o B$ whose $m^2$ cross terms make it approximate.

*Agreeing roles.* For records $A$, $B$,
$"den"(F_A - F_B) = product q$ over keys where the records differ (a key
stored in only one counts as differing), so
$"lcm"(D_A, D_B) \/ "den"(F_A - F_B)$ is the product of the keys on which
they agree.

== Graded nearness <sec-graded>

The memory so far answers equality. Precision gives it graded nearness.
Give each prime key $q$ a precision $k_q$ and let its value $v_q$ live in
$ZZ\/q^(k_q)$, stored as $v_q\/q^(k_q)$. Two values agree to depth $j$ when
their last $j$ base-$q$ digits are equal, $j = min(k_q, nu_q (v - x))$,
with $nu_q$ the $q$-adic valuation.

#theorem("Proposition 4 (graded agreement)")[
  For records $F = sum v_q \/ q^(k_q)$ and $P = sum x_q \/ q^(k_q)$ on the
  same keys, the exponent of $q$ in $"den"(F - P)$ is $k_q - j_q$, where
  $j_q$ is the depth to which $v_q$ and $x_q$ agree.
]
#proof[
  The $q$-term of $F - P$ is $(v_q - x_q)\/q^(k_q)$. Writing
  $v_q - x_q = q^(j_q) u$ with $q divides.not u$ (or $0$, when $j_q = k_q$),
  it reduces to $u \/ q^(k_q - j_q)$, and terms at distinct primes do not
  interact (Proposition 1).
]

So one subtraction, against a probe record or another record, gives every
role's depth at once. Depth defines an ultrametric, $q^(-j)$ (two values
agreeing to depths $i$ and $j$ with a third agree to depth _at least_
$min(i, j)$ with each other). It
means something only if the encoding puts meaning in the low digits: for a
hierarchy, write the root's choice as the last digit, the next level's as
the one before, and so on, and the depth becomes the number of shared
ancestors. Inside one value, nearness is necessarily a shared prefix: the
order of the levels is the model. Across a record it need not be. Give each
concept (attribute) its own key and let its value be a path in that
concept's own hierarchy: a red car and a blue car then agree fully at the
key for _kind_ and to whatever depth the colour hierarchy shares at the key
for _colour_, and one subtraction reports both. Shared keys are shared
concepts (a bag), digits are shared ancestry (a tree) (@sec-concepts).

== Re-binding is not holistic <sec-rebind>

Re-binding moves a value from key $p$ to key $q$. In a VSA it is linear
— multiply the bundle by $p dot.o q$ — because all keys live in one
group. Here they do not. The $p$-part of $F$ lives in
$(1\/p) ZZ \/ ZZ tilde.equiv ZZ\/p$ and the $q$-part in $ZZ\/q$.

#theorem("Proposition 3")[
  For distinct primes $p$, $q$ every additive map $phi: ZZ\/p -> ZZ\/q$ is
  zero.
]
#proof[
  $phi$ is fixed by $c = phi(1)$ and must satisfy $p c = phi(p dot 1) =
  phi(0) = 0$ in $ZZ\/q$. As $p$ is invertible modulo $q$, $c = 0$.
]

So no additive operation on the memory transfers a value between keys; an
exact re-binding must read $v$ out to $ZZ$ (Proposition 1) and write
$F - v\/p + v\/q$. The VSA's holistic re-binding is a consequence of the
shared group that also makes it noisy. The proof script checks the
statement exhaustively for the #fmt(h5.rows.at(0).pairs) ordered pairs of
distinct primes below #h5.rows.at(0).bound and finds
#h5.rows.at(0).nonzero nonzero maps.

= Experiments <sec-experiments>

All experiments are executable scripts that assert their expected outcomes
and emit a report and a data file only when every assertion holds. Most
thresholds were fixed after an exploratory pilot had measured the effect,
so they guard the result against regressions rather than predict it
blind; the FHRR predictions below were derived from a variance argument
before any FHRR run. The exact-memory rows check Propositions 1, 2 and 4 in
software: they test the implementation, not an empirical hypothesis. Arithmetic is exact (integers and
fractions); NumPy is used as an integer array engine for the baselines.
Tables in this paper are generated from those data files.

*Setup.* A universe of $U = "20,000"$ keys and $V = "1,000"$ values; keys map
to the primes above $V$. For each load $K$ we draw $K$ random facts, query
up to 300 stored keys and 300 absent keys. *MAP-I* @schlegel2022comparison (below,
MAP): bipolar atoms, binding by elementwise product, bundling by integer
sum without thresholding, clean-up by integer dot product against all $V$
value vectors, and "present" when the best score is at least $n\/2$. A VSA's
bits are $n$ times the width of its largest counter. We report MAP at the
exact memory's bits and at $n = "10,000"$.

== Against a bipolar VSA

#datatable(
  m1,
  ("K", "ex_recall", "ex_false", "ex_bits", "ratio", "set_ratio", "m_recall", "m_false", "t_recall", "t_false"),
  ("K", "exact", "false", "bits", "÷ packed", "÷ set floor", "MAP same bits", "false", "MAP n=10⁴", "false"),
  [Exact memory against MAP. Recall is stored keys answered correctly; _false_ is absent keys answered (of 300). _÷ packed_: against $K (ceil(log_2 U) + ceil(log_2 V))$ bits; _÷ set floor_: against $ceil(log_2 (binom(U, K) (V-1)^K))$.],
) <tab-map>

The exact memory recalls every stored key and no absent key at every load,
at a constant ratio to the packed table, and a slowly rising one to the
set floor (@tab-map). MAP at the same bits fails from
the smallest load. Given $n = "10,000"$ dimensions, many times the bits, it is
perfect to $K = 100$, answers #cell(m1, "K", 300, "t_false") of 300 absent
keys at $K = 300$, and recalls #cell(m1, "K", 1000, "t_recall") at
$K = "1,000"$. The exact memory is also the fastest to query here:
recall is one big-integer reduction, linear in the memory's size but run in
native code (#cell(m1, "K", 3000, "ex_us") µs at $K = "3,000"$ against
#cell(m1, "K", 3000, "m_us") µs for MAP's clean-up). Random sequences of
#fmt(m4.rows.at(0).ops) inserts, deletes and merges leave the memory equal to
one rebuilt from scratch.

== Against FHRR

FHRR binds by multiplying unit phasors and bundles by complex sum. We place
the phases on the 4th roots of unity, so every component is a Gaussian
integer and the clean-up score $"Re" sum_j m_j overline(z_j)$ is exact.
This loses nothing: the noise a stored fact adds to a score is the real
part of a random phasor, $cos theta$, and for $theta$ uniform on $m >= 3$
equally spaced points, or on the circle,
$EE[cos theta] = 0$ and $EE[cos^2 theta] = 1\/2 + EE[cos 2 theta]\/2 = 1\/2$.
Against MAP's variance of 1 this halves the noise per dimension, but each
component needs two counters. We therefore predicted no gain per bit and a
doubling of capacity at fixed $n$.

#datatable(
  m5,
  ("K", "f_n", "f_recall", "m_recall", "t_recall", "t_false", "tm_recall"),
  ("K", "FHRR n", "FHRR same bits", "MAP same bits", "FHRR n=10⁴", "false", "MAP n=10⁴"),
  [FHRR on the same facts. _FHRR n_ is the dimension affordable at the exact memory's bits.],
) <tab-fhrr>

Both predictions held (@tab-fhrr): at equal bits FHRR and MAP agree almost
row for row, and at $n = "10,000"$ FHRR recalls
#cell(m5, "K", 1000, "t_recall") at $K = "1,000"$ where MAP recalls
#cell(m5, "K", 1000, "tm_recall"). The comparison at equal storage is thus
not an artefact of a weak baseline: per bit, the strongest dense VSA is no
better.

== Against an exact VSA <sec-dr>

Deng and Raviv's atoms @dengraviv2025histogram are Reed–Solomon codewords
over $FF_N$, $N = p^m$, mapped through a Hadamard code to $n = N^2$ roots of
unity. With the key and the value each owning a block of the message, a
bound pair has code dimension $k = ceil(log_N U) + ceil(log_N V)$, and in
the noiseless case their bound recovers $u <= floor((N - 1)\/(k - 1))$
superposed pairs. Hence $n >= (u (k - 1) + 1)^2$: storage grows at least
quadratically in the number of facts. We take their noiseless bound, charge
each bundle entry only its information content
$ceil(log_2 binom(u + p - 1, p - 1))$ bits, and choose the cheapest prime
power $N <= 2^14$; all three choices favour them.

#datatable(
  m7,
  ("K", "ex_bits", "dr_bits", "ratio", "field", "k"),
  ("K", "exact bits", "Deng–Raviv bits", "÷ exact", "N", "k"),
  [Bits to hold the same $K$ facts. Binary fields were cheapest at every load.],
) <tab-dr>

The ratio grows from #cell(m7, "K", 10, "ratio") at 10 facts to
#cell(m7, "K", 3000, "ratio") at 3,000 (@tab-dr). What the premium buys is
real: their memory survives corrupted entries, ours does not. The two
constructions sit at opposite corners — exact near the packed size and
fragile, or exact under noise at quadratic cost; redundant moduli
(@sec-limits) could place a CRT memory between them, which we leave untested.

== Holistic operations

Records have $m$ roles, each with its own vocabulary of 100 fillers; analogy
pairs share no filler, as in @kanerva2010dollar. MAP computes analogy as
clean-up of $x dot.o A dot.o B$, the agreeing-role count as
$"round"(A dot B \/ n)$, and re-binding by reading with clean-up and
rewriting.

#datatable(
  h1,
  ("m", "ex", "ex_bits", "an", "ag", "rb", "map_bits", "an_m"),
  ("roles m", "exact (all ops)", "exact bits", "MAP analogy", "MAP agreeing", "MAP re-bind", "MAP bits", "MAP same bits: analogy"),
  [Exact holistic operations against MAP at $n = "10,000"$ (correct of 100) and at the exact records' bits.],
) <tab-holistic>

The exact operations are correct in every trial (@tab-holistic). MAP's
mapping vector carries $m^2$ cross terms, so its analogy accuracy falls from
#cell(h1, "m", 10, "an")% at $m = 10$ to #cell(h1, "m", 100, "an")% at
$m = 100$, while using #fmt(at-k(h1, "m", 100).map_bits) bits against the
exact record's #fmt(at-k(h1, "m", 100).ex_bits).

== Schema mode <sec-schema>

Records have $m$ roles, the first $m$ primes above $V = "1,000"$, with values
$0 <= v < V$ ($0$ an empty role); 200 records per $m$. Only $N$ is stored;
$D$ is recomputed from the schema. The packed size is $m ceil(log_2 V)$ bits.
Merge is tested on pairs of records with disjoint supports.

#datatable(
  s1,
  ("m", "round_trip", "n_bits", "floor", "ratio", "frac_bits", "frac_ratio", "merge", "holding"),
  ("roles m", "round trip", "N bits", "packed", "÷ packed", "fraction bits", "÷ schema", "merge", "holding"),
  [Schema mode: exact round trip, size against the packed size and against storing $N$ and $D$, and the operations.],
) <tab-schema>

For a sparse memory over a known dictionary of $U = "20,000"$ entries, the key
set can be stored as $D$, as Elias-γ codes of the gaps between dictionary
positions, or as a presence bitmap:

#datatable(
  s4,
  ("K", "d_bits", "gamma_bits", "bitmap_bits", "best"),
  ("keys K", "D", "γ gaps", "bitmap", "cheapest"),
  [Bits to store which $K$ keys are present.],
) <tab-sparse>

$D$ wins only at #at-k(s4, "best", "D").K keys; a gap code wins from about
100 keys and a bitmap once half the dictionary is present (@tab-sparse). So
the fraction form's self-description costs little in very sparse memories
and should be traded for a schema or an index code in dense ones.

== Graded nearness <sec-graded-exp>

A taxonomy of 4 levels with branching 4 (256 leaves); records of $m$ roles,
each holding a leaf encoded in its key's base. Probe depths are prescribed
uniformly in ${0, dots, 4}$, so a fixed guess scores 20%. MAP-I encodes a
leaf as the sum of one vector per ancestor prefix, so that its dot product
counts shared ancestors. To compare two records role-wise it must first
clean up each unbound role to the nearest of the 256 leaves: without that,
$(r dot.o R_A) dot (r dot.o R_B) = R_A dot R_B$ for every role $r$, since
$r dot.o r = 1$, and only the whole-record similarity remains.

#datatable(
  g1,
  ("m", "ex_q1", "ex_q2", "ex_bits", "map_bits", "map_q1", "map_q2", "same_q1", "same_q2"),
  ("roles m", "exact: probe", "exact: records", "exact bits", "MAP bits", "MAP: probe", "MAP: records", "same bits: probe", "records"),
  [Role-wise depth of agreement, to a probe item and between two records. MAP at $n = "10,000"$ (records compared after clean-up) and at the exact record's bits.],
) <tab-graded>

Every exact depth is right, from one subtraction, at #fmt(at-k(g1, "m", 100).ex_bits)
bits for 100 roles against MAP's #fmt(at-k(g1, "m", 100).map_bits) bits, and
MAP's probe query falls to #cell(g1, "m", 100, "map_q1") at 100 roles (@tab-graded). Inside
one value the prefix shape is binding: packing four independent attributes
into one value, its depth equals the number of shared attributes for exactly
#g5.rows.at(0).fraction of all ordered pairs (those whose shared attributes
happen to form a prefix), while a MAP bag of attribute vectors recovers the
count for #g5.rows.at(0).bag_ok random pairs. That is a limit of the
encoding, as the next section shows.

== Concepts and hierarchies <sec-concepts>

The same 256 leaves with one attribute per key: the number of keys agreeing
at full depth equals the shared-attribute count for
#c1.rows.at(0).per_key ordered pairs. With $m$ attributes, each a
hierarchy of 3 levels (branching 3) at its own key, one subtraction gives
every attribute's depth of agreement:

#datatable(
  c2,
  ("m", "exact", "ex_bits", "map_acc", "map_bits", "same_acc"),
  ("attributes m", "exact: every depth", "exact bits", "MAP (n=10⁴)", "MAP bits", "MAP same bits"),
  [Bag and tree nearness together: per-attribute depth of agreement between two records. MAP compares each attribute after a clean-up against that attribute's 27 leaves.],
) <tab-concepts>

MAP matches the exact depths at $n = "10,000"$ with a clean-up per role,
using #fmt(at-k(c2, "m", 64).map_bits) bits against the exact record's
#fmt(at-k(c2, "m", 64).ex_bits) at 64 attributes (@tab-concepts).

Which concept gets which prime is a coding choice. With frequent concepts
on the smallest primes, sparse records (1,000 concepts, concept $i$
present with probability $1\/(i+1)$) take #cell(c4, "order", "frequency", "vs_random")
the bits of a random assignment, and the reverse order
#cell(c4, "order", "reversed", "vs_random"): frequent concepts get the cheapest keys, as a
Huffman code gives frequent symbols the shortest words.

= Limitations <sec-limits>

- *No noise tolerance.* One flipped bit of $N$ or $D$ corrupts the whole
  memory as built here. Graceful degradation, the main virtue of VSAs, is
  absent from this form, though not from the representation: redundant
  moduli turn a CRT integer into an error-correcting code
  @goldreich2000crt, at a cost in bits we have not measured.
- *Query cost grows with the memory.* Recall reduces an integer of
  $approx 2 sum log_2 q$ bits modulo $q$: linear in the memory's size, not
  constant like a hash table.
- *Keys are primes and bound values.* Symbols need a prime dictionary
  (composite keys break closure under addition, @sec-memory), and values
  must be smaller than every key that may hold them.
- *Nearness is structured, not geometric.* Atoms are not
  similarity-preserving. Nearness is shared concepts (keys) and shared
  ancestry (prefixes within a value, @sec-graded); similarity that is
  neither — learned or continuous, as in an embedding — is outside it.
- *What is new is narrow.* The algebra (partial fractions, the CRT,
  prime-product sets, p-adic encodings of hierarchies) is classical, and the
  secure lock already stores values this way. Our contribution is the VSA
  interface — superposition, unbinding, holistic queries and graded
  nearness — as rational arithmetic, its proofs, and the measured
  comparison.

= Conclusion

Superposition does not have to be noisy. Writing a key–value memory as one
reduced fraction gives exact recall, exact absence, and merge and delete as
arithmetic, at about 1.3× an ideally packed table — or within
#cell(s1, "m", 10, "ratio") to #cell(s1, "m", 1000, "ratio") of it when the key set is known and only the numerator is kept; its denominator turns
value queries, analogy and role agreement into one subtraction each, and
with $q$-adic precision it grades nearness, exactly, over shared concepts
and shared ancestry at once. It does not re-bind holistically, and cannot. Against VSAs at equal storage, the
noisy ones fail and the exact one costs orders of magnitude more, buying
noise tolerance. The practical question this leaves is the one a dictionary
never asks: which applications want VSA-style operations _and_ exactness —
symbolic reasoning over small structured records is the natural candidate.

*Reproducibility.* The library (`rhind.memory`), the proofs
(001–005) and their data files are in the accompanying repository;
rerunning a proof regenerates its report and data, and recompiling this
document regenerates every table.

#bibliography("refs.bib", style: "ieee")
