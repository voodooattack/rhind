import random

from rhind import PrimeDictionary, is_prime, odd_primes

_rng = random.Random(124)
ITEMS = [f"w{i}" for i in range(3000)]
DIC = PrimeDictionary(ITEMS)


def test_primes():
    ps = odd_primes(200)
    assert ps[:5] == [3, 5, 7, 11, 13] and all(is_prime(p) for p in ps)
    assert odd_primes(3, start_after=103) == [107, 109, 113]
    assert is_prime(2**31 - 1) and not is_prime(
        2**31 - 3
    )  # Mersenne prime; 2^31−3 = 5·429496729
    assert [n for n in range(100) if is_prime(n)] == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
        31,
        37,
        41,
        43,
        47,
        53,
        59,
        61,
        67,
        71,
        73,
        79,
        83,
        89,
        97,
    ]


def test_factor_finds_exactly_the_dictionary_primes():
    ps = _rng.sample(DIC.primes, 30)
    D = 1
    for p in ps:
        D *= p
    assert sorted(DIC.factor(D * 2**5)) == sorted(ps)


def test_is_prime_rejects_the_twelve_base_pseudoprime():
    """ψ₁₂ fools Miller–Rabin with bases 2 … 37; base 41 catches it."""
    psi12 = 318665857834031151167461
    assert psi12 == 399165290221 * 798330580441
    assert not is_prime(psi12)
    assert is_prime(399165290221) and is_prime(798330580441)
