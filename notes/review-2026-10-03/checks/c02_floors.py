"""Information floors vs the paper's 'floor', and dependence of the 1.3x ratio on U, V.
Exact integers only: ceil(log2 X) = (X-1).bit_length()."""

from math import comb, prod
import random
from rhind import ExactMemory, odd_primes


def clog2(x):  # ceil(log2 x) for integer x >= 1
    return (x - 1).bit_length()


U, V = 20000, 1000
reported = {10: 327, 30: 990, 100: 3212, 300: 9720, 1000: 32396, 3000: 97587}
print(
    "== 1. Paper 'floor' K*(15+10) vs true floor ceil(log2(C(U,K) * (V-1)^K)) (values 1..V-1)"
)
for K, ex in reported.items():
    naive = K * 25
    true = clog2(comb(U, K) * (V - 1) ** K)
    # ratio as exact fraction rounded down to 2 decimals
    r1 = 100 * ex // naive
    r2 = 100 * ex // true
    print(
        f" K={K:5d} exact={ex:6d} naive_floor={naive:6d} ({r1//100}.{r1%100:02d}x)  true_floor={true:6d} ({r2//100}.{r2%100:02d}x)"
    )

print("== 2. Sparse key-set: D bits (report) vs enumerative optimum ceil(log2 C(U,K))")
dbits = {10: 156, 100: 1620, 300: 4854, 1000: 16311, 3000: 48744, 10000: 162632}
gam = {10: 194, 100: 1324, 300: 3176, 1000: 7470, 3000: 14184, 10000: 22738}
for K in dbits:
    opt = clog2(comb(U, K))
    print(
        f" K={K:5d} D={dbits[K]:6d} gamma={gam[K]:6d} bitmap={U}  optimum={opt:6d}  -> D beats optimum? {dbits[K] < opt}"
    )

print(
    "== 3. Fraction-mode bits per fact vs naive floor at other (U, V): keys = first U primes above V"
)
rng = random.Random(1)
for U2, V2, K in [
    (20000, 1000, 300),
    (1000, 2**16, 300),
    (2**20, 2, 300),
    (2**20, 16, 300),
    (200, 200, 100),
]:
    primes = odd_primes(U2, start_after=V2)
    keys = rng.sample(primes, K)
    M = ExactMemory.build({q: rng.randrange(1, V2) for q in keys})
    naive = K * (clog2(U2) + clog2(V2))
    true = clog2(comb(U2, K) * (V2 - 1) ** K)
    r1 = 100 * M.bits() // naive
    r2 = 100 * M.bits() // true
    print(
        f" U={U2:8d} V={V2:6d} K={K}: bits={M.bits():6d}  /naive={r1//100}.{r1%100:02d}x  /true={r2//100}.{r2%100:02d}x"
    )
