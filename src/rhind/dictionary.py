"""
Symbols ↔ primes.

A PrimeDictionary assigns each symbol its own prime and factors
denominators over the dictionary (by gcd against chunk products), which is
how a memory lists the keys it holds. `residue` reads the partial-fraction
numerator of N/D at one prime: c ≡ N · (D/p)⁻¹ (mod p).
"""

from __future__ import annotations

from math import gcd, prod

from rhind.primes import odd_primes


def residue(N: int, D: int, p: int) -> int:
    """Partial-fraction numerator of N/D at the prime p (p ∥ D), in [0, p)."""
    return N * pow(D // p, -1, p) % p


class PrimeDictionary:
    """items ↔ primes, plus fast factoring of denominators over the dictionary."""

    def __init__(self, items, primes=None, start_after: int = 2, chunk: int = 256):
        items = list(items)
        self.primes = (
            list(primes) if primes is not None else odd_primes(len(items), start_after)
        )
        if len(self.primes) < len(items):
            raise ValueError("not enough primes for the items")
        self.prime = dict(zip(items, self.primes))
        self.item = {p: w for w, p in self.prime.items()}
        self._chunks = [
            self.primes[i : i + chunk] for i in range(0, len(self.primes), chunk)
        ]
        self._products = [prod(c) for c in self._chunks]

    def __len__(self) -> int:
        return len(self.prime)

    def factor(self, D: int) -> list:
        """Dictionary primes dividing D (each found once; D need not be squarefree)."""
        found = []
        for c, P in zip(self._chunks, self._products):
            if gcd(D, P) > 1:
                found += [p for p in c if D % p == 0]
        return found
