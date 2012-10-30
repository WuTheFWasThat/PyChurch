import globals
from globals import Environment, RandomDB
from expressions import *

def reset():
  if globals.use_traces:
    globals.traces.reset()
  else:
    globals.db.reset()

def assume(varname, expr):
  if globals.use_traces:
    return globals.traces.assume(varname, expr)
  else:
    return globals.db.assume(varname, expr)

def observe(expr, obs_val):
  assert expr.type == 'apply' and expr.op.type == 'value' 
  assert expr.op.val.type == 'xrp'
  assert not expr.op.val.val.deterministic

  if globals.use_traces:
    return globals.traces.observe(expr, obs_val)
  else:
    return globals.db.observe(expr, obs_val)

def forget(observation):
  # if using db, is a hashval
  # if using traces, is an evalnode

  if globals.use_traces:
    globals.traces.forget(observation)
  else:
    globals.db.forget(observation)

def sample(expr, env = None, varname = None, reflip = False):
  if globals.use_traces:
    name = str(expr) + str(random.randint(0, 2**32-1))
    assume(name, expr)
    return globals.traces.env.assumes[name].evaluate(False)
  else:
    if varname is None:
      return globals.db.evaluate(expr, env, reflip, ['expr', expr.hashval])
    else:
      return globals.db.evaluate(expr, env, reflip, [varname])

def resample(expr, env = None, varname = None):
  return sample(expr, env, varname, True)

def rerun(reflip):
# Class representing environments
  if globals.use_traces:
    globals.traces.rerun(reflip)
  else:
    globals.db.rerun(reflip)

def infer():
  if globals.use_traces:
    node = globals.traces.random_node() 
    globals.traces.reflip(node)
    return
  else:
    stack = globals.db.random_stack() 
    globals.db.reflip(stack)

