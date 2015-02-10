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


mats = ["sglass",
        "sbrick",
        "glass",
        "grout",
        "sand",
        "gravel",
        "clay"]
mat_vars = ["_w", "_n", "_h", "_e"]
variables = it.product(mats, mat_vars)
variables = ["".join(x) for x in variables]
indices = dict(zip(variables, it.count(0)))

addeq(1., [("sglass_w", 1./5.)])
addeq(0., [("sglass_n", -1.),
           ("glass_w", 1./5.)])
addeq(0., [("sglass_n", -1.),
           ("sbrick_w", 1./4.)])
addeq(0., [("sbrick_n", -1.),
           ("grout_w", 1.)])
addeq(0., [("glass_n", -1.),
           ("sand_w", 1.)])
addeq(0., [("grout_n", -1.),
           ("sand_w", 1.)])
addeq(0., [("grout_n", -1.),
           ("clay_w", 1.)])
addeq(0., [("grout_n", -1.),
           ("gravel_w", 1.)])

for mat in mats:
    addeq(0, [(mat + "_w", -1.),
              (mat + "_n", 1.),
              (mat + "_h", 1.),
              (mat + "_e", -1)])


counts = [("sglass", 0.),
          ("sbrick", 0.),
          ("glass", 0.),
          ("grout", 0.),
          ("sand", 0.),
          ("gravel", 0.),
          ("clay", 0.)]

for mat,count in counts:
    addeq(count, [(mat + "_h", 1.)])

for mat in mats:
    addineq(0., [(mat + "_w", -1.)])
    addineq(0., [(mat + "_e", -1.)])

overages = [("sglass", 1.),
            ("sbrick", 1.),
            ("glass", 1.),
            ("grout", 1.),
            ("sand", 1.),
            ("gravel", 1.),
            ("clay", 1.)]

c_rows = [0] * len(variables)
for mat,cost in overages:
    c_rows[indices[mat + "_e"]] = cost
    c_rows[indices[mat + "_w"]] = cost

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

# for var in variables:
#     print("{0:20}: {1}".format(var, numbers[indices[var]]))

# v1 = "sglass_n"
# for line in A_rows:
#     if line[indices[v1]] != 0:
#         print()
#         for v2 in variables:
#             if line[indices[v2]] != 0:
#                 print("{0:20}: {1}".format(v2, line[indices[v2]]))
            

for mat in mats:
    print("{0:8}: want {1:5}, have {2:5}, so need {3:5} and {4:5} extra".format(
        mat,
        numbers[indices[mat + "_w"]],
        numbers[indices[mat + "_h"]],
        numbers[indices[mat + "_n"]],
        numbers[indices[mat + "_e"]]
    ))
