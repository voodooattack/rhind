import random
from itertools import combinations

import pytest

from rhind import AdicMemory, Schema, decode_path, encode_path

_rng = random.Random(42)
SCHEMA = Schema({5: 4, 7: 3, 11: 2, 13: 4, 101: 1})


def _vals():
    return {q: _rng.randrange(m) for q, m in SCHEMA.modulus.items()}


def _depth(a, b, q, k):
    j = 0
    while j < k and a % q == b % q:
        a, b, j = a // q, b // q, j + 1
    return j


def test_get_round_trips_every_value_including_zero():
    for _ in range(300):
        vals = _vals()
        mem = AdicMemory.build(vals, SCHEMA)
        assert {q: mem.get(q) for q in vals} == vals


def test_agreement_is_the_shared_trailing_digits_for_every_key_at_once():
    for _ in range(500):
        vals = _vals()
        mem = AdicMemory.build(vals, SCHEMA)
        x = _rng.randrange(10**6)
        want = {
            q: _depth(v, x % SCHEMA.modulus[q], q, k)
            for (q, k), v in zip(SCHEMA.precision.items(), vals.values())
        }
        assert mem.agreement(x) == want


def test_agreement_with_another_memory_and_near():
    for _ in range(300):
        a, b = _vals(), _vals()
        A, B = AdicMemory.build(a, SCHEMA), AdicMemory.build(b, SCHEMA)
        want = {q: _depth(a[q], b[q], q, k) for q, k in SCHEMA.precision.items()}
        assert A.agreement_with(B) == want == B.agreement_with(A)
        assert A.agreement_with(A) == SCHEMA.precision  # full depth = equal
    mem = AdicMemory.build({5: encode_path([1, 2, 3, 4], 5)}, SCHEMA)
    assert 5 in mem.near(encode_path([1, 2, 0, 0], 5), 2)
    assert 5 not in mem.near(encode_path([1, 2, 0, 0], 5), 3)


def test_depth_is_an_ultrametric():
    q, k = 7, 3
    vals = [_rng.randrange(q**k) for _ in range(60)]
    for a, b, c in combinations(vals, 3):
        dab, dbc, dac = (_depth(x, y, q, k) for x, y in ((a, b), (b, c), (a, c)))
        assert dac >= min(dab, dbc)  # q^(-depth) obeys the strong triangle inequality


def test_merge_adds_values_mod_q_to_the_k():
    for _ in range(200):
        a, b = _vals(), _vals()
        M = AdicMemory.build(a, SCHEMA) + AdicMemory.build(b, SCHEMA)
        assert {q: M.get(q) for q in a} == {
            q: (a[q] + b[q]) % SCHEMA.modulus[q] for q in a
        }
        assert M - AdicMemory.build(b, SCHEMA) == AdicMemory.build(a, SCHEMA)


def test_paths_encode_ancestors_in_the_low_digits():
    assert encode_path([3, 0, 2], 5) == 3 + 0 * 5 + 2 * 25
    assert decode_path(encode_path([3, 0, 2, 4], 5), 5, 4) == [3, 0, 2, 4]
    a, b = encode_path([1, 4, 2, 0], 5), encode_path([1, 4, 3, 3], 5)
    assert _depth(a, b, 5, 4) == 2  # two shared ancestor levels
    with pytest.raises(ValueError):
        encode_path([5], 5)


def test_schema_and_values_are_validated():
    with pytest.raises(ValueError, match="not prime"):
        Schema({15: 2})
    with pytest.raises(ValueError):
        Schema({5: 0})
    with pytest.raises(ValueError):
        AdicMemory.build({5: 625}, SCHEMA)
    with pytest.raises(KeyError):
        AdicMemory.build({3: 1}, SCHEMA)
    with pytest.raises(ValueError):
        AdicMemory.build({5: 1}, SCHEMA).agreement_with(
            AdicMemory.build({5: 1}, Schema({5: 4}))
        )
