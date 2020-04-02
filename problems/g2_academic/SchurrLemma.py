from pycsp3 import *

"""
 Problem 015 on CSPLib

 The variant 'mod' corresponds to the one proposed in [Bessiere Meseguer Freuder Larrosa, On forward checking for non-binary constraint satisfaction, 2002].
"""

n, d = data  # n is the number of balls -- d is the number of boxes

# x[i] is the box where the ith ball is put
x = VarArray(size=n, dom=range(d))

if not variant():
    satisfy(
        NValues(x[i], x[j], x[k]) > 1 for (i, j, k) in product(range(n), repeat=3) if i < j and i + 1 + j == k
    )
elif variant("mod"):
    satisfy(
        AllDifferent(x[i], x[j], x[k]) for (i, j, k) in product(range(n), repeat=3) if i < j and i + 1 + j == k
    )
