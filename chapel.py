import random
import warnings

def expression(tup):
  if tup.__class__.__name__ == 'Expression':
    return tup
  else:
    return Expression(tup)

# Class representing environments
class Environment:
  def __init__(self, parent = None):
    self.parent = parent 
    self.assignments = {}
    return

  def set(self, name, expression):
    self.assignments[name] = expression

  def lookup(self, name):
    if name in self.assignments:
      return self.assignments[name]
    else:
      if self.parent is None:
        return None
      else:
        return self.parent.lookup(name)

# Class representing expressions 
class Expression:
  # Initializes an expression, taking in a type string, and a list of other parameter arguments 
  def __init__(self, tup):
    self.hashval = random.randint(0, 2**32-1)
    self.val = None
    self.children = []
    self.parents = []

    if tup.__class__.__name__ == 'str':
      self.type = 'variable' 
      self.var = tup
      return

    self.type = tup[0]
    if self.type in ['const', 'c', 'val']:
      self.type = 'constant'
    elif self.type == 'flip':
      self.type = 'bernoulli'
    elif self.type in ['var', 'v']:
      self.type = 'variable'
    elif self.type == 'op':
      self.type = 'apply'
    elif self.type == 'lambda':
      self.type = 'function'
    elif self.type == 'if':
      self.type = 'switch'
    elif self.type == '|':
      self.type = 'or'
    elif self.type == '&':
      self.type = 'and'

    if self.type == 'bernoulli':
      self.p = tup[1]
      if not 0 <= self.p <= 1: 
        warnings.warn('Probability should be a float between 0 and 1')
    elif self.type == 'beta':
      self.a = tup[1]
      self.b = tup[2]
      if self.a <= 0 or self.b <= 0:
        warnings.warn('Alpha and Beta must be > 0')
    elif self.type == 'uniform':
      self.n = tup[1]
      if type(self.n).__name__ != 'int':
        warnings.warn('Parameter N must be integer')
    elif self.type == 'constant':
      self.val = tup[1]
    elif self.type == 'variable':
      self.var = tup[1]
      if type(self.var).__name__ != 'str':
        warnings.warn('Variable must be string')
    elif self.type == 'switch':
      self.index = expression(tup[1])
      self.children = [expression(x) for x in tup[2]]
      self.n = len(self.children)
    elif self.type == 'apply':
      self.op = expression(tup[1])
      self.children = [expression(x) for x in tup[2]]
      if self.op.type == 'function' and len(self.op.vars) < len(self.children):
        warnings.warn('Applying function to too many arguments!')
    elif self.type == 'function':
      self.vars = [x for x in tup[1]]
      self.body = expression(tup[2]) 
    elif self.type == 'and':
      self.children = [expression(x) for x in tup[1]] 
    elif self.type == 'or':
      self.children = [expression(x) for x in tup[1]] 
    else:
      warnings.warn('Invalid type %s' % str(self.type))
    return 

  def __str__(self):
    if self.type == 'bernoulli':
      return 'Bernoulli(%f)' % (self.p)
    elif self.type == 'beta':
      return 'Beta(%f, %f)' % (self.a, self.b)
    elif self.type == 'uniform':
      return 'Uniform(0, %d)' % (self.n)
    elif self.type == 'constant':
      return str(self.val)
    elif self.type == 'variable':
      return self.var
    elif self.type == 'switch':
      return 'switch of (%s) into (%s)' % (str(self.index), str(self.children))
    elif self.type == 'apply':
      return 'application of (%s) to (%s)' % (str(self.op), str(self.children))
    elif self.type == 'function':
      return 'function lambda %s : (%s)' % (str(self.vars), str(self.body))
    elif self.type == 'and':
      return 'and of %s' % (str(self.children))
    elif self.type == 'or':
      return 'or of %s' % (str(self.children))
    else:
      warnings.warn('Invalid type %s' % str(self.type))
      return 'Invalid Expression'

  def __repr__(self):
    return self.__str__()
    #return '<Expression of type %s>' % (self.type)

  def __hash__(self):
    return self.hashval 

  def __and__(self, other): 
    #return Expression(('and', ('function', ['x', 'y'], ('&', (('var', 'x'), ('var', 'y')))), [self, expression(other)]))
    return Expression(('and', [self, expression(other)]))
  def __or__(self, other): 
    #return Expression(('apply', ('function', ['x', 'y'], ('|', (('var', 'x'), ('var', 'y')))), [self, expression(other)]))
    return Expression(('or', [self, expression(other)]))

global_env = Environment() 

# A table which records all random choices made
chapel_obs = []
chapel_stack = []

def assume(varname, expression):
  global_env.set(varname, expression) 

# rejection based inference
def infer(expr, niter = 1000, burnin = 100):
  if expr.__class__.__name__ != 'Expression':
    warnings.warn('Attempting to infer something which isn\'t an expression.')
    return expr

  dict = {}
  for n in xrange(niter):
    # re-draw from prior
    for var in chapel_stack:
      val = sample(var)
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

# Draws a sample value (without re-sampling other values) given its parents, and sets it
def sample(expr, env = global_env):
  #print "\nsampling %s in environment %s" % (str(expr), str(env)) 

  # need to keep track of all sampled things
  # sampled = []

  if expr.__class__.__name__ != 'Expression': 
    warnings.warn('Attempting to sample %s, which isn\'t an expression.' % str(expr))
    return expr

  if expr.type == 'constant':
    return expr
  elif expr.val != None:
    return Expression(('val', expr.val))
  elif expr.type == 'bernoulli':
    if random.random() < expr.p:
      expr.val = True  
    else:
      expr.val = False
    return Expression(('val', expr.val))
  elif expr.type == 'beta':
    expr.val = random.betavariate(expr.a, expr.b) 
    return Expression(('val', expr.val))
  elif expr.type == 'uniform':
    expr.val = random.randint(0, expr.n-1)
    return Expression(('val', expr.val))
  elif expr.type == 'variable':
    var = expr.var
    val = env.lookup(var)
    if val is None:
      return expr
    else:
      return val
  elif expr.type == 'switch':
    i = sample(expr.index, env)
    el = expr.children[i.val]
    return sample(el, env)
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
      val = sample(x, env).val
      if val is None:
        remaining.append(x)
      elif not val: 
        expr.val = False 
        return Expression(('val', expr.val))
    if remaining:
      return Expression(('and', remaining))
    else:
      expr.val = True
      return Expression(('val', expr.val))
  elif expr.type == 'or':
    remaining = []
    for x in expr.children:
      val = sample(x, env).val
      if val is None:
        remaining.append(x)
      elif val: 
        expr.val = True 
        return Expression(('val', expr.val))
    if remaining:
      return Expression(('or', remaining))
    else:
      expr.val = False
      return Expression(('val', expr.val))
  else:
    warnings.warn('Invalid expression type %s' % expr.type)
    return None


def chapel_prob():
  ans = 1
  for var in chapel_stack:
    ans *= var.prob()
  return ans

def bernoulli(p):
  expr = expression(('bernoulli', p))
  chapel_stack.append(expr)
  return expr

def beta(a, b):
  expr = expression(('beta', a, b))
  chapel_stack.append(expr)
  return expr

def constant(c):
  expr = expression(('constant', c))
  chapel_stack.append(expr)
  return expr

def var(v):
  expr = expression(('variable', v))
  chapel_stack.append(expr)
  return expr

def uniform(n):
  expr = expression(('uniform', n))
  chapel_stack.append(expr)
  return expr

def chapel_if(ifvar, tup):
  (truevar, falsevar) = tup
  expr = expression(('switch', ifvar, (truevar, falsevar)))
  chapel_stack.append(expr)
  return expr

def chapel_switch(switchvar, array):
  expr = expression(('switch', switchvar, array))
  return expr

#def forget(var):
#  return var.forget()

x = bernoulli(0.3) 
y = beta(3, 4) 
z = uniform(3) 
c = (x & y) | z
print c 
print sample(c)
#print x.val, y.val, z.val 

a = chapel_if(uniform(2), (constant(2), constant(5))) 
#a = Expression(('switch', ('uniform', 2), (('val', 2), ('constant', 5)))) 
print a
print sample(a)

b = Expression(('function', ('x', 'y', 'z'), var('x') & var('y') & var('z')))
#b = Expression(('function', ['x', 'y'], ('&', (('var', 'x'), ('var', 'y')))))
print b
print sample(b)

#d =  Expression(('op', b, [a, c, c]))
e = Expression(('op', b, [a,c]))

d = Expression(('op', e, [c])) 
print "\nd"
print d
print "\nd sample"
print sample(d)
print a.val, c.val

"""
cloudy = bernoulli(0.5)

print sample(cloudy)
print cloudy
print sample(cloudy)
print cloudy

sprinkler = chapel_if(cloudy, bernoulli(0.1), bernoulli(0.5)) 

cloudyandsprinkler = (lambda x, y : x and y) (cloudy, sprinkler)

print sprinkler, cloudyandsprinkler

#sprinkler.observe(True)

print chapel_obs

print infer(cloudy)

#sprinkler.forget()

print chapel_stack

print infer(cloudy)

"""
"""
  # Observes a value 
  def observe(self, value):
    if self.type == 'bernoulli':
      if type(value).__name__ != 'bool': 
        print "Observation inconsistent with type: %s." % (self.type)
    elif self.type == 'uniform':
      if type(value).__name__ != 'int': 
        print "Observation inconsistent with type: %s." % (self.type)
      elif value >= self.n or value < 0: 
        print "Observation inconsistent with domain: [0, %d]." % (self.n - 1)
    elif self.type == 'constant':
      warnings.warn('Attempting to observe a constant.')
      return
    #elif self.type == 'switch':
    ##   WANT TO DO THIS, BUT THERE IS PROBLEM WITH INFERENCE, THEN
    #  for var in self.children:
    #    var.observe(value)
    self.obsval = value
    chapel_obs.append(self)
    self.observed = True
    self.val = value
    return

  # Forgets the current value
  def forget(self):
    #if self.type == 'switch':
    #  for var in self.children:
    #    var.forget()
    # MUST BE CAREFUL WITH REMOVES!!
    chapel_obs.remove(self)
    self.observed = False 
    self.obsval = None
    return

  def prob(self):
    #self.getval()
    if self.type == 'bernoulli':
      if self.val:
        return self.p
      else:
        return 1.0 - self.p
    elif self.type == 'uniform':
      return (1.0 / self.n)
    elif self.type == 'constant':
      return 1.0
    elif self.type == 'switch':
      #self.el = self.children[self.index.getval()]
      if not self.val == self.el.val:
        warnings.warn('Inconsistent values.')
      return self.el.prob()
    else:
      return 1.0
      #return reduce(lambda x, y : x * y, [child.prob() for child in self.children])
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
        oldval = var.getval()
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
