from expressions import *
from mem import *

from traces import *
from reducedtraces import *
from randomdb import *
from utils.format import table_to_string
from utils.rexceptions import RException

import time
import sys

try:
  from pypy.rlib.jit import JitDriver
  jitdriver = JitDriver(greens = [ \
                                 ### INTs 
                                 ### REFs 
                                 ### FLOATs 
                                 ],  \
                        reds   = [  \
                                 ### INTs 
                                 #'assume', \
                                 #'observed', \
                                 #'predict', \
                                 #'active', \
                                 #'mem', \
                                 #'random_xrp_apply', \

                                 ### REFs 
                                 #'traces', \
                                 #'parent', \
                                 #'mem_calls', \
                                 #'env', \
                                 #'assume_name', \
                                 #'observe_val', \
                                 #'expression', \
                                 #'type', \
                                 #'children', \
                                 #'active_children', \
                                 #'lookups', \
                                 #'xrp_applies', \
                                 #'xrp', \
                                 #'args', \
                                 #'val', \
                                 #'xrp_force_val', \
                                 'engine' \

                                 ### FLOATs 
                                 #'p' \
                                 ])
  def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()
  use_jit = True
except:
  use_jit = False

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
        raise RException("id %d was never observed" % id) 
      (expr, val, active) = self.observes[id]
      if not active:
        raise RException("observe %d was already forgotten" % id) 
      self.observes[id] = (expr, val, False)
    elif self.directives[id] == 'predict':
      if id not in self.predicts:
        raise RException("id %d was never predicted" % id) 
      (expr, active) = self.predicts[id]
      if not active:
        raise RException("predict %d was already forgotten" % id) 
      self.predicts[id] = (expr, False)
    else:
      raise RException("Cannot forget assumes")
    
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
  raise RException("Engine %s is not implemented" % engine_type)

sys.setrecursionlimit(10000)

def reset_helper():
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

  assume('make-CRP', xrp(gen_CRP_XRP()), True)

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

def reset():
  reset_helper()
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
  reset_helper()
  for id in range(len(memory.directives)):
    if memory.directives[id] == 'assume':
      (varname, expr) = memory.assumes[id]
      engine.assume(varname, expr, id)
    elif memory.directives[id] == 'observe':
      (expr, val, active) = memory.observes[id]
      if active:
        engine.observe(expr, val, id)
    elif memory.directives[id] == 'predict':
      (expr, active) = memory.predicts[id]
      if active:
        engine.predict(expr, id)
    else:
      raise RException("Invalid directive")
  
def report_value(id):
  value = engine.report_value(id)
  return value

def report_directives(directive_type = ""):
  return engine.report_directives(directive_type)

def infer(iters = 1):

  t = time.time()

  for i in range(iters):
    if use_jit:
      jitdriver.jit_merge_point( \
                                 # INTs
                                 #observed = evalnode.observed, \
                                 #assume = evalnode.assume, \
                                 #predict = evalnode.predict, \
                                 #active = evalnode.active, \
                                 #random_xrp_apply = evalnode.random_xrp_apply, \
                                 #mem = evalnode.mem, \
                                 ## REFs
                                 #traces = evalnode.traces, \
                                 #parent = evalnode.parent, \
                                 #mem_calls = evalnode.mem_calls, \
                                 #env = evalnode.env, \
                                 #assume_name = evalnode.assume_name, \
                                 #observe_val = evalnode.observe_val, \
                                 #expression = evalnode.expression, \
                                 #type = evalnode.type, \
                                 #children = evalnode.children, \
                                 #active_children = evalnode.active_children, \
                                 #lookups = evalnode.lookups, \
                                 #xrp_applies = evalnode.xrp_applies, \
                                 #xrp = evalnode.xrp, \
                                 #args = evalnode.args, \
                                 #val = evalnode.val, \
                                 engine = engine \
                                 # FLOATs
                                 #p = evalnode.p
                                 )   
    #node = engine.random_node()
    ## evalnode if traces/reduced traces
    ## stack if randomdb

    engine.infer()

  t = time.time() - t
  return t

reset()
