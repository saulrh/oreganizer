#!/usr/bin/env python3

from cvxopt import spmatrix, matrix, solvers
import itertools as it

# i is rows, j is columns

A_x = []
A_i = []
A_j = []

G_x = []
G_i = []
G_j = []

h_dict = dict()
c_dict = dict()
b_dict = dict()

eqrows = dict()
ineqrows = dict()

def addeq(name, const, terms):
    eqrows[name] = len(eqrows)
    for var, coeff in terms:
        A_i.append(eqrows[name])
        A_j.append(indices[var])
        A_x.append(coeff)
    b_dict[eqrows[name]] = const

def addineq(name, const, terms):
    ineqrows[name] = len(ineqrows)
    for var, coeff in terms:
        G_i.append(ineqrows[name])
        G_j.append(indices[var])
        G_x.append(coeff)
    h_dict[ineqrows[name]] = const

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

# our final dict: maps variable names to their columns
indices = dict(zip(variables, it.count(0)))

addeq("sglass top",
      1., [("sglass_w", 1./5.)])
addeq("sglass-n glass",
      0., [("sglass_n", -1.),
           ("glass_w", 1./5.)])
addeq("sglass-n sbrick",
      0., [("sglass_n", -1.),
           ("sbrick_w", 1./4.)])
addeq("sbrick-n grout",
      0., [("sbrick_n", -1.),
           ("grout_w", 1.)])
addeq("glass-n sand",
      0., [("glass_n", -1.),
           ("sand_w", 1.)])
addeq("grout-n sand",
      0., [("grout_n", -1.),
           ("sand_w", 1.)])
addeq("grout-n clay",
      0., [("grout_n", -1.),
           ("clay_w", 1.)])
addeq("grout-n gravel",
      0., [("grout_n", -1.),
           ("gravel_w", 1.)])

for mat in mats:
    addeq(mat + "-balance",
          0, [(mat + "_w", -1.),
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
    addeq(mat + "-have",
          count, [(mat + "_h", 1.)])

for mat in mats:
    addineq(mat + "-w pos",
            0., [(mat + "_w", -1.)])
    addineq(mat + "-e pos",
            0., [(mat + "_e", -1.)])

overages = [("sglass", 1.),
            ("sbrick", 1.),
            ("glass", 1.),
            ("grout", 1.),
            ("sand", 1.),
            ("gravel", 1.),
            ("clay", 1.)]

for mat,cost in overages:
    c_dict[indices[mat + "_e"]] = cost
    c_dict[indices[mat + "_w"]] = cost

h_row = [0] * len(ineqrows)
for idx, val in h_dict.items():
    h_row[idx] = val

b_row = [0] * len(eqrows)
for idx, val in b_dict.items():
    b_row[idx] = val

c_row = [0] * len(variables)
for idx, val in c_dict.items():
    c_row[idx] = val


c = matrix(c_row)
b = matrix(b_row)
G = spmatrix(G_x, G_i, G_j)
A = spmatrix(A_x, A_i, A_j)
h = matrix(h_row)

print(repr(h))

sol = solvers.lp(c, G, h, A, b)

numbers = [round(x, 3) for x in sol['x']]
for mat in mats:
    print("{0:8}: want {1:5}, have {2:5}, so need {3:5} and {4:5} extra".format(
        mat,
        numbers[indices[mat + "_w"]],
        numbers[indices[mat + "_h"]],
        numbers[indices[mat + "_n"]],
        numbers[indices[mat + "_e"]]
    ))
