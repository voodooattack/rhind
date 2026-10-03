"""
Graded nearness in an exact memory: keys at q-adic precision.

A schema gives each key a prime q and a precision k. A value at q is an
element of ℤ/q^k, stored as v/q^k:

    F = Σ v_q / q^k_q  (mod 1),        S = Σ 1 / q^k_q   (the schema's bag).

Nearness is q-adic: two values at q agree to depth j when their last j
base-q digits are equal, i.e. j = v_q(v − x), capped at k. Subtracting
x·S subtracts x from every value at once, and the q-part of the reduced
denominator of F − x·S is exactly q^(k − depth). So ONE subtraction
reports, for every key, how deeply its value agrees with x
(`agreement`). Between two memories over the same schema, the q-part of
den(F_A − F_B) gives the per-key agreement depth the same way
(`agreement_with`). Depth k means equal; the depths form an ultrametric
(the strong triangle inequality holds by construction).

The keys are primes; precision lives in the exponent, not in the key.
That is why prime powers are fine here: 5/25 reduces to 1/5, which keeps
the prime 5 in the denominator and records that the value has q-adic
depth 1. What breaks a memory is a key mixing DIFFERENT primes (15, or 6
and 10); see ExactMemory.build.

Digit agreement means something only if the encoding puts meaning in the
low digits. `encode_path` does that for hierarchies: the root-level choice
is the last base-q digit, so depth = the number of shared ancestor levels.
Nearness that is not a shared prefix (red car vs red apple) cannot be
expressed: the order of the levels is the model.

The schema is shared knowledge (as in schema mode, proof 003): only F is
the memory. Values are stored in full (0 included), so absence is not read
from the memory here; that is the trade for graded nearness.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, prod

from rhind.primes import is_prime


def encode_path(path, q: int) -> int:
    """A root-first path of choices (each 0 ≤ c < q) → a value whose last
    base-q digit is the root's choice. Depth of agreement = shared prefix."""
    v, place = 0, 1
    for c in path:
        if not 0 <= c < q:
            raise ValueError(f"choice {c} does not fit base {q}")
        v += c * place
        place *= q
    return v


def decode_path(v: int, q: int, k: int) -> list:
    """Inverse of encode_path for a path of length k."""
    out = []
    for _ in range(k):
        v, c = divmod(v, q)
        out.append(c)
    return out


def _frac_part(F: Fraction) -> Fraction:
    return F - (F.numerator // F.denominator)


def _depth(den: int, q: int, k: int) -> int:
    """k − (exponent of q in den), the exponent read via gcd with q^k."""
    g = gcd(den, q**k)
    e = 0
    while g % q == 0:
        g //= q
        e += 1
    return k - e


class Schema:
    """Keys (primes) with precisions. Shared by every memory built on it."""

    __slots__ = ("precision", "modulus", "D", "bag")

    def __init__(self, precision: dict):
        for q, k in precision.items():
            if not is_prime(q):
                raise ValueError(f"key {q} is not prime")
            if k < 1:
                raise ValueError(f"precision {k} for key {q} must be at least 1")
        self.precision = dict(precision)
        self.modulus = {q: q**k for q, k in self.precision.items()}
        self.D = prod(self.modulus.values()) if self.modulus else 1
        self.bag = _frac_part(
            sum((Fraction(1, m) for m in self.modulus.values()), Fraction(0))
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Schema) and self.precision == other.precision

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.precision.items())))


class AdicMemory:
    """Values in ℤ/q^k at prime keys, with graded (q-adic) nearness."""

    __slots__ = ("F", "schema")

    def __init__(self, F: Fraction, schema: Schema):
        self.F = _frac_part(Fraction(F))
        self.schema = schema
        if schema.D % self.F.denominator:
            raise ValueError("F does not live on this schema")

    @classmethod
    def build(cls, values: dict, schema: Schema) -> "AdicMemory":
        """{prime key q: value 0 ≤ v < q^k} → memory (keys not given hold 0)."""
        N = 0
        for q, v in values.items():
            m = schema.modulus.get(q)
            if m is None:
                raise KeyError(q)
            if not 0 <= v < m:
                raise ValueError(f"value {v} for key {q} must lie in 0 … {m - 1}")
            N += v * (schema.D // m)
        return cls(Fraction(N % schema.D, schema.D), schema)

    def get(self, q: int) -> int:
        """The value at key q, in 0 … q^k − 1."""
        m = self.schema.modulus[q]
        n = (self.F * self.schema.D).numerator  # integer: D is a multiple of den(F)
        return n % m * pow((self.schema.D // m) % m, -1, m) % m

    def agreement(self, x: int) -> dict:
        """{key: depth}: how many trailing base-q digits each value shares with
        x, up to its precision. One subtraction for all keys."""
        den = _frac_part(self.F - x * self.schema.bag).denominator
        return {q: _depth(den, q, k) for q, k in self.schema.precision.items()}

    def agreement_with(self, other: "AdicMemory") -> dict:
        """{key: depth} between two memories on the same schema."""
        if other.schema != self.schema:
            raise ValueError("memories are on different schemas")
        den = _frac_part(self.F - other.F).denominator
        return {q: _depth(den, q, k) for q, k in self.schema.precision.items()}

    def near(self, x: int, depth: int) -> list:
        """Keys whose value agrees with x to at least `depth` digits."""
        return sorted(q for q, j in self.agreement(x).items() if j >= depth)

    def __add__(self, other: "AdicMemory") -> "AdicMemory":
        if other.schema != self.schema:
            raise ValueError("memories are on different schemas")
        return AdicMemory(self.F + other.F, self.schema)

    def __sub__(self, other: "AdicMemory") -> "AdicMemory":
        if other.schema != self.schema:
            raise ValueError("memories are on different schemas")
        return AdicMemory(self.F - other.F, self.schema)

    def bits(self) -> int:
        """Size of the memory alone (N); the schema is shared knowledge."""
        return (self.F * self.schema.D).numerator.bit_length()

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, AdicMemory)
            and self.schema == other.schema
            and self.F == other.F
        )

    def __hash__(self) -> int:
        return hash((self.F, self.schema))

    def __repr__(self) -> str:
        return f"AdicMemory({len(self.schema.precision)} keys, {self.bits()} bits)"
