from traces import *
from randomdb import *
import sys

class DirectivesMemory:
  def __init__(self):
    # id -> (name, expr)
    self.assumes = {}
    # id -> (expr, val, active)
    self.observes = {}
    self.directives = []
    self.next_id = -1

  def reset(self):
    self.__init__()

  def get_next_id(self):
    self.next_id += 1
    return self.next_id

  def assume(self, name, expr): 
    self.directives.append('assume')
    id = self.get_next_id()
    self.assumes[id] = (name, expr)
    return id

  def observe(self, expr, val): 
    self.directives.append('observe')
    id = self.get_next_id()
    self.observes[id] = (expr, val, True)
    return id

  def forget(self, id):
    if id not in self.observes:
      raise Exception("id %d was never observed" % id) 
    (expr, val, active) = self.observes[id]
    if not active:
      raise Exception("id %d was already forgotten" % id) 
    self.observes[id] = (expr, val, False)
    
  def reset(self):
    self.__init__()

memory = DirectivesMemory()

use_traces = True

# The global environment. Has assignments of names to expressions, and parent pointer 

if use_traces:
  env = EnvironmentNode()
  # The traces datastructure. 
  # DAG of two interlinked trees: 
  #   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
  #   2. environments
  # crosslinked by symbol lookup nodes and by the env argument to eval
  traces = Traces(env)
else:
  # The global environment. Has assignments of names to expressions, and parent pointer 
  env = Environment()
  # Table storing a list of (xrp, value, probability) tuples
  db = RandomDB(env)

sys.setrecursionlimit(10000)

