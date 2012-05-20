import globals
from globals import Environment, RandomDB
from expressions import *

def reset():
  globals.env.assignments = {}
  globals.db.reset()
  globals.mem.reset()

def assume_helper(varname, expr, reflip):
  value = evaluate(expr, globals.env, reflip = reflip, stack = [varname])
  globals.env.set(varname, value)
  return value

def assume(varname, expr):
  expr = expression(expr)
  globals.mem.add('assume', (varname, expr))
  return assume_helper(varname, expr, True)

def observe_helper(expr, obs_val):
  # bit of a hack, here, to make it recognize same things as with noisy_expr
  val = evaluate(expr, globals.env, reflip = False, stack = ['obs', expr.hashval], xrp_force_val = obs_val)

def observe(expr, obs_val):
  expr = expression(expr)
  obs_val = value(obs_val)
  assert expr.type == 'apply' and expr.op.type == 'value' 
  assert expr.op.val.type == 'xrp'
  globals.mem.add('observe', (expr, obs_val))
  observe_helper(expr, obs_val)
  return expr.hashval 

def forget(hashval):
  globals.db.remove(['obs', hashval])
  globals.mem.forget(hashval)

# Replaces variables with the values from the environment 
def replace(expr, env):
  if expr.type == 'value':
    return expr
  elif expr.type == 'variable':
    val = env.lookup(expr.name)
    if val is None:
      return expr
      #warnings.warn('Unbound free variable %s' % expr.name)  ... not necessarily bad 
    else:
      return Expression(val)
  elif expr.type == 'if':
    cond = replace(expr.cond, env)
    true = replace(expr.true, env)
    false = replace(expr.false, env)
    return Expression(('if', cond, true, false)) 
  elif expr.type == 'switch':
    index = replace(expr.index, env)
    children = [replace(x, env) for x in expr.children]
    return Expression(('switch', index, children)) 
  elif expr.type == 'apply':
    # hmm .. replace non-bound things in op?  causes recursion to break...
    children = [replace(x, env) for x in expr.children] 
    return Expression(('apply', expr.op, children)) 
  elif expr.type == 'function':
    body = replace(expr.body, env)
    return Expression(('function', expr.vars, body)) 
  elif expr.type in ['=', '<', '>', '>=', '<=', '&', '|', 'add', 'subtract', 'multiply']:
    children = [replace(x, env) for x in expr.children] 
    return Expression((expr.type, children)) 
  elif expr.type == '~':
    return Expression(('not', replace(expr.negation, env))) 
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    return None


# Draws a sample value (without re-sampling other values) given its parents, and sets it
def evaluate(expr, env = None, reflip = False, stack = [], xrp_force_val = None):
  if env is None:
    env = globals.env

  expr = expression(expr)

  def binary_op_evaluate(expr, env, reflip, stack, op): 
    val1 = evaluate(expr.children[0], env, reflip, stack + [0])
    val2 = evaluate(expr.children[1], env, reflip, stack + [1])
    return Value(op(val1.val , val2.val))

  def list_op_evaluate(expr, env, reflip, stack, op):
    vals = [evaluate(expr.children[i], env, reflip, stack + [i]).val for i in xrange(len(expr.children))]
    return Value(reduce(op, vals))

  # THIS IS NONSENSE
  #if (not reflip) and globals.db.has(expr):
  #  return globals.db.get_val(expr)

  if expr.type == 'value':
    return expr.val
  elif expr.type == 'variable':
    var = expr.name
    val = env.lookup(var)
    if val is None:
      #warnings.warn('Variable %s undefined' % var)
      print 'Variable %s undefined' % var
      assert False
    else:
      return val
  elif expr.type == 'if':
    cond = evaluate(expr.cond, env, reflip, stack + [-1])
    assert type(cond.val) in [bool] 
    if cond.val: 
      globals.db.unevaluate(stack + [0])
      return evaluate(expr.true, env, reflip, stack + [1])
    else:
      globals.db.unevaluate(stack + [1])
      return evaluate(expr.false, env, reflip, stack + [0])
  elif expr.type == 'switch':
    index = evaluate(expr.index, env, reflip, stack + [-1])
    assert type(index.val) in [int] 
    assert 0 <= index.val < expr.n
    # unevaluate?
    return evaluate(expr.children[index.val], env, reflip, stack + [index.val])
  elif expr.type == 'apply':
    n = len(expr.children)
    args = [evaluate(expr.children[i], env, reflip, stack + [i]) for i in range(n)]
    op = evaluate(expr.op, env, reflip, stack + [-2])
    if op.type == 'procedure':
      globals.db.unevaluate(stack + [-1], args)
      assert n == len(op.vars)
      newenv = op.env.spawn_child()
      for i in range(n):
        newenv.set(op.vars[i], args[i]) 
      return evaluate(op.body, newenv, reflip, stack + [-1, tuple(args)])
    elif op.type == 'xrp':

      if xrp_force_val != None: 
        if globals.db.has(stack):
          globals.db.remove(stack)
        globals.db.insert(stack, op.val, xrp_force_val, args, True) 
        return xrp_force_val

      stack = stack + [-1, tuple(args)]
      if not globals.db.has(stack):
        val = value(op.val.apply(args))
        globals.db.insert(stack, op.val, val, args)
      else:
        if reflip:
          globals.db.remove(stack)
          val = value(op.val.apply(args))
          globals.db.insert(stack, op.val, val, args)
        else:
          val = globals.db.get_val(stack) 
      return val
    else:
      warnings.warn('Must apply either a procedure or xrp')
  elif expr.type == 'function':
    n = len(expr.vars)
    newenv = env.spawn_child()
    for i in range(n): # Bind variables
      newenv.set(expr.vars[i], expr.vars[i])
    procedure_body = replace(expr.body, newenv)
    return Value((expr.vars, procedure_body), env)
  elif expr.type == '=':
    return binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x == y)
  elif expr.type == '<':
    return binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x < y)
  elif expr.type == '>':
    return binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x > y)
  elif expr.type == '<=':
    return binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x <= y)
  elif expr.type == '>=':
    return binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x >= y)
  elif expr.type == '&':
    return list_op_evaluate(expr, env, reflip, stack, lambda x, y : x & y)
  elif expr.type == '|':
    return list_op_evaluate(expr, env, reflip, stack, lambda x, y : x | y)
  elif expr.type == '~':
    neg = evaluate(expr.negation, env, reflip, stack)
    return Value(not neg.val)
  elif expr.type == 'add':
    return list_op_evaluate(expr, env, reflip, stack, lambda x, y : x + y)
  elif expr.type == 'subtract':
    val1 = evaluate(expr.children[0], env, reflip, stack + [0])
    val2 = evaluate(expr.children[1], env, reflip, stack + [1])
    return Value(val1.val - val2.val)
  elif expr.type == 'multiply':
    return list_op_evaluate(expr, env, reflip, stack, lambda x, y : x * y)
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    return None

def sample(expr, env = None, varname = None, reflip = False):
  expr = expression(expr)
  if env is None:
    env = globals.env
  if varname is None:
    return evaluate(expr, env, reflip, ['expr', expr.hashval])
  else:
    return evaluate(expr, env, reflip, [varname])

def resample(expr, env = None, varname = None):
  return sample(expr, env, varname, True)

### OUTDATED
##def reject_infer():
##  flag = False
##  while not flag:
##    rerun(True)
##
##    # Reject if observations untrue
##    flag = True
##    for obs_expr in globals.obs.obs:
##      obsval = resample(obs_expr)
##      if obsval.val != globals.obs.get_val(obs_expr):
##        flag = False
##        break

# Rejection based inference
def reject_infer_many(name, niter = 1000):
  if name in globals.mem.vars:
    expr = globals.mem.vars[name]
  else:
    warnings.warn('%s is not defined' % str(name))

  dict = {}
  for n in xrange(niter):
    # Re-draw from prior
    reject_infer()
    ans = evaluate(expr, globals.env, False, [name]) 

    if ans.val in dict:
      dict[ans.val] += 1
    else:
      dict[ans.val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 

def rerun(reflip):
# Class representing environments
  for (varname, expr) in globals.mem.assumes:
    assume_helper(varname, expr, reflip)
  for hashval in globals.mem.observes:
    (expr, obs_val) = globals.mem.observes[hashval] 
    observe_helper(expr, obs_val)

def infer(): # RERUN AT END
  # reflip some coin
  is_obs_noise = True
  while is_obs_noise:
    stack = globals.db.random_stack() 
    (xrp, val, prob, args, is_obs_noise) = globals.db.get(stack)

  #debug = True 
  debug = False 

  old_p = globals.db.prob() 
  old_to_new_q = - math.log(globals.db.count) 
  if debug:
    old_db = [(s, globals.db.db[s][1].val) for s in globals.db.db] 
    print len(globals.db.db)

  globals.db.save()

  globals.db.remove(stack)
  new_val = xrp.apply(args)

  if debug:
    print "\nchanging", stack, "to", new_val
    print  "old_db", old_db
  if val == new_val:
    globals.db.insert(stack, xrp, new_val, args)
    return
  globals.db.insert(stack, xrp, new_val, args)

  rerun(False)
  new_p = globals.db.prob() 
  new_to_old_q = -math.log(globals.db.count) 
  old_to_new_q += globals.db.eval_p 
  new_to_old_q += globals.db.uneval_p 
  if debug:
    print "new db", [(s, globals.db.db[s][1]) for s in globals.db.db] 
    print "q(o -> n)", old_to_new_q, "q(n -> o)", new_to_old_q 
    print "p(old)", old_p, "p(new)", new_p
    print 'log transition prob',  new_p + new_to_old_q - old_p - old_to_new_q 

  if old_p * old_to_new_q > 0:
    p = random.random()
    if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
      globals.db.restore()
      if debug: 
        print 'restore'
  globals.db.save()
  if debug: 
    print "new db", [(s, globals.db.db[s][1]) for s in globals.db.db] 

def follow_prior(name, niter = 1001, burnin = 100):

  if name in globals.mem.vars:
    expr = globals.mem.vars[name]
  else:
    warnings.warn('%s is not defined' % str(name))

  dict = {}
  for n in xrange(niter):
    #if n % 100 == 0: print n

    # re-draw from prior
    rerun(True)
    for t in xrange(burnin):
      infer()

    rerun(False) 
    val = evaluate(name, globals.env, reflip = False, stack = [name])
    if val.val in dict:
      dict[val.val] += 1
    else:
      dict[val.val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 


