from expressions import *
from mem import *

from traces import *
#from reducedtraces import *
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

engine_type = 'traces'

# The global environment. Has assignments of names to expressions, and parent pointer 

if engine_type == 'reduced traces':
  env = EnvironmentNode()
  # The traces datastructure. 
  # DAG of two interlinked trees: 
  #   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
  #   2. environments
  # crosslinked by symbol lookup nodes and by the env argument to eval
  engine = ReducedTraces(env)
elif engine_type == 'traces':
  env = EnvironmentNode()
  # The traces datastructure. 
  # DAG of two interlinked trees: 
  #   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
  #   2. environments
  # crosslinked by symbol lookup nodes and by the env argument to eval
  engine = Traces(env)
elif engine_type == 'randomdb':
  # The global environment. Has assignments of names to expressions, and parent pointer 
  env = Environment()
  # Table storing a list of (xrp, value, probability) tuples
  engine = RandomDB(env)
else:
  raise Exception("Engine %s is not implemented" % engine_type)

sys.setrecursionlimit(10000)


def reset():
  engine.reset()

  assume('bernoulli', xrp(bernoulli_args_XRP()))
  assume('flip', var('bernoulli'))
  assume('beta', xrp(beta_args_XRP()))
  assume('gamma', xrp(gamma_args_XRP()))
  assume('gaussian', xrp(gaussian_args_XRP()))
  assume('uniform', xrp(uniform_args_XRP()))
  assume('mem', xrp(mem_XRP()))
  assume('rand', function([], apply(var('beta'), [num_expr(1), num_expr(1)])))

  # NOTE: There are a constant number of floating assumes!
  memory.reset()

def assume(varname, expr):
  id = memory.assume(varname, expr)
  val = engine.assume(varname, expr)
  return (val, id)

def observe(expr, obs_val):
  id = memory.observe(expr, obs_val)

  #NOTE: the following would be true, except there could be variables, etc
  #assert expr.type == 'apply' and expr.op.type == 'value' 
  #assert expr.op.val.type == 'xrp'
  #assert not expr.op.val.xrp.deterministic

  engine.observe(expr, obs_val, id)
  return id

def forget(id):
  # if using db, is a hashval
  # if using traces, is an evalnode

  memory.forget(id)
  engine.forget(id)
  
def sample(expr):
  return engine.sample(expr)

def rerun(reflip):
# Class representing environments
  engine.rerun(reflip)
  
def infer():
  engine.infer()
