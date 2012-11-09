import globals
from globals import Environment, RandomDB
from expressions import *
from mem import *

def reset():
  globals.engine.reset()

  assume('bernoulli', xrp(bernoulli_args_XRP()))
  assume('flip', var('bernoulli'))
  assume('beta', xrp(beta_args_XRP()))
  assume('gamma', xrp(gamma_args_XRP()))
  assume('gaussian', xrp(gaussian_args_XRP()))
  assume('uniform', xrp(uniform_args_XRP()))
  assume('mem', xrp(mem_XRP()))
  assume('rand', function([], apply(var('beta'), [num_expr(1), num_expr(1)])))

  # NOTE: There are a constant number of floating assumes!
  globals.memory.reset()

def assume(varname, expr):
  id = globals.memory.assume(varname, expr)
  val =  globals.engine.assume(varname, expr)
  return (val, id)

def observe(expr, obs_val):
  id = globals.memory.observe(expr, obs_val)

  #NOTE: the following would be true, except there could be variables, etc
  #assert expr.type == 'apply' and expr.op.type == 'value' 
  #assert expr.op.val.type == 'xrp'
  #assert not expr.op.val.xrp.deterministic

  globals.engine.observe(expr, obs_val, id)
  return id

def forget(id):
  # if using db, is a hashval
  # if using traces, is an evalnode

  globals.memory.forget(id)
  globals.engine.forget(id)
  
def sample(expr):
  return globals.engine.sample(expr)

def rerun(reflip):
# Class representing environments
  globals.engine.rerun(reflip)
  
def infer():
  globals.engine.infer()
