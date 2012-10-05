import globals
from globals import Environment, RandomDB
from expressions import *

def reset():
  globals.env.assignments = {}
  globals.db.reset()
  globals.traces.reset()
  globals.mem.reset()

def assume_helper(varname, expr, reflip):
  value = evaluate(expr, globals.env, reflip = reflip, stack = [varname])
  globals.env.set(varname, value)
  return value

def assume(varname, expr):
  expr = expression(expr)
  globals.mem.add('assume', (varname, expr))
  if globals.use_traces:
    return globals.traces.assume(varname, expr)
  else:
    return assume_helper(varname, expr, True)

def observe_helper(expr, obs_val):
    # bit of a hack, here, to make it recognize same things as with noisy_expr
    evaluate(expr, globals.env, reflip = False, stack = ['obs', expr.hashval], xrp_force_val = obs_val)
    return expr.hashval

def observe(expr, obs_val):
  expr = expression(expr)
  obs_val = value(obs_val)
  assert expr.type == 'apply' and expr.op.type == 'value' 
  assert expr.op.val.type == 'xrp'
  assert not expr.op.val.val.deterministic

  globals.mem.add('observe', (expr, obs_val))
  if globals.use_traces:
    return globals.traces.observe(expr, obs_val)
  else:
    return observe_helper(expr, obs_val)

def forget(observation):
  # if using db, is a hashval
  # if using traces, is an evalnode

  if globals.use_traces:
    pass
  else:
    globals.db.remove(['obs', observation])
    globals.mem.forget(observation)

# Draws a sample value (without re-sampling other values) given its parents, and sets it
def evaluate(expr, env = None, reflip = False, stack = [], xrp_force_val = None):
  if env is None:
    env = globals.env

  if globals.use_traces:
    return globals.traces.evaluate(expression(expr), reflip)
  expr = expression(expr)

  # TODO: remove reflip
  def evaluate_recurse(subexpr, env, reflip, stack, addition):
    if type(addition) != list:
      val = evaluate(subexpr, env, reflip, stack + [addition])
    else:
      val = evaluate(subexpr, env, reflip, stack + addition)
    return val

  def binary_op_evaluate(expr, env, reflip, stack, op): 
    val1 = evaluate_recurse(expr.children[0], env, reflip, stack, 0).val
    val2 = evaluate_recurse(expr.children[1], env, reflip, stack, 1).val
    return Value(op(val1 , val2))

  def list_op_evaluate(expr, env, reflip, stack, op):
    vals = [evaluate_recurse(expr.children[i], env, reflip, stack, i).val for i in xrange(len(expr.children))]
    return Value(reduce(op, vals))

  if xrp_force_val != None: 
    assert expr.type == 'apply'

  if expr.type == 'value':
    val = expr.val
  elif expr.type == 'variable':
    var = expr.name
    (val, lookup_env) = env.lookup(var)
  elif expr.type == 'if':
    cond = evaluate_recurse(expr.cond, env, reflip, stack , -1)
    assert type(cond.val) in [bool] 
    if cond.val: 
      globals.db.unevaluate(stack + [0])
      val = evaluate_recurse(expr.true, env, reflip, stack , 1)
    else:
      globals.db.unevaluate(stack + [1])
      val = evaluate_recurse(expr.false, env, reflip, stack , 0)
  elif expr.type == 'switch':
    index = evaluate_recurse(expr.index, env, reflip, stack , -1)
    assert type(index.val) in [int] 
    assert 0 <= index.val < expr.n
    # unevaluate?
    val = evaluate_recurse(expr.children[index.val], env, reflip, stack, index.val)
  elif expr.type == 'let':
    # TODO:think more about the behavior with environments here...
    n = len(expr.vars)
    assert len(expr.expressions) == n
    values = []
    new_env = env
    for i in range(n): # Bind variables
      new_env = new_env.spawn_child()
      val = evaluate_recurse(expr.expressions[i], new_env, reflip, stack, i)
      values.append(val)
      new_env.set(expr.vars[i], values[i])
      if val.type == 'procedure':
        val.env = new_env
    new_body = expr.body.replace(new_env)
    val = evaluate_recurse(new_body, new_env, reflip, stack, -1)
  elif expr.type == 'apply':
    n = len(expr.children)
    args = [evaluate_recurse(expr.children[i], env, reflip, stack, i) for i in range(n)]
    op = evaluate_recurse(expr.op, env, reflip, stack , -2)
    if op.type == 'procedure':
      globals.db.unevaluate(stack + [-1], tuple(hash(x) for x in args))
      if n != len(op.vars):
        warnings.warn('Procedure should have %d arguments.  \nVars were \n%s\n, but children were \n%s.' % (n, op.vars, expr.children))
        assert False
      new_env = op.env.spawn_child()
      for i in range(n):
        new_env.set(op.vars[i], args[i]) 
      val = evaluate_recurse(op.body, new_env, reflip, stack, (-1, tuple(hash(x) for x in args)))
    elif op.type == 'xrp':
      globals.db.unevaluate(stack + [-1], tuple(hash(x) for x in args))

      if xrp_force_val != None: 
        assert not reflip
        if globals.db.has(stack):
          globals.db.remove(stack)
        globals.db.insert(stack, op.val, xrp_force_val, args, True) 
        val = xrp_force_val
      else:
        substack = stack + [-1, tuple(hash(x) for x in args)]
        if not globals.db.has(substack):
          if op.val.__class__.__name__ == 'mem_proc_XRP':
            val = value(op.val.apply(args, stack))
          else:
            val = value(op.val.apply(args))
          globals.db.insert(substack, op.val, val, args)
        else:
          if reflip:
            globals.db.remove(substack)
            if op.val.__class__.__name__ == 'mem_proc_XRP':
              val = value(op.val.apply(args, stack))
            else:
              val = value(op.val.apply(args))
            globals.db.insert(substack, op.val, val, args)
          else:
            (xrp, val, dbargs, is_obs_noise) = globals.db.get(substack) 
            assert not is_obs_noise
    else:
      warnings.warn('Must apply either a procedure or xrp')
  elif expr.type == 'function':
    n = len(expr.vars)
    new_env = env.spawn_child()
    for i in range(n): # Bind variables
      new_env.set(expr.vars[i], expr.vars[i])
    procedure_body = expr.body.replace(new_env)
    val = Value((expr.vars, procedure_body, stack), env)
    #TODO: SET SOME RELATIONSHIP HERE?  If body contains reference to changed var...
  elif expr.type == '=':
    val = binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x == y)
  elif expr.type == '<':
    val = binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x < y)
  elif expr.type == '>':
    val = binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x > y)
  elif expr.type == '<=':
    val = binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x <= y)
  elif expr.type == '>=':
    val = binary_op_evaluate(expr, env, reflip, stack, lambda x, y : x >= y)
  elif expr.type == '&':
    val = list_op_evaluate(expr, env, reflip, stack, lambda x, y : x & y)
  elif expr.type == '^':
    val = list_op_evaluate(expr, env, reflip, stack, lambda x, y : x ^ y)
  elif expr.type == '|':
    val = list_op_evaluate(expr, env, reflip, stack, lambda x, y : x | y)
  elif expr.type == '~':
    negval = evaluate_recurse(expr.negation, env, reflip, stack, 0).val
    val = Value(not negval)
  elif expr.type == 'add':
    val = list_op_evaluate(expr, env, reflip, stack, lambda x, y : x + y)
  elif expr.type == 'subtract':
    val1 = evaluate_recurse(expr.children[0], env, reflip, stack , 0).val
    val2 = evaluate_recurse(expr.children[1], env, reflip, stack , 1).val
    val = Value(val1 - val2)
  elif expr.type == 'multiply':
    val = list_op_evaluate(expr, env, reflip, stack, lambda x, y : x * y)
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    assert False 
  return val

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

def rerun(reflip):
# Class representing environments
  for (varname, expr) in globals.mem.assumes:
    assume_helper(varname, expr, reflip)
  for hashval in globals.mem.observes:
    (expr, obs_val) = globals.mem.observes[hashval] 
    observe_helper(expr, obs_val)

def infer():
  if globals.use_traces:
    node = globals.traces.random_node() 
    globals.traces.reflip(node)
    return
  # reflip some coin
  stack = globals.db.random_stack() 
  (xrp, val, args, is_obs_noise) = globals.db.get(stack)

  #debug = True 
  debug = False 

  old_p = globals.db.p
  old_to_new_q = - math.log(globals.db.count) 
  if debug:
    print  "old_db", globals.db

  globals.db.save()

  globals.db.remove(stack)
  if xrp.__class__.__name__ == 'mem_proc_XRP':
    new_val = xrp.apply(args, list(stack))
  else:
    new_val = xrp.apply(args)
  globals.db.insert(stack, xrp, new_val, args)

  if debug:
    print "\nCHANGING ", stack, "\n  TO   :  ", new_val, "\n"

  if val == new_val:
    return

  rerun(False)
  new_p = globals.db.p
  new_to_old_q = globals.db.uneval_p - math.log(globals.db.count) 
  old_to_new_q += globals.db.eval_p 
  if debug:
    print "new db", globals.db, \
          "\nq(old -> new) : ", old_to_new_q, \
          "q(new -> old) : ", new_to_old_q, \
          "p(old) : ", old_p, \
          "p(new) : ", new_p, \
          'log transition prob : ',  new_p + new_to_old_q - old_p - old_to_new_q , "\n"

  if old_p * old_to_new_q > 0:
    p = random.random()
    if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
      globals.db.restore()
      if debug: 
        print 'restore'
      rerun(False) 

  if debug: 
    print "new db", globals.db
    print "\n-----------------------------------------\n"

