import globals
from globals import Environment, RandomDB
from expressions import *
from mem import *

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

def reset():
  if globals.use_traces:
    globals.traces.reset()
  else:
    globals.db.reset()

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
  if globals.use_traces:
    val =  globals.traces.assume(varname, expr)
  else:
    val = globals.db.assume(varname, expr)
  return (val, id)

def observe(expr, obs_val):
  id = memory.observe(expr, obs_val)

  #NOTE: would be true, except there could be variables, etc
  #assert expr.type == 'apply' and expr.op.type == 'value' 
  #assert expr.op.val.type == 'xrp'
  #assert not expr.op.val.xrp.deterministic

  if globals.use_traces:
    print "here3"
    globals.traces.observe(expr, obs_val, id)
    print "here4"
  else:
    globals.db.observe(expr, obs_val, id)
  return id

def forget(id):
  # if using db, is a hashval
  # if using traces, is an evalnode

  memory.forget(id)
  if globals.use_traces:
    globals.traces.forget(id)
  else:
    globals.db.forget(id)

def sample(expr, env = None, varname = None, reflip = False):
  if globals.use_traces:
    name = str(expr) + str(rrandom.random.randbelow())
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
  node = globals.traces.random_node() 

def infer():
  if globals.use_traces:
    globals.traces.infer()
    return
  else:
    globals.db.infer()
