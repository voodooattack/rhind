"""Prime generation. Exact; deterministic."""

from math import isqrt

_SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


def odd_primes(n: int, start_after: int = 2) -> list:
    """The first n odd primes greater than `start_after`, by sieve."""
    limit = max(64, start_after * 2)
    while True:
        sieve = bytearray([1]) * (limit + 1)
        sieve[0:2] = b"\x00\x00"
        for i in range(2, isqrt(limit) + 1):
            if sieve[i]:
                sieve[i * i :: i] = bytearray(len(sieve[i * i :: i]))
        ps = [
            i for i in range(max(3, start_after + 1), limit + 1) if sieve[i] and i % 2
        ]
        if len(ps) >= n:
            return ps[:n]
        limit *= 2


def is_prime(n: int) -> bool:
    """Miller–Rabin with the first 13 primes as bases (2 … 41).

    Deterministic, hence exact, for n < ψ₁₃ = 3,317,044,064,679,887,385,961,981
    (Sorenson and Webster, Math. Comp. 86 (2017)); above that it is a strong
    probable-prime test. The first 12 bases alone are fooled by
    ψ₁₂ = 318,665,857,834,031,151,167,461 = 399,165,290,221 · 798,330,580,441,
    which an earlier version accepted (cold review, 2026-10-04)."""
    if n < 2:
        return False
    for p in _SMALL:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _SMALL:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True
