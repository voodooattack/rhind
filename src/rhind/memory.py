"""
An exact associative memory in one rational (proof 001).

    memory = Σ v_q / q   (mod 1)   =   N / D,   D = ∏ keys present

Keys are primes; a value is a residue 1 ≤ v < q (0 means "absent").
Recall reads the partial-fraction coefficient, v = N·(D/q)⁻¹ mod q, and a key
is absent exactly when q ∤ D: no false recalls. Merge and delete are + and −;
a key whose value reaches 0 mod q drops out of D by reduction. Restricting
to a subset of keys is one CRT step. Everything is exact.

A query needs only the key's prime, so keys may come from a shared
PrimeDictionary or from any deterministic map (a hash to a prime). Listing
the keys present needs D factored, which is cheap only over a known
dictionary.

Semantics to know: merging two memories that share a key ADDS the values
mod q (it is arithmetic, not a union that keeps one side). Use `conflicts`
first when that is not what you want.

Holistic operations (proof 002). Keep beside a record its
key bag S = Σ 1/q (`key_bag`): every key with value 1. Then
  F − x·S        subtracts x from EVERY value at once; the keys holding x
                 vanish from the reduced denominator, so
                 holding(x) = D / den(F − x·S)
  analogy        "the x of A": the key holding x in B, then A's value there
  agreeing       lcm(D_A, D_B) / den(F_A − F_B): the keys where both hold the
                 same value (equal values cancel)
Re-binding has no holistic form, and cannot have one: the value at key q
lives in ℤ/q, and the only additive map ℤ/q_old → ℤ/q_new for coprime
orders is zero. So `rebind` reads, then writes (proof 002, P5).
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, prod

from rhind.dictionary import PrimeDictionary
from rhind.primes import is_prime


def _den(F: Fraction) -> int:
    return (F - (F.numerator // F.denominator)).denominator


class ExactMemory:
    __slots__ = ("F",)

    def __init__(self, F: Fraction = Fraction(0)):
        F = Fraction(F)
        self.F = F - (F.numerator // F.denominator)  # live in Q/Z: [0, 1)

    # ── construction ──────────────────────────────────────────────────

    @classmethod
    def build(cls, facts: dict) -> "ExactMemory":
        """{prime key q: value 1 ≤ v < q} → memory.

        Keys must be prime. A composite key breaks the construction: a value
        sharing a factor with it collapses the key (5/15 = 1/3), two valid
        values can sum to such a value (4/15 + 1/15 = 1/3), and keys sharing
        a factor alias (1/6 + 1/10 = 4/15 = 2/3 + 3/5). Primality is checked
        with deterministic Miller–Rabin (exact below 3.3·10²⁴; a strong
        probable-prime test above that).

        `ExactMemory(F)` itself trusts its argument: checking an arbitrary
        fraction would mean factoring its denominator."""
        for q, v in facts.items():
            if not is_prime(q):
                raise ValueError(f"key {q} is not prime")
            if not 0 < v < q:
                raise ValueError(f"value {v} for key {q} must lie in 1 … {q - 1}")
        D = prod(facts) if facts else 1
        N = sum(v * (D // q) for q, v in facts.items())
        return cls(Fraction(N % D, D) if D > 1 else Fraction(0))

    # ── reading ───────────────────────────────────────────────────────

    @property
    def N(self) -> int:
        return self.F.numerator

    @property
    def D(self) -> int:
        return self.F.denominator

    def get(self, q: int):
        """The value stored under prime key q, or None if q is absent."""
        if self.D % q:
            return None
        return self.N % q * pow((self.D // q) % q, -1, q) % q or None

    def __contains__(self, q: int) -> bool:
        return self.D % q == 0

    def keys(self, dic: PrimeDictionary) -> list:
        """Keys present, by factoring D over a known dictionary."""
        ks = dic.factor(self.D) if self.D > 1 else []
        if prod(ks) != self.D:
            raise ValueError("D does not factor over this dictionary")
        return sorted(ks)

    def items(self, dic: PrimeDictionary) -> dict:
        return {q: self.get(q) for q in self.keys(dic)}

    def bits(self) -> int:
        return self.N.bit_length() + self.D.bit_length()

    # ── algebra ───────────────────────────────────────────────────────

    def merge(self, other: "ExactMemory") -> "ExactMemory":
        return ExactMemory(self.F + other.F)

    def delete(self, other: "ExactMemory") -> "ExactMemory":
        return ExactMemory(self.F - other.F)

    __add__ = merge
    __sub__ = delete

    def conflicts(self, other: "ExactMemory") -> int:
        """Product of the keys both memories hold (1 if they are disjoint)."""
        return gcd(self.D, other.D)

    def project(self, keys) -> "ExactMemory":
        """The sub-memory on the given prime keys (those present), one CRT step:
        F = A/D_S + B/D_R  ⇒  A ≡ N · D_R⁻¹ (mod D_S)."""
        D_S = prod(q for q in set(keys) if self.D % q == 0)
        if D_S == 1:
            return ExactMemory()
        D_R = self.D // D_S
        return ExactMemory(Fraction(self.N * pow(D_R, -1, D_S) % D_S, D_S))

    # ── holistic operations ───────────────────────────────────────────

    @classmethod
    def key_bag(cls, keys) -> "ExactMemory":
        """S = Σ 1/q over the given prime keys: the record's roles alone."""
        return cls.build({q: 1 for q in set(keys)})

    def holding(self, x: int, bag: "ExactMemory") -> int:
        """Product of the keys whose value is x (1 if none), in one subtraction.

        `bag` is the key bag of the roles to search; it may name keys this
        memory leaves empty (value 0). x must lie below every key.

        Every key of the bag or the memory with a value other than x stays in
        den(F − x·S) (an empty role contributes −x/q); the keys holding x
        vanish. So the answer is lcm(D, D_bag) / den(F − x·S). Dividing D
        alone is wrong as soon as the bag names an empty role."""
        if x <= 0:
            raise ValueError("values are positive")
        both = self.D // gcd(self.D, bag.D) * bag.D
        return both // _den(self.F - x * bag.F)

    def analogy(self, other: "ExactMemory", x: int, bag: "ExactMemory"):
        """'The x of self': self's value at the key where `other` holds x, or
        None if other holds x at no key, or at more than one."""
        q = other.holding(x, bag)
        return self.get(q) if q > 1 and is_prime(q) else None

    def agreeing(self, other: "ExactMemory") -> int:
        """Product of the keys present in both memories with equal values."""
        lcm = self.D // gcd(self.D, other.D) * other.D
        return lcm // _den(self.F - other.F)

    def rebind(self, q_old: int, q_new: int) -> "ExactMemory":
        """Move the value at q_old to q_new (read, then write: no holistic
        form exists). The value must lie below q_new."""
        if not is_prime(q_new):
            raise ValueError(f"key {q_new} is not prime")
        v = self.get(q_old)
        if v is None:
            raise KeyError(q_old)
        if q_new in self:
            raise ValueError(f"key {q_new} is already present")
        if v >= q_new:
            raise ValueError(f"value {v} does not fit below key {q_new}")
        return ExactMemory(self.F - Fraction(v, q_old) + Fraction(v, q_new))

    def __eq__(self, other) -> bool:
        return isinstance(other, ExactMemory) and self.F == other.F

    def __hash__(self) -> int:
        return hash(self.F)

    def __repr__(self) -> str:
        return f"ExactMemory({self.bits()} bits)"
