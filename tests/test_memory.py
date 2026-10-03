import random
from fractions import Fraction

import pytest

from rhind import ExactMemory, PrimeDictionary

_rng = random.Random(129)
V = 500
DIC = PrimeDictionary(range(3000), start_after=V)  # keys above the value range
KEYS = DIC.primes


def _facts(k):
    return {q: _rng.randrange(1, V) for q in _rng.sample(KEYS, k)}


def test_recall_is_exact_and_absent_keys_are_absent():
    for k in (0, 1, 7, 100, 1000):
        facts = _facts(k)
        mem = ExactMemory.build(facts)
        assert all(mem.get(q) == v for q, v in facts.items())
        others = [q for q in _rng.sample(KEYS, 300) if q not in facts]
        assert all(mem.get(q) is None and q not in mem for q in others)


def test_keys_and_items_round_trip_over_the_dictionary():
    facts = _facts(200)
    mem = ExactMemory.build(facts)
    assert mem.keys(DIC) == sorted(facts) and mem.items(DIC) == facts


def test_merge_and_delete_are_inverse():
    a, b = _facts(150), _facts(150)
    b = {q: v for q, v in b.items() if q not in a}
    A, B = ExactMemory.build(a), ExactMemory.build(b)
    assert A + B == ExactMemory.build({**a, **b})
    assert (A + B) - B == A and (A + B) - A == B
    assert (A - A) == ExactMemory() and ExactMemory().D == 1


def test_random_operation_sequence_matches_a_rebuild():
    truth, mem = {}, ExactMemory()
    for _ in range(1500):
        r = _rng.random()
        if r < 0.5 or not truth:
            q = _rng.choice(KEYS)
            if q not in truth:
                truth[q] = _rng.randrange(1, V)
                mem += ExactMemory.build({q: truth[q]})
        elif r < 0.8:
            q = _rng.choice(sorted(truth))
            mem -= ExactMemory.build({q: truth.pop(q)})
        else:
            batch = {
                q: _rng.randrange(1, V) for q in _rng.sample(KEYS, 4) if q not in truth
            }
            truth.update(batch)
            mem += ExactMemory.build(batch)
    assert mem == ExactMemory.build(truth)
    assert all(mem.get(q) == v for q, v in truth.items())


def test_shared_keys_add_mod_q_and_conflicts_names_them():
    q1, q2, q3 = KEYS[:3]
    A = ExactMemory.build({q1: 5, q2: 7})
    B = ExactMemory.build({q2: 11, q3: 2})
    assert A.conflicts(B) == q2
    assert (A + B).get(q2) == 18  # arithmetic, not a union
    C = ExactMemory.build({q2: q2 - 7})  # cancels A's value at q2
    assert q2 not in (A + C) and (A + C).get(q1) == 5


def test_project_extracts_exactly_the_sub_memory():
    facts = _facts(300)
    mem = ExactMemory.build(facts)
    sub = _rng.sample(sorted(facts), 40) + _rng.sample(KEYS, 20)  # some absent
    want = {q: facts[q] for q in sub if q in facts}
    assert mem.project(sub) == ExactMemory.build(want)
    assert mem.project(sub) + mem.project([q for q in facts if q not in want]) == mem


def test_values_must_be_nonzero_residues():
    with pytest.raises(ValueError):
        ExactMemory.build({KEYS[0]: 0})
    with pytest.raises(ValueError):
        ExactMemory.build({KEYS[0]: KEYS[0]})


def test_keys_need_not_come_from_a_dictionary():
    from rhind import is_prime

    def key(path: str) -> int:  # any deterministic path → prime
        q = (1 << 39) | (hash(("salt", path)) & ((1 << 39) - 1)) | 1
        while not is_prime(q):
            q += 2
        return q

    facts = {
        key(f"rec{i}.role{j}"): _rng.randrange(1, 10**6)
        for i in range(30)
        for j in range(5)
    }
    mem = ExactMemory.build(facts)
    assert all(mem.get(q) == v for q, v in facts.items())
    assert mem.get(key("rec0.role9")) is None


# ── holistic operations (proof 002) ──────────────────────────

ROLES = KEYS[:20]
BAG = ExactMemory.key_bag(ROLES)


def _record(rng):
    return {q: rng.randrange(1, V) for q in ROLES}


def test_holding_identity_den_of_F_minus_xS():
    rng = random.Random(1300)
    for _ in range(300):
        facts = _record(rng)
        x = rng.choice(list(facts.values()) + [rng.randrange(1, V)])
        want = 1
        for q, v in facts.items():
            if v == x:
                want *= q
        assert ExactMemory.build(facts).holding(x, BAG) == want


def test_analogy_reads_the_value_at_the_matching_role():
    rng = random.Random(1301)
    for _ in range(200):
        a, b = _record(rng), _record(rng)
        q = rng.choice(ROLES)
        if list(b.values()).count(b[q]) != 1:
            continue  # x must sit at one role in b
        assert ExactMemory.build(a).analogy(ExactMemory.build(b), b[q], BAG) == a[q]
    assert (
        ExactMemory.build(_record(rng)).analogy(
            ExactMemory.build({q: 1 for q in ROLES}), V + 5, BAG
        )
        is None
    )


def test_agreeing_is_the_product_of_equal_roles():
    rng = random.Random(1302)
    for _ in range(200):
        a = _record(rng)
        b = {q: (a[q] if rng.random() < 0.4 else rng.randrange(1, V)) for q in ROLES}
        want = 1
        for q in ROLES:
            if a[q] == b[q]:
                want *= q
        assert ExactMemory.build(a).agreeing(ExactMemory.build(b)) == want
    # one-sided keys never agree
    assert (
        ExactMemory.build({KEYS[0]: 3}).agreeing(ExactMemory.build({KEYS[1]: 3})) == 1
    )


def test_rebind_moves_one_value_and_nothing_else():
    rng = random.Random(1303)
    spare = KEYS[30]
    for _ in range(100):
        facts = _record(rng)
        q = rng.choice(ROLES)
        moved = ExactMemory.build(facts).rebind(q, spare)
        want = dict(facts)
        want[spare] = want.pop(q)
        assert moved == ExactMemory.build(want)
    with pytest.raises(KeyError):
        ExactMemory.build({KEYS[0]: 2}).rebind(KEYS[1], spare)


def test_holding_with_empty_roles_in_the_bag():
    """A schema bag may name roles a record leaves empty (value 0): those
    roles hold 0, not x, and must not corrupt the answer."""
    rng = random.Random(41)
    keys = DIC.primes[:200]
    bag = ExactMemory.key_bag(keys)
    for _ in range(300):
        vals = {q: rng.choice([0, 0, rng.randrange(1, V)]) for q in keys}
        mem = ExactMemory.build({q: v for q, v in vals.items() if v})
        x = rng.randrange(1, V)
        truth = 1
        for q, v in vals.items():
            if v == x:
                truth *= q
        assert mem.holding(x, bag) == truth


def test_composite_keys_are_refused():
    """Each failure mode of a composite key (see build's docstring) is refused
    at the door rather than stored as a wrong memory."""
    for facts in ({15: 5, 7: 3}, {15: 4}, {6: 1, 10: 1}, {9: 2}, {1: 0}):
        with pytest.raises(ValueError, match="not prime"):
            ExactMemory.build(facts)
    with pytest.raises(ValueError, match="not prime"):
        ExactMemory.key_bag([1009, 1011])  # 1011 = 3 · 337
    mem = ExactMemory.build({1009: 42})
    with pytest.raises(ValueError, match="not prime"):
        mem.rebind(1009, 1015)  # 1015 = 5 · 7 · 29
    assert mem.rebind(1009, 1013).get(1013) == 42
