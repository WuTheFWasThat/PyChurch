from expressions import *

# The global environment
global_env = Environment() 
# Table storing, for each variable name, a (value, conditional probability) tuple
global_db = RandomDB() 
# A dictionary storing the observations of any variables
global_obs = Observations() 

def assume(varname, expression):
  global_env.set(varname, expression) 

def observe(varname, value):
  global_obs.observe(varname, value) 

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
      assert type(i.val) is int
      assert 0 <= i.val < expr.n
      el = expr.children[i.val]
      return sample(el, env)
    else:
      return expr
  elif expr.type == 'apply':
    n = len(expr.children)
    op = sample(expr.op, env)
    if op.type != 'function':
      warnings.warn('Should be applying a function!')
    for i in range(n):
      newenv = Environment(env)
      newenv.set(op.vars[i], sample(expr.children[i], env)) 
    if n == len(op.vars):
      return sample(op.body, newenv)
    else:
      return Expression(('function', op.vars[n:], sample(op.body, newenv))) 
  elif expr.type == 'function':
    if len(expr.vars) == 0:
      return expr.body
    else:
      return expr
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
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    return None

# Rejection based inference
def infer(expr, niter = 1000, burnin = 100):
  expr = validate_expr(expr)

  dict = {}
  for n in xrange(niter):
    # Re-draw from prior
    ans = sample(expr)
    flag = True
    for var in chapel_obs:
      obsval = var.getval()
      if var in chapel_stack and var.obsval != obsval:
        var.setval(obsval)
        flag = False
        break
    if flag:
      val = expr.getval()
      if val in dict:
        dict[val] += 1
      else:
        dict[val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 

def chapel_prob():
  ans = 1
  for var in chapel_stack:
    ans *= var.prob()
  return ans

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

def ifelse(ifvar, truevar, falsevar):
  ifvar = validate_expr(ifvar, global_env)
  truevar = validate_expr(truevar, global_env)
  falsevar = validate_expr(falsevar, global_env)
  return expression(('switch', ifvar, truevar, falsevar))

def switch(switchvar, array):
  return expression(('switch', switchvar, [validate_expr(x, global_env) for x in array]))
  return expr

""" TESTS """

#def forget(var):
#  return var.forget()

x = bernoulli(0.3) 
y = beta(3, 4) 
z = uniform(3) 
c = (x & y) | z
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

assume('cloudy', bernoulli(0.5))
print "here"

print sample('cloudy')
print "here"
print sample('cloudy')

assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5))) 

print global_db.db
print global_env.assignments

"""
observe('sprinkler', True)

infer('cloudy')

forget('sprinkler')

infer('cloudy')
"""

"""
def chapel_infer(variable, niter = 1000, burnin = 100):
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
