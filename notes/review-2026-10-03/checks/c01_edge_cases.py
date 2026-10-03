"""Edge cases of ExactMemory against the paper's statements. Exact ints/Fractions only."""

from fractions import Fraction
from math import prod, gcd
from rhind import ExactMemory, AdicMemory, Schema


def den(F):
    return (F - (F.numerator // F.denominator)).denominator


print(
    "== 1. Prop 2 formula when Q is not a subset of R (stored key outside the bag holds x)"
)
# keys 11, 13 stored; bag R = {11} only; key 13 holds x=5 but is outside R
M = ExactMemory.build({11: 5, 13: 5})
S = ExactMemory.key_bag([11])
x = 5
d = den(M.F - x * S.F)
claimed = prod(
    q for q in {11, 13} if {11: 5, 13: 5}[q] != x
)  # Prop 2 product over Q∪R with v_q != x  -> 1
print(
    " den(F - xS) =",
    d,
    " Prop 2 predicts",
    claimed,
    " -> Prop 2 as stated is",
    d == claimed,
)
print(
    " library holding():", M.holding(x, S), "(=11, correct for 'keys in R holding x')"
)

print(
    "== 2. Analogy formula in text: role = D_B / den(F_B - xS) with an empty role in the bag"
)
B = ExactMemory.build({11: 5, 13: 7})  # role 17 empty
S = ExactMemory.key_bag([11, 13, 17])
d = den(B.F - 5 * S.F)
print(
    " D_B =",
    B.D,
    " den =",
    d,
    " D_B/den is integer?",
    B.D % d == 0,
    " Fraction:",
    Fraction(B.D, d),
)
print(" lcm form:", (B.D * S.D // gcd(B.D, S.D)) // d)

print("== 3. gcd(D_A,D_B)>1 flags shared keys, not disagreement; merge is not union")
A = ExactMemory.build({11: 5})
A2 = ExactMemory.build({11: 5})
print(" conflicts of two IDENTICAL memories:", A.conflicts(A2))
print(" (A+A).get(11) =", (A + A2).get(11), "(not 5)")
A3 = ExactMemory.build({11: 6})
print(
    " A{11:5} + A{11:6} -> key 11 present?",
    11 in (A + A3),
    " (value 11 ≡ 0 deletes the key silently)",
)

print("== 4. delete needs the exact value: subtracting the wrong value is not deletion")
M = ExactMemory.build({11: 5, 13: 7})
W = M - ExactMemory.build({11: 4})
print(" after subtracting 4/11 instead of 5/11, get(11) =", W.get(11))

print("== 5. get() with a composite query (product of two stored keys)")
M = ExactMemory.build({11: 5, 13: 7})
print(
    " get(143) =",
    M.get(143),
    " 143 in M:",
    143 in M,
    "(should be None/False: 143 is not a key)",
)
print(" get(1) =", M.get(1), " 1 in M:", 1 in M)

print("== 6. holding() with x >= a key (precondition not enforced)")
M = ExactMemory.build({11: 5, 13: 7})
S = ExactMemory.key_bag([11, 13])
print(
    " holding(16) =",
    M.holding(16, S),
    "(reports key 11 'holding' 16 because 16 ≡ 5 mod 11)",
)

print("== 7. empty memory")
E = ExactMemory()
print(
    " N,D =",
    E.N,
    E.D,
    " get(11)",
    E.get(11),
    " holding(3, bag{11,13}) =",
    E.holding(3, ExactMemory.key_bag([11, 13])),
    " agreeing(E,E) =",
    E.agreeing(ExactMemory()),
)
print(
    " agreeing of two empty memories is 1 (no keys); agreeing(E, A{11:5}) =",
    E.agreeing(A),
)

print("== 8. analogy when B holds x at two roles")
A = ExactMemory.build({11: 1, 13: 2})
B = ExactMemory.build({11: 5, 13: 5})
print(
    " analogy ->",
    A.analogy(B, 5, ExactMemory.key_bag([11, 13])),
    "(None: ambiguity silently -> None, not stated in paper)",
)

print("== 9. Adic: ultrametric 'agree to depth min(i,j)' is only a lower bound")
sch = Schema({5: 3})
a = AdicMemory.build({5: 7}, sch)
b = AdicMemory.build({5: 7}, sch)
c = AdicMemory.build({5: 2}, sch)
print(
    " depth(a,c) =",
    a.agreement_with(c)[5],
    " depth(b,c) =",
    b.agreement_with(c)[5],
    " depth(a,b) =",
    a.agreement_with(b)[5],
    "(> min)",
)

print(
    "== 10. Adic: a value divisible by q is indistinguishable from a lower-precision key without the schema"
)
F1 = Fraction(5, 25)  # value 5 at precision 2
print(
    " 5/25 reduces to", F1, "; value 0 makes the key vanish entirely:", Fraction(0, 25)
)
