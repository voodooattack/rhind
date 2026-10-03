"""Prime generation. Exact; deterministic."""

from math import isqrt

_SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


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
    """Deterministic Miller–Rabin for n < 3.3·10²⁴ (bases: the first 12 primes)."""
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
