"""How the 'one subtraction' operations scale with memory size, vs a plain dict scan.
Timings are integer nanoseconds (perf_counter_ns), median of 5."""

import random, time
from rhind import ExactMemory, PrimeDictionary, odd_primes


def t(f, reps=5):
    xs = []
    for _ in range(reps):
        a = time.perf_counter_ns()
        f()
        xs.append(time.perf_counter_ns() - a)
    return sorted(xs)[reps // 2]


rng = random.Random(7)
V = 1000
print(
    " K        bits   build_us  get_us  holding_us  agreeing_us  merge_us | dict_scan_us  keys(dic)_us"
)
for K in (1000, 4000, 16000, 64000):
    primes = odd_primes(K, start_after=V)
    facts = {q: rng.randrange(1, V) for q in primes}
    facts2 = dict(facts)
    for q in rng.sample(primes, K // 2):
        facts2[q] = rng.randrange(1, V)
    tb0 = time.perf_counter_ns()
    A = ExactMemory.build(facts)
    tb = time.perf_counter_ns() - tb0
    B = ExactMemory.build(facts2)
    bag = ExactMemory.key_bag(primes)
    q0 = primes[K // 2]
    x = 7
    tg = t(lambda: A.get(q0))
    th = t(lambda: A.holding(x, bag), 3)
    ta = t(lambda: A.agreeing(B), 3)
    tm = t(lambda: A + B, 3)
    ts = t(lambda: [q for q, v in facts.items() if v == x])
    dic = PrimeDictionary(range(K), primes=primes)
    tk = t(lambda: dic.factor(A.holding(x, bag)), 1)
    assert A.holding(x, bag) == __import__("math").prod(
        q for q, v in facts.items() if v == x
    )
    print(
        f" {K:6d} {A.bits():9d} {tb//1000:9d} {tg//1000:7d} {th//1000:11d} {ta//1000:12d} {tm//1000:9d} | {ts//1000:12d} {tk//1000:12d}"
    )
