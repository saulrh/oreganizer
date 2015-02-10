#!/usr/bin/env python3

from cvxopt import matrix, solvers
import itertools as it
import tabulate

A_rows = []
b_rows = []
G_rows = []
h_rows = []
c_rows = []

def buildrow(terms):
    row = [0] * len(indices)
    for var,coeff in terms:
        row[indices[var]] = coeff
    return row

def addeq(const, terms):
    row = buildrow(terms)
    A_rows.append(row)
    b_rows.append(const)

def addineq(const, terms):
    row = buildrow(terms)
    G_rows.append(row)
    h_rows.append(const)


mats = ["searedglass",
        "searedbrick",
        "glass",
        "grout",
        "sand",
        "gravel",
        "clay"]
mat_vars = ["_want", "_need", "_have", "_extra"]
variables = it.product(mats, mat_vars)
variables = ["".join(x) for x in variables]
indices = dict(zip(variables, it.count(0)))

addeq(1., [("searedglass_want", 1.)])
addeq(0., [("searedglass_need", -1.),
           ("searedbrick_want", 1./4.),
           ("glass_want", 1./5.)])
addeq(0., [("searedbrick_need", -1.),
           ("grout_want", 1.)])
addeq(0., [("glass_need", -1.),
           ("sand_want", 1.)])
addeq(0., [("grout_need", -1.),
           ("sand_want", 1.),
           ("gravel_want", 1.),
           ("clay_want", 1.)])

for mat in mats:
    addeq(0, [(mat + "_want", -1.),
              (mat + "_need", 1.),
              (mat + "_have", 1.),
              (mat + "_extra", -1.)])


counts = [("searedglass", 0.),
          ("searedbrick", 0.),
          ("glass", 0.),
          ("grout", 0.),
          ("sand", 0.),
          ("gravel", 0.),
          ("clay", 0.)]

for mat,count in counts:
    addeq(count, [(mat + "_have", 1.)])
    

for mat in mats:
    addineq(0., [(mat + "_want", -1.)])
    addineq(0., [(mat + "_extra", -1.)])

overages = [("searedglass", 1.),
            ("searedbrick", 1.),
            ("glass", 1.),
            ("grout", 1.),
            ("sand", 1.),
            ("gravel", 1.),
            ("clay", 1.)]

c_rows = [0] * len(variables)
for mat,cost in overages:
    c_rows[indices[mat + "_extra"]] = cost

print()
print(tabulate.tabulate(A_rows))

print()
print(tabulate.tabulate(G_rows))

print()
print(b_rows)
print(h_rows)
print()
print(c_rows)

c = matrix(c_rows)
b = matrix(b_rows)
G = matrix(G_rows).T
A = matrix(A_rows).T
h = matrix(h_rows)


sol = solvers.lp(c, G, h, A, b)

numbers = [round(x, 3) for x in sol['x']]

for var in variables:
    print("{0:20}: {1}".format(var, numbers[indices[var]]))

v1 = "searedglass_need"
for line in A_rows:
    if line[indices[v1]] != 0:
        print()
        for v2 in variables:
            if line[indices[v2]] != 0:
                print("{0:20}: {1}".format(v2, line[indices[v2]]))
            
