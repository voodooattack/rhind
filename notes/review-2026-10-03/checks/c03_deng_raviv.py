"""Re-derive the Deng–Raviv size with the RS dimension as their paper defines subcodes
(dim C_i = log_p |U_i| over F_p, so the F_{p^m}-dimension of the bound pair need not be
ceil(log_N U) + ceil(log_N V)). Same noiseless bound u <= floor((N-1)/(K-1)), n = N^2,
entries charged ceil(log2 C(u+p-1, p-1)). Exact integers."""

from math import comb

U, V = 20000, 1000
exact = {10: 327, 30: 990, 100: 3212, 300: 9720, 1000: 32396, 3000: 97587}


def prime_powers(limit):
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\0\0"
    for i in range(2, limit + 1):
        if sieve[i]:
            sieve[i * i :: i] = bytearray(len(sieve[i * i :: i]))
            N, m = i, 1
            while N <= limit:
                yield i, m, N
                N, m = N * i, m + 1


def clog(base, x):
    k, c = 0, 1
    while c < x:
        k, c = k + 1, c * base
    return k


def best(u, mode, nmax=1 << 14):
    out = None
    for p, m, N in prime_powers(nmax):
        if mode == "paper":
            K = clog(N, U) + clog(N, V)
        else:  # F_p-subcodes: total F_p dimension, packed into F_{p^m} symbols
            K = -(-(clog(p, U) + clog(p, V)) // m)
        if K < 2 or (N - 1) // (K - 1) < u:
            continue
        bits = N * N * (comb(u + p - 1, p - 1) - 1).bit_length()
        if out is None or bits < out[0]:
            out = (bits, f"{p}^{m}", K)
    return out


for u, ex in exact.items():
    a = best(u, "paper")
    b = best(u, "subcode")
    print(
        f" K={u:5d} paper: {a[0]:>10d} bits N={a[1]:>5s} k={a[2]} ({a[0]//ex}x)   F_p-subcodes: {b[0]:>10d} bits N={b[1]:>5s} k={b[2]} ({b[0]//ex}x)"
    )
