"""
rhind — exact vector-symbolic memory from partial fractions.

A memory holding facts key → value is one reduced fraction,

    F = Σ v_q / q  (mod 1)  =  N / D,

with keys distinct primes q and values residues 1 ≤ v < q. Recall is one
modular inversion, absence is q ∤ D, merge and delete are + and −, and the
denominator makes value queries, analogy and role agreement one
subtraction each. Pure Python, exact integers only, no dependencies.

Named after the Rhind Mathematical Papyrus, whose 2/n table splits
fractions into sums of distinct unit fractions; recall here is the same
problem with primes as the denominators.
"""

from rhind.dictionary import PrimeDictionary, residue
from rhind.memory import ExactMemory
from rhind.primes import is_prime, odd_primes

__all__ = ["ExactMemory", "PrimeDictionary", "residue", "is_prime", "odd_primes"]
