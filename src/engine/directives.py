from expressions import *
from mem import *

from traces import *
from reducedtraces import *
from randomdb import *
from utils.format import table_to_string

import sys

class DirectivesMemory:
  def __init__(self):
    # id -> (name, expr)
    self.assumes = {}
    # id -> (expr, val, active)
    self.observes = {}
    # id -> (expr, active)
    self.predicts = {}

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

  def predict(self, expr): 
    self.directives.append('predict')
    id = self.get_next_id()
    self.predicts[id] = (expr, True)
    return id

  def forget(self, id):
    if self.directives[id] == 'observe':
      if id not in self.observes:
        raise Exception("id %d was never observed" % id) 
      (expr, val, active) = self.observes[id]
      if not active:
        raise Exception("observe %d was already forgotten" % id) 
      self.observes[id] = (expr, val, False)
    elif self.directives[id] == 'predict':
      if id not in self.predicts:
        raise Exception("id %d was never predicted" % id) 
      (expr, active) = self.predicts[id]
      if not active:
        raise Exception("predict %d was already forgotten" % id) 
      self.predicts[id] = (expr, False)
    else:
      raise Exception("Cannot forget assumes")
    
  def reset(self):
    self.__init__()

memory = DirectivesMemory()

engine_type = 'reduced traces'

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

  assume('bernoulli', xrp(bernoulli_args_XRP()), True)
  assume('flip', var('bernoulli'), True)
  assume('beta', xrp(beta_args_XRP()), True)
  assume('gamma', xrp(gamma_args_XRP()), True)
  assume('gaussian', xrp(gaussian_args_XRP()), True)
  assume('normal', var('gaussian'), True)
  assume('uniform', xrp(uniform_args_XRP()), True)
  assume('rand', function([], apply(var('beta'), [num_expr(1), num_expr(1)])), True)

  assume('make-symmetric-dirichlet', xrp(make_symmetric_dirichlet_XRP()), True)

  assume('mem', xrp(mem_XRP()), True)

  """DEFINITION OF DP"""
  assume('DP_uncollapsed', \
         function(['concentration', 'basemeasure'], \
                  let([('sticks', apply(var('mem'), [function(['j'], apply(var('beta'), [num_expr(1), var('concentration')]))])),
                       ('atoms',  apply(var('mem'), [function(['j'], apply(var('basemeasure'), []))])),
                       ('loop', \
                        function(['j'], 
                                 ifelse(apply(var('bernoulli'), [apply(var('sticks'), [var('j')])]), \
                                        apply(var('atoms'), [var('j')]), \
                                        apply(var('loop'), [op('+', [var('j'), num_expr(1)])])))) \
                      ], \
                      function([], apply(var('loop'), [num_expr(1)])))),
         True) 

  """DEFINITION OF ONE ARGUMENT DPMEM"""
  assume('DPmem_uncollapsed', \
         function(['concentration', 'proc'], \
                  let([('restaurants', \
                        apply(var('mem'), [function(['args'], apply(var('DP'), [var('concentration'), function([], apply(var('proc'), [var('args')]))]))]))], \
                      function(['args'], apply(var('restaurants'), [var('args')])))), 
         True) 

  memory.reset()

def assume(varname, expr, default = False):
  id = -1
  if not default:
    id = memory.assume(varname, expr)
  val = engine.assume(varname, expr, id)
  return (val, id)

def observe(expr, obs_val):
  id = memory.observe(expr, obs_val)
  val = engine.observe(expr, obs_val, id)
  return id

def forget(id):
  memory.forget(id)
  engine.forget(id)
  return
  
def predict(expr):
  id = memory.predict(expr)
  val = engine.predict(expr, id)
  return (val, id)

def rerun():
# Class representing environments
  engine.rerun()
  
def report_directives(directive_type = ""):
  directives_report = engine.report_directives(directive_type)
  return table_to_string(directives_report, ['id', 'directive', 'value'])  

def infer():
  engine.infer()
