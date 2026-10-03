"""(Role-wise clean-ups use that role's 100 fillers, as proof 005 does.)
Proof 002 gives MAP a one-shot mapping vector (m^2 cross terms) for analogy, while the
exact memory does two steps (find the role holding x, then read A there). Give MAP the same
two-step algorithm: clean up x*B against the role codebook, then clean up role*A against the
fillers. Same setting as proof 002: m roles, 100 fillers per role, bipolar MAP-I, n = 10,000.
Integer arithmetic only (numpy int64)."""

import numpy as np, random

VF, TRIALS = 100, 100
rng = random.Random(130)
nr = np.random.default_rng(130)
for m in (10, 30, 100):
    for n in (10000, 2000):
        roles = nr.choice(np.array([-1, 1], dtype=np.int64), size=(m, n))
        fill = nr.choice(np.array([-1, 1], dtype=np.int64), size=(m * VF, n))
        rec = lambda fs: sum(roles[r] * fill[f] for r, f in enumerate(fs))
        one = two = agree_onestep = agree_twostep = 0
        for _ in range(TRIALS):
            a = [r * VF + rng.randrange(VF) for r in range(m)]
            b = [
                r * VF + (a[r] - r * VF + 1 + rng.randrange(VF - 1)) % VF
                for r in range(m)
            ]
            A, B = rec(a), rec(b)
            r = rng.randrange(m)
            x = b[r]
            one += int((fill @ (fill[x] * A * B)).argmax()) == a[r]
            rhat = int((roles @ (fill[x] * B)).argmax())
            two += (
                rhat * VF
                + int((fill[rhat * VF : (rhat + 1) * VF] @ (roles[rhat] * A)).argmax())
                == a[r]
            )
            # agreeing roles: per-role clean-up of both records (the exact memory returns the set)
            c = [r * VF + rng.randrange(VF) for r in range(m)]
            d = list(c)
            for i in rng.sample(range(m), rng.randint(0, m)):
                d[i] = i * VF + rng.randrange(VF)
            C, Dv = rec(c), rec(d)
            want = {i for i in range(m) if c[i] == d[i]}
            got = {
                i
                for i in range(m)
                if int((fill[i * VF : (i + 1) * VF] @ (roles[i] * C)).argmax())
                == int((fill[i * VF : (i + 1) * VF] @ (roles[i] * Dv)).argmax())
            }
            agree_twostep += got == want
            agree_onestep += round(int(C @ Dv) / n) == len(want)
        print(
            f" m={m:3d} n={n:5d}: analogy one-shot {one}/{TRIALS}, two-step {two}/{TRIALS};"
            f" agreeing count one-shot {agree_onestep}/{TRIALS}, agreeing SET via per-role clean-up {agree_twostep}/{TRIALS}"
        )
