#!/usr/bin/env python3

print()

# we're using cvxopt, a python package for convex optimization. Which is ludicrous overkill, but it
# works and it's efficient and that's what's important.
from cvxopt import spmatrix, matrix, solvers
import itertools as it

################################################################################
## THE BIG IDEA ################################################################
################################################################################

# 
# Math:
# 
# we use cvxopt's linear programming solver, which takes
# c, G, h, A, and b to form a linear program:
# 
# minimize c^T x subject to
# 
# Gx + s = h
# Ax = b
# s >= 0
# 
# that is, G is a matrix with coefficients for a series of linear inequalities with coefficients G
# and constants h, and A and b are similarly coefficients and constants for a series of linear
# equalities.
# 
# We construct our problem with variables representing how many of each material we want, already
# have, need to make. For each material, we have a few things:
# 
# First, the core relation: 0 = mat_have + mat_need - mat_want - mat_extra. The number that we have
# (mat_have) and that we'll need to make (mat_need) equals the number we want total (mat_want) and
# the number we'll make but not use (mat_extra). Inputs equal outputs. We call this equation
# mat-balance.
# 
# Second, the amount of that material that we already have. n = mat_have, where n is the quantity
# that the user already has. We call this equation mat-have.
# 
# Third, a pair of inequalities that keep things positive. 0 >= -mat_extra and 0 >= -mat_want. We
# can't want a negative quantity of something, and we keep extra positive so it doesn't get used by
# the optimizer to trivially satisfy our needs (and so the system doesn't explode off to negative
# infinity as it tries to minimize our costs). We call these inequalities mat-w-pos and mat-e-pos.
# 
# Fourth, the equation that determines how many resources go into the construction of each one of
# the material. Because each material will be required for multiple other constructions and we're
# using equalities, though, we have an intermediate stage where we want a bunch of variables that
# get added up to form the total "want" for the dependent material. for each dep in the
# dependencies list, 0 = -dep_required * mat_need + mat_dep_want, where dep_required is how many of
# them we need and mat_dep_want will be how many of dep we need to make the mats we need. In other
# words, if we need 5 glass to make 1 searedglass, our equation will be 0 = -5 * searedglass_want +
# * searedglass_searedbrick_want. This works out to the number of searedglass we make being 1/5th
# the number of seared bricks we want, so this works. We call the equation relating material mat to
# dependency dep mat-dep-want.
# 
# Fifth, the summation equation that puts all the mat-dep-want variables together into the ultimate
# mat-want total. 0 = -mat_want + sum(invdep, invdep_mat_want), where we add up the count
# (invdep_mat_want) for each material that depends on this material (invdep). We call this equation
# mat-wantsum.
# 
# We also have several global equations.
# 
# First, the inequalities which add the player's ultimate goals to the system. For each material
# that we want, we add an inequality -count >= -mat_want, where we want to make at least count of
# material mat. The formulation of the convex optimization problem is Gx + s = h where s is
# arbitrary, so individual equations can only be of the form const >= coeffs .* terms, so we have
# to multiply everything by -1 to get mat_want >= count.
# 
# Second, and this is the only really disgusting part of this system, we have a number of
# automatically added intermediate inequalities that we use to take care of building tools and the
# like. For example, pulverized coal can only be made using a pulverizer, but a single pulverizer
# can manufacture an arbitrarily large amount of pulverized coal once it's been built. So our
# problem is not *actually* convex optimization, but something closer to satisfiability. Either way
# it's bad. So we implement something that feels a little bit like column generation. When we have
# materials that require dependencies but doesn't consume them in construction, which we call
# "requires" as opposed to "consumes", we run the optimizer entirely disregarding these
# dependencies: they might as well not exist. Then, after the optimizer has found a solution
# disregarding construction requirements, we look through our list of materials, find all of the
# dependencies that have require dependencies that won't be created in sufficient quantity, and
# create new inequalities for each dependency specifying that we want some of them. We then rerun
# the optimizer. We repeat this optimization-addition process until we find have no materials which
# are part of a require dependency and are insufficiently wanted.
# 
# Finally, we have the objective function, which is the thing that our optimizer will be
# minimizing. We currently set this to minimize extra production: c = sum(mat, mat_cost *
# mat_extra), where we sum up over all materials (mat) the cost (mat_cost) of producing extra of
# that material (mat_extra).


# 
# Inputs:
# 
# mats is a list of string names of materials that our system will be using.
# 
# counts is a dictionary mapping mats to how many of that mat the user already has.
# 
# overages is a dictionary mapping mats to how much it costs to have extra of that material. It's
# unlikely that this will ever really make a difference, but it's there in case you have a material
# with multiple recipes, or in case you want something to be "free". For example, cobble is easy to
# obtain in extreme quantities once you can build a cobble generator, so we might set its overage
# cost to be near-zero; then the system would recognize that, if given the choice, it'd be better
# to spend 1e5 cobble than it would be to spend 1 iron ingot.
# 
# goals is a dictionary mapping mats to how many of those mats we eventually want to make.
# 
# dependencies is the meat of the system; it is a dictionary mapping materials to dictionaries that
# map dependencies to counts: mat => { string => int }. This is where you add your recipes to the
# system. For example, the recipe for a piston:
# 
# {"piston": {
#     "cobblestone": 4,
#     "planks": 3,
#     "iron ingot": 1,
#     "redstone dust": 1
# }
# 

################################################################################
## DECLARATIONS ################################################################
################################################################################

mats = ["sglass",
        "sbrick",
        "glass",
        "grout",
        "sand",
        "gravel",
        "clay"
]

counts = [("sglass", 0),
          ("sbrick", 0),
          ("glass", 0),
          ("grout", 0),
          ("sand", 0),
          ("gravel", 0),
          ("clay", 0)
]


overages = [("sglass", 1),
            ("sbrick", 1),
            ("glass", 1),
            ("grout", 1),
            ("sand", 1),
            ("gravel", 1),
            ("clay", 1)
]

goals = {
    "sglass": 5
}

dependencies = {
    "sglass": {
        "glass": 5,
        "sbrick": 4
    },
    "sbrick": {
        "grout": 1
    },
    "glass": {
        "sand": 1
    },
    "grout": {
        "sand": 1,
        "gravel": 1,
        "clay": 1
    }
}

################################################################################
## VARIABLES ###################################################################
################################################################################

# lists to store the values in our matrices. i is rows, j is columns. Because we're using sparse
# matrices, instead of actually building matrices directly we build lists of (x, i, j) triplets and
# then the sparse matrix constructor consumes those to build the matrix. Annoyingly, spmatrix
# constructor doesn't /actually/ take tuples, but instead takes similarly-indexed lists. Which is
# super annoying.

# The A matrix stores the coefficients in equality relations.
A_x = []
A_i = []
A_j = []

# The G matrix stores the coefficients in inequality relations.
G_x = []
G_i = []
G_j = []

# h stores the constant terms in inequality relations. b stores the constant terms in equality
# relations.
h_dict = dict()
b_dict = dict()

# c stores the coefficients for our objective function.
c_dict = dict()

# these dictionaries map equation names to the rows in the matrices which encode those equations.
eqrows = dict()
ineqrows = dict()

# we define the variables that we'll be using: for each material, a "_wants", "_needs", "_have",
# and "_extra" var.
mat_vars = ["_w", "_n", "_h", "_e"]
variables = it.product(mats, mat_vars)
variables = ["".join(x) for x in variables]

# maps the name of variable to the column in the various matrices that store that variable's
# coefficients.
indices = dict(zip(variables, it.count(0)))

# dictionary mapping mats to lists of variables in each mat's wantsum equation.
revdeps = dict()

################################################################################
## PROBLEM DEFINITION ##########################################################
################################################################################

########################################
# some nice clean functions to help us add human-readable chunks of the problem to the matrices.

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

def adddep(mat, dep, count):
    var = mat + "_" + dep + "_w"
    variables.append(var)
    indices[var] = len(variables) - 1
    addeq(mat + "-" + dep + "-w",
          0,
          [(mat + "_n", -count),
           (var, 1)])
    if dep not in revdeps:
        revdeps[dep] = []
    revdeps[dep].append(var)

########################################
# add the mat-n-dependency equations from the dependencies dict that was one of our inputs

for mat, deps in dependencies.items():
    for dep, count in deps.items():
        adddep(mat, dep, count)

########################################
# add the mat-wantsum equations

for dep, revdep_vars in revdeps.items():
    l = [(dep + "_w", -1)]
    l += [(var, 1) for var in revdep_vars]
    addeq(dep + "-wantsum", 0, l)

########################################
# add our mat-top equations from the goals dict that was one of our inputs

for mat, count in goals.items():
    addeq(mat + "-top",
          -count,
          [(mat + "_w", -1.)])

########################################
# add the mat-balance equations

for mat in mats:
    addeq(mat + "-balance",
          0, [(mat + "_w", -1.),
              (mat + "_n", 1.),
              (mat + "_h", 1.),
              (mat + "_e", -1)])

########################################
# add the mat-have equations from the counts dict that was one of our inputs.

for mat,count in counts:
    addeq(mat + "-have",
          count, [(mat + "_h", 1.)])

########################################
# add the mat-pos inequalities that keep things from exploding.

for mat in mats:
    addineq(mat + "-w pos",
            0., [(mat + "_w", -1.)])
    addineq(mat + "-e pos",
            0., [(mat + "_e", -1.)])
    addineq(mat + "-n pos",
            0., [(mat + "_n", -1.)])

########################################
# set up the coefficients for the objective function using the overages dict that was an input.

for mat,cost in overages:
    c_dict[indices[mat + "_e"]] = cost
    c_dict[indices[mat + "_w"]] = cost

########################################
# as it turns out, h, b, and c have to be dense, so we turn those dicts into actual lists.

h_row = [0] * len(ineqrows)
for idx, val in h_dict.items():
    h_row[idx] = val

b_row = [0] * len(eqrows)
for idx, val in b_dict.items():
    b_row[idx] = val

c_row = [0] * len(variables)
for idx, val in c_dict.items():
    c_row[idx] = val

################################################################################
## SOLVE #######################################################################
################################################################################

########################################
# finally create the actual matrices

c = matrix(c_row, tc='d')
b = matrix(b_row, tc='d')
G = spmatrix(G_x, G_i, G_j, size=(len(ineqrows), len(variables)), tc='d')
A = spmatrix(A_x, A_i, A_j, tc='d')
h = matrix(h_row, tc='d')

########################################
# run the solver!

sol = solvers.lp(c, G, h, A, b)

################################################################################
## OUTPUT ######################################################################
################################################################################

########################################
# our program is guaranteed to have a solution if we constructed it right, so we just grab our
# solution numbers out and give them to the user:

numbers = [round(x, 3) for x in sol['x']]
for mat in mats:
    print("{0:8}: want {1:5}, have {2:5}, so need {3:5} and {4:5} extra".format(
        mat,
        numbers[indices[mat + "_w"]],
        numbers[indices[mat + "_h"]],
        numbers[indices[mat + "_n"]],
        numbers[indices[mat + "_e"]]
    ))
