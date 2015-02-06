#!/usr/bin/env python3



import json
import sys


################################################################################
## definitions #################################################################
################################################################################


class GoalData(object):
    def __init__(self, count, dtype):
        pass

def AddGoal(goal, goal_count, goal_type, goaldict):
    if goal not in goaldict:
        # nothing there, shove it in
        goaldict[goal] = (goal_count, goal_type)
    else:
        # it's already in there, we need to update it appropriately
        old_count, old_type = goaldict[goal]
        if old_type == "consume" and goal_type == "consume":
            # just add them together
            goaldict[goal] = (old_count + goal_count, "consume")
        elif old_type == "require" and goal_type == "require":
            # whichever one needs more gets it
            goaldict[goal] = (max(old_count, goal_count), "require")
        elif old_type != goal_type:
            # TODO: figure out something smarter to do here. I'm not sure what it might be; it'll
            # probably involve a significant architectural change. It *may* require algorithmic
            # changes. This situation - where we need to use something before eating it - is really
            # the domain of a partial-order planner, and we're doing a dumb stateless recursive
            # thing that assumes that everything is additive. Probably going to be two stages;
            # first would be an architectural change that lets us have both requires and consumes
            # goals for the same thing and consider them intelligently, second would be shifting
            # over to an entirely different algorithm, probably something in the partial-order
            # family.
            goaldict[goal] = (max(old_count, goal_count), "consume")

class DAGEdge(object):
    def __init__(self, action, dependency, satisfier):
        self.action = action
        self.dependency = dependency
        dependency.satisfiedby.add(self)
        self.satisfier = satisfier
        satisfier.satisfies.add(self)
    def remove(self):
        self.dependency.satisfiedby.remove(self)
        self.satisfier.satisfies.remove(self)

class DAGNode(object):
    def __init__(self, name, count):
        self.satisfies = set()  # set of DAGEdges
        self.satisfiedby = set()  # set of DAGEdges
        self.name = name
        self.count = count

################################################################################
## declarations/globals/set-up-once-and-use-multiple ###########################
################################################################################

# list to store things that the player can do to transform goals into simpler intermediate goals
actions = None

# dag of actions which when linearized will be our plan
nodes = dict()
dagroot = DAGNode("root", 0)

# set of goals which need to be satisfied. keys are tuples that specify the count and whether the
# goal is a a consume or a require. (count, "consume"|"require")
unsat = dict()

# things that seem to be terminals - we can't find any actions which would satisfy them
unsatisfiable = dict()

# set of goals which satisfied previous consumes dependencies and are therefore still around
resources = dict()

# and a thing to track how much stuff goes through our system
resources_consumed = dict()

################################################################################
## handle command line args and get input ######################################
################################################################################

# a list of actions that we can take.
actionsfilename = sys.argv[1]
with open(actionsfilename, "r") as actionfile:
    actions = json.load(actionfile)

# a list of top-level goals.
goalsfilename = sys.argv[2]
with open(goalsfilename, "r") as goalfile:
    goals = json.load(goalfile)

# a list of things we've already built or gotten done.
if len(sys.argv) >= 4:
    resourcesfilename = sys.argv[3]
    with open(resourcesfilename, "r") as resourcesfile:
        resources = json.load(resourcesfile)
else:
    resources = dict()


################################################################################
## set up planner data structures ##############################################
################################################################################

# we store actions as a map from the thing the action provides
def action_filter(input_actions):
    for name, deps in input_actions.items():
        dependencies = dict()
        for g,c in deps["requires"].items():
            dependencies[g] = (c, "require")
        for g,c in deps["consumes"].items():
            dependencies[g] = (c, "consume")
        yield (name, dependencies)
actions = dict(action_filter(actions))

print("Actions: ")
for name,deps in actions.items():
    print("  {0} <- {1} using {2}".format(name,
                                          ["{0} {1}".format(depc, depn)
                                           for (depn,(depc, dept)) in deps.items()
                                           if dept == "consume"],
                                          ["{0} {1}".format(depc, depn)
                                           for (depn,(depc, dept)) in deps.items()
                                           if dept == "require"]))
print()

# we start the algorithm off with several unsatisfied requires dependencies, corresponding to the
# user's top-level goals
unsat = {name: (count, "require") for (name, count) in goals.items()}

print("Initial goals:")
for name,(count, t) in unsat.items():
    print("  {0}: {1:3}x {2}".format(t, count, name))
print()

# resources is already in the correct format, since it doesn't need anything special. it's just a
# map from names to counts of the resources we already have.
print("Initial resources:")
for name,count in resources.items():
    print("  {0:3}x {1}".format(count, name))
print()

################################################################################
## run the actual planner ######################################################
################################################################################


while unsat:
    (next_name,(next_count,next_type)) = unsat.popitem()
    print("{2}ing {0} x{1}".format(next_name, next_count, next_type[:-1]))

    if next_type == "consume":
        # track how much we consume total
        AddGoal(next_name, next_count, "consume", resources_consumed)
        
    if next_name in resources:
        if next_type == "require" and resources[next_name] >= next_count:
            # we have everything we need, continue happily
            print("  satisfied by existing resources")
            continue
        elif next_type == "require" and resources[next_name] < next_count:
            # we have some, but not enough. reduce our count and move to the next section to add
            # the remainder
            print("  partially satisfied by existing resources")
            next_count -= resources[next_name]
        elif next_type == "consume" and resources[next_name] > next_count:
            # we have everything we need, but we have to eat some of it
            print("  partially satisfied by existing resources")
            # print("  consuming {0}x {1}".format(next_count, next_name))
            # AddGoal(next_name, next_count, "consume", resources_consumed)
            resources[next_name] -= next_count
            # otherwise done; no need for more goals
            continue
        elif next_type == "consume" and resources[next_name] == next_count:
            # we're going to consume exactly as much as we have
            print("  satisfied perfectly by existing resources")
            # print("  consuming {0}x {1}".format(next_count, next_name))
            # AddGoal(next_name, next_count, "consume", resources_consumed)
            del resources[next_name]
            # otherwise done; no need for more goals
            continue
        elif next_type == "consume" and resources[next_name] < next_count:
            # we don't have enough to consume, so we remove that much from our count and add a goal
            # for the remainder
            print("  satisfied existing resources")
            # print("  consuming {0}x {1}".format(resources[next_name], next_name))
            # AddGoal(next_name, resources[next_name], "consume", resources_consumed)
            next_count -= resources[next_name]
            del resources[next_name]
            # move to the next section to add the remainder
            
    if next_name not in actions:
        # we can't satisfy this action, because we don't already have any and we don't know how to
        # make them. add a goal for it to the "you do this manually" list.
        AddGoal(next_name, next_count, next_type, unsatisfiable)
        print("  todo: {0}x {1}".format(next_count, next_name))
        
    # we need to add more of them and we have an action that will give us more.
    else:
        for subgoal_name, (subgoal_count, subgoal_type) in actions[next_name].items():
            if subgoal_type == "consume":
                # we need an entire set of the subgoal for every instance
                total_count = subgoal_count * next_count
            elif subgoal_type == "require":
                # we only need the number of resources specified total
                total_count = subgoal_count
            AddGoal(subgoal_name, total_count, subgoal_type, unsat)
            print("  new goal: {2} {1}x {0}".format(subgoal_name, total_count, subgoal_type))
    
    # now, if next_goal was a consume goal, it goes away entirely, but if it was a require goal
    # it's going to stick around. Put it in the resources set.
    if next_type == "require":
        if next_name in resources:
            resources[next_name] = max(resources[next_name], next_count)
        else:
            resources[next_name] = next_count


    
print()
print()
print("Remaining unsatisfied goals (should be none):")
for name,(count, t) in unsat.items():
    print("  {0}: {1:3}x {2}".format(t, count, name))
print()

print("Todo by hand:")
for name,(count, t) in [(n, (c, t)) for (n, (c, t)) in unsatisfiable.items() if t == "require"]:
    print("  {0}: {1:3}x {2}".format(t, count, name))
for name,(count, t) in [(n, (c, t)) for (n, (c, t)) in unsatisfiable.items() if t == "consume"]:
    print("  {0}: {1:3}x {2}".format(t, count, name))
print()

print("Resources that will be consumed:")
for name,(count, _) in resources_consumed.items():
    print("  {0:3}x {1}".format(count, name))
print()

print("Resources remaining at end:")
for name,count in resources.items():
    print("  {0:3}x {1}".format(count, name))
print()





# Local Variables:
# mode: python
# End:
