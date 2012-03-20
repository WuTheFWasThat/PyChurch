from expressions import *

# The global environment
global_env = Environment() 
# Table storing, for each variable name, a (value, conditional probability) tuple
global_db = RandomDB() 
# A dictionary storing the observations of any variables
global_obs = Observations() 

def assume(varname, expression):
  global_env.set(varname, expression) 
  #global_env.set(varname, sample(expression)) # NOT SURE WHAT IS GOING ON HERE 

def observe(expression, value):
  #noisy_expression = 
  global_obs.observe(expression, value) 

def forget(varname):
  global_obs.forget(varname) 

def validate_expr(expr, env = global_env):
  if expr.__class__.__name__ == 'str': 
    expr = env.lookup(expr)
    if expr is None:
      warnings.warn('Attempting to sample a variable %s which is not instantiated' % expr)
      assert False 
    return expr 
  elif expr.__class__.__name__ != 'Expression': 
    warnings.warn('Reference to %s, which isn\'t an expression or variable name.' % str(expr))
    assert False 
  return expr

# Draws a sample value (without re-sampling other values) given its parents, and sets it
def sample(expr, env = global_env):
  expr = validate_expr(expr, env)

  if global_db.has(expr):
    return Expression(('val', global_db.get_val(expr)))

  if expr.type == 'constant':
    return expr
  elif expr.type == 'bernoulli':
    if random.random() < expr.p:
      global_db.insert(expr, True, expr.p)
      return Expression(('val', True)) 
    else:
      global_db.insert(expr, False, 1 - expr.p)
      return Expression(('val', False)) 
  elif expr.type == 'beta':
    val = random.betavariate(expr.a, expr.b) 
    global_db.insert(expr, val, 0) # SHOULD IT HAVE THE PDF?  BUT THEN WHAT IF A SWITCH COMPARES IT TO SOMETHING ELSE?
    return Expression(('val', val)) 
  elif expr.type == 'uniform':
    val = random.randint(0, expr.n-1)
    global_db.insert(expr, val, (1.0/expr.n)) 
    return Expression(('val', val)) 
  elif expr.type == 'variable':
    var = expr.var
    val = env.lookup(var)
    if val is None:
      return expr
    else:
      return val
  elif expr.type == 'switch':
    i = sample(expr.index, env)
    if i.type == 'constant':
      assert 0 <= i.val.val < expr.n
      el = expr.children[int(i.val.val)]
      return sample(el, env)
    else:
      return expr
  elif expr.type == 'apply':
    n = len(expr.children)
    if expr.op.type != 'constant':
      op = sample(expr.op, env)
    else:
      op = expr.op
    assert op.type == 'constant' and op.val.type == 'procedure'
    for i in range(n):
      newenv = Environment(env)
      newenv.set(op.val.vars[i], sample(expr.children[i], env)) 
    newbody = sample(op.val.body, newenv) 
    if n == len(op.val.vars):
      return newbody 
    else:
      vars = op.val.vars[n:]
      return Expression(('val', Value((vars, newbody), env)))
  elif expr.type == 'function':
    procedure_body = sample(expr.body, env)
    procedure = Value((expr.vars, procedure_body), env)
    # assert that the procedure has no unbound variables that aren't in expr.vars
    return Expression(('val', procedure))
  elif expr.type == 'and':
    remaining = []
    for x in expr.children:
      child = sample(x, env)
      if child.type != 'constant':
        remaining.append(x)
      elif not child.val: 
        return Expression(('val', False))
    if len(remaining) > 1:
      return Expression(('and', remaining))
    elif len(remaining) == 1:
      return remaining[0]
    else:
      return Expression(('val', True))
  elif expr.type == 'or':
    remaining = []
    for x in expr.children:
      child = sample(x, env)
      if child.type != 'constant':
        remaining.append(x)
      elif not child.val: 
        return Expression(('val', True))
    if len(remaining) > 1:
      return Expression(('or', remaining))
    elif len(remaining) == 1:
      return remaining[0]
    else:
      return Expression(('val', False))
  elif expr.type == 'not':
    neg = sample(expr.negation)
    if neg.type == 'constant':
      return Expression(('val', ~neg.val))
    else:
      return expr
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    return None

# Rejection based inference
def infer(expr, niter = 1000, burnin = 100):
  expr = validate_expr(expr)

  dict = {}
  for n in xrange(niter):
    # Re-draw from prior
    global_db.clear()
    ans = sample(expr) 
    assert ans.type == 'constant'

    # Reject if observations untrue
    flag = True
    for obs_expr in global_obs.obs:
      obsval = sample(obs_expr)
      if obsval.type != 'constant' or obsval.val != global_obs.get(obs_expr):
        flag = False
        break

    if flag:
      if ans.val.val in dict:
        dict[ans.val.val] += 1
      else:
        dict[ans.val.val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 

def bernoulli(p):
  return expression(('bernoulli', p))
  return expr

def beta(a, b):
  return expression(('beta', a, b))

def constant(c):
  return expression(('constant', c))

def var(v):
  return expression(('variable', v))

def uniform(n):
  return expression(('uniform', n))

def apply(f, args):
  f = validate(f)
  args = [validate(x) for x in args]
  return expression(('apply', f, args))

def ifelse(ifvar, truevar, falsevar):
  ifvar = validate_expr(ifvar, global_env)
  truevar = validate_expr(truevar, global_env)
  falsevar = validate_expr(falsevar, global_env)
  return expression(('switch', ifvar, truevar, falsevar))

def switch(switchvar, array):
  return expression(('switch', switchvar, [validate_expr(x, global_env) for x in array]))
  return expr

""" TESTS """

""" testing expressions and sampling"""

#def forget(var):
#  return var.forget()

x = bernoulli(0.3) 
y = beta(3, 4) 
z = uniform(3) 
c = (~x & y) | z
print '\nSample of\n%s\n= %s\n' % (str(c), str(sample(c)))
#print x.val, y.val, z.val 

a = ifelse(uniform(2), constant(2), constant(5)) 
#a = Expression(('switch', ('uniform', 2), (('val', 2), ('constant', 5)))) 
print '\nSample of\n%s\n= %s\n' % (str(a), str(sample(a)))

b = Expression(('f', ('x','y','z'), var('x') & var('y') & var('z')))
#b = Expression(('function', ['x', 'y'], ('&', (('var', 'x'), ('var', 'y')))))
print '\nSample of\n%s\n= %s\n' % (str(b), str(sample(b)))

e = Expression(('apply', b, [a,c]))
d = Expression(('apply', e, [c])) 
#d =  Expression(('apply', b, [a, c, c]))
print '\nSample of\n%s\n= %s\n' % (str(d), str(sample(d)))

#print a.val, c.val

""" testing inference"""

assume('cloudy', bernoulli(0.5))

print sample('cloudy')
global_db.clear()
print sample('cloudy')

assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5))) 

observe('sprinkler', True)

print infer('cloudy')

forget('sprinkler')

print infer('cloudy')

"""
def infer(variable, niter = 1000, burnin = 100):
  if variable.__class__.__name__ != 'Expression':
    warnings.warn('Attempting to infer something which isn\'t an expression.')
    return variable

  dict = {}
  for n in xrange(niter):
    # re-draw from prior
    for var in chapel_stack:
      if var not in chapel_obs:
        var.sample()
    for t in xrange(burnin):
      i = random.randint(0, len(chapel_stack) -1)
      var = chapel_stack[i]
      if not var.observed:
        oldp = chapel_prob()
        oldval = var.get_val()
        var.sample()
        if random.random() + (chapel_prob() / oldp) < 1:
          var.setval(oldval) 
    flag = True
    for var in chapel_obs:
      obsval = var.getval()
      if var in chapel_stack and var.getval() != obsval:
        var.setval(obsval)
        flag = False
        break
    if flag:
      val = variable.getval()
      if val in dict:
        dict[val] += 1
      else:
        dict[val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 
"""
