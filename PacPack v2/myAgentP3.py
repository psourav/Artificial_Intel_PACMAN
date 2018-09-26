# myAgentP3.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).
# This file was based on the starter code for student bots, and refined
# by Mesut (Xiaocheng) Yang


from captureAgents import CaptureAgent
import random, time, util

from game import Directions
import game
from util import nearestPoint

SEARCH_DEPTH = 2
#########
# Agent #
#########
class myAgentP3(CaptureAgent):
  """
  YOUR DESCRIPTION HERE
  """


  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).
    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)
    IMPORTANT: This method may run for at most 15 seconds.
    """

    # Make sure you do not delete the following line.
    # If you would like to use Manhattan distances instead
    # of maze distances in order to save on initialization
    # time, please take a look at:
    # CaptureAgent.registerInitialState in captureAgents.py.
    CaptureAgent.registerInitialState(self, gameState)
    self.start = gameState.getAgentPosition(self.index)
    self.t_index = list(filter(lambda index: index == self.index, gameState.getPacmanTeamIndices()))[0]
    self.start_dots = len(gameState.getFood().asList())
    self.reroute = 0
    self.problem_dot = None
    self.random_dot = None

  #returns the optimal plan gor
  def mini_max(self, state, teammate_plan, plan_so_far, player, depth, alpha, beta):
    is_win = len(state.getFood().asList()) == 2
    team_pacman = state.getPacmanTeamIndices()
    my_pacman = self.index
    if is_win or depth == 0:
        return [self.evaluationFunction(state, teammate_plan), plan_so_far]
    elif player in team_pacman:
        return self.maximize(state, teammate_plan, plan_so_far, player, depth, alpha, beta)
    else:
        return self.minimize(state, teammate_plan, plan_so_far, player, depth, alpha, beta)


  def maximize(self, state, teammate_plan, plan_so_far, player, depth, alpha, beta):
    my_pacman = self.index
    max_node = [float("-inf"), plan_so_far]
    if player == my_pacman:
        actions = actionsWithoutStop(state.getLegalActions(player))
    else:

        actions = actionsWithoutReverse(actionsWithoutStop(state.getLegalActions(player)), state,player)
    successors = ([state.generateSuccessor(player, a), a] for a in actions)
    for s,a in successors:
        next_player = (player + 1) % state.getNumAgents()
        if player == my_pacman:
            c_node = self.mini_max(s, teammate_plan, plan_so_far + [a], next_player, depth, alpha, beta)
        else:
            c_node = self.mini_max(s, teammate_plan, plan_so_far, next_player, depth, alpha, beta)
        max_node = max(max_node, c_node, key = lambda x: x[0])
        value = max_node[0]
        if value > beta:
            return max_node
        alpha = max(alpha, value)
    return max_node

  def minimize(self, state, teammate_plan, plan_so_far, player, depth, alpha, beta):
    min_node = [float("inf"), plan_so_far]
    actions =  actionsWithoutReverse(actionsWithoutStop(state.getLegalActions(player)), state, player)
    successors = ([state.generateSuccessor(player, a), plan_so_far] for a in actions)
    for s,a in successors:
        n_player = (player + 1) % state.getNumAgents()
        c_node = self.mini_max(s, teammate_plan, plan_so_far, n_player, depth - 1, alpha, beta)
        min_node = min(min_node, c_node, key = lambda x: x[0])
        value = min_node[0]
        if value < alpha:
            return min_node
        beta = min(beta, value)
    return min_node

  #return the value of gamestate in said gameState
  def evaluationFunction(self, state, teammates_plan):
    oldFood = state.getFood()
    pos = state.getAgentPosition(self.index)
    #filter the dots that your teammate plans on eating
    f_dots = []
    for x in range(oldFood.width):
        for y in range(oldFood.height):
            if oldFood[x][y] and not (x,y) in teammates_plan:
                f_dots.append((x,y))


    ghostPositions = [state.getAgentPosition(ghostIndex) for ghostIndex in self.getOpponents(state)]
    ghostDistances = [self.getMazeDistance(pos, ghostPosition) for ghostPosition in ghostPositions]
    ghostDistances.append( 1000 )

    if self.reroute == 0:
        f_dots.sort(key = lambda dot: self.getMazeDistance(pos, dot))
        min_dot = self.getMazeDistance(f_dots[0], pos)
        closestFood = float(1) / float(min_dot  + 1.0)
        if min(ghostDistances) < 3:
            closestGhost = float(0.025) / float(min( ghostDistances ) + 1)
        else :
            closestGhost = 0
        score = self.getScore(state)
        closestFriend = float(5) /  float(self.getMazeDistance(pos, state.getAgentPosition(self.t_index)) + 1.0)

        numRepeats = sum([1 for x in self.observationHistory[-20:] if x.getAgentPosition(self.index) == pos])
        #try spreading out if stuck?? idk if you have any ideas
        if numRepeats > 4:
            f_dots.sort(key = lambda dot: self.getMazeDistance(pos, dot))
            self.problem_dot = f_dots[0]
            random.shuffle(f_dots)
            self.random_dot = f_dots[0]
            self.reroute += 100
        return closestFood + score - closestGhost - closestFriend
    else:
        print(self.reroute)
        self.reroute -= 1
        #go to dot thats furthest away for a bit to guarantee you don't get
        #stuck trying to reach for another dot
        f_dots.sort()
        new_dot = f_dots[0]
        min_dot = self.getMazeDistance(self.random_dot, pos)
        closestFood = float(1) / float(min_dot  + 1.0)
        closestGhost = float(0.001) / float(min( ghostDistances ) + 1)

        score = self.getScore(state)
        closestFriend = float(10) /  float(self.getMazeDistance(pos, state.getAgentPosition(self.t_index)) + 1.0)
        return closestFood + score - closestGhost - closestFriend

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    teammateActions = self.receivedBroadcast

    t_future_pos = getFuturePositions(gameState, teammateActions, self.t_index)

    t_plan = getFutureDots(t_future_pos, gameState, self.t_index)
    # Process your teammate's broadcast!
    # Use it to pick a better action for yourself

    plan = self.mini_max(gameState, t_plan, [], self.index, SEARCH_DEPTH, float("-Inf"), float("Inf"))[1]
    max_action = plan[0]# Change this!
    futureActions = plan
    self.toBroadcast = plan
    return max_action

#returns the dots the agent specified plans on eating
def getFutureDots(positions, gameState, agent_index):
    dots = []
    if positions:
        uneaten = gameState.getFood().asList()
        for pos in positions:
            if pos in uneaten:
                dots.append(pos)
    return dots

def actionsWithoutStop(legalActions):
  """
  Filters actions by removing the STOP action
  """
  legalActions = list(legalActions)
  if Directions.STOP in legalActions:
    legalActions.remove(Directions.STOP)
  return legalActions

def actionsWithoutReverse(legalActions, gameState, agentIndex):
  """
  Filters actions by removing REVERSE, i.e. the opposite action to the previous one
  """
  legalActions = list(legalActions)
  reverse = Directions.REVERSE[gameState.getAgentState(agentIndex).configuration.direction]
  if len (legalActions) > 1 and reverse in legalActions:
    legalActions.remove(reverse)
  return legalActions

def getFuturePositions(gameState, plannedActions, agentIndex):
    """
    Returns list of future positions given by a list of actions for a
    specific agent starting form gameState
    NOTE: this does not take into account other agent's movements
    (such as ghosts) that might impact the *actual* positions visited
    by such agent
    """
    if plannedActions is None:
      return None

    planPositions = [gameState.getAgentPosition(agentIndex)]
    for action in plannedActions:
      if action in gameState.getLegalActions(agentIndex):
        gameState = gameState.generateSuccessor(agentIndex, action)
        planPositions.append(gameState.getAgentPosition(agentIndex))
      else:
        print("Action list contained illegal actions")
        break
    return planPositions