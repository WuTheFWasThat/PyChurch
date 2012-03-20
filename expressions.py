import random
import warnings

class Value:
  def __init__(self, val, env = None):
    self.val = val
    if type(val) == int:
      self.type = 'int'
    elif type(val) == float:
      self.type = 'float'
    elif type(val) == bool:
      self.type = 'bool'
    else:
      assert val.__class__.__name__ == 'Expression'
      assert val.type == 'function'
      assert env is not None
      self.type = 'procedure'
      self.env = env 

  def __str__(self):
    return str(self.val)
  def __repr__(self):
    return str(self.val)

  def __cmp__(self, other):
    if other.__class__.__name__ == 'Value':
      if (self.val == other.val):
        return 0
      elif (self.val > other.val):
        return 1
      else:
        return -1
    else:
      if (self.val == other):
        return 0
      elif (self.val > other):
        return 1
      else:
        return -1

  def __and__(self, other):
    return Value(self.val & other.value)
  def __xor__(self, other):
    return Value(self.val ^ other.value)
  def __or__(self, other):
    return Value(self.val | other.value)
  def __invert__(self):
    return Value(~self.val)


# Class representing observations
class Observations:
  def __init__(self):
    self.obs = {}

  def observe(self, expr, val):
    if val.__class__.__name__ == 'Value':
      self.obs[expr] = val
    else:
      self.obs[expr] = Value(val)

  def has(self, expr):
    return expr in self.obs

  def get(self, expr):
    return self.obs[expr]

  def forget(self, expr):
    if self.has(expr):
      del self.obs[expr]

# Class representing random db
class RandomDB:
  def __init__(self):
    self.db = {} 
    return

  def has(self, expression):
    return expression in self.db

  def insert(self, expression, value, probability):
    if value.__class__.__name__ != 'Value':
      value = Value(value)
    self.db[expression] = (value, probability)

  def get(self, expression):
    return self.db[expression]

  def get_val(self, expression):
    return self.db[expression][0]

  def get_prob(self, expression):
    return self.db[expression][1]

  def prob(self):
    ans = 1
    for choice in self.db:
      ans *= self.db[choice][1]
    return ans

  def clear(self):
    self.db = {}

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

def expression(tup):
  if tup.__class__.__name__ == 'Expression':
    return tup 
  else:
    return Expression(tup)

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
    elif tup.__class__.__name__ != 'tuple':
      self.type = 'constant'
      self.val = tup
      return

    self.type = tup[0]
    if self.type in ['const', 'c', 'val']:
      self.type = 'constant'
    elif self.type in ['flip']:
      self.type = 'bernoulli'
    elif self.type in ['unif']:
      self.type = 'uniform'
    elif self.type in ['beta_dist']:
      self.type = 'beta'
    elif self.type in ['var', 'v']:
      self.type = 'variable'
    elif self.type in ['a']:
      self.type = 'apply'
    elif self.type in ['lambda', 'f']:
      self.type = 'function'
    elif self.type in ['if', 'cond', 'ifelse']:
      self.type = 'switch'
    elif self.type in ['|']:
      self.type = 'or'
    elif self.type in ['&']:
      self.type = 'and'
    elif self.type in ['~', 'negation']: 
      self.type = 'not'

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
      if tup[1].__class__.__name__ == 'Value': 
        self.val = tup[1]
      else:
        self.val = Value(tup[1])
    elif self.type == 'variable':
      self.var = tup[1]
      if type(self.var).__name__ != 'str':
        warnings.warn('Variable must be string')
    elif self.type == 'switch':
      self.index = expression(tup[1])
      if len(tup) == 3:
        self.children = [expression(x) for x in tup[2]]
      elif len(tup) == 4:
        self.children = [expression(tup[2]), expression(tup[3])]
      else:
        warnings.warn('Switch must either take a list of children or 2 children, after the index argument')
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
    elif self.type == 'not':
      self.negation = tup[1]
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
      return '(%s)(%s)' % (str(self.op), str(self.children))
    elif self.type == 'function':
      return 'function lambda %s : (%s)' % (str(tuple(self.vars)), str(self.body))
    elif self.type == 'and':
      return 'and%s' % (str(tuple(self.children)))
    elif self.type == 'or':
      return 'or%s' % (str(tuple(self.children)))
    elif self.type == 'not':
      return 'not %s' % (str(self.negation))
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
  def __invert__(self):
    #return Expression(('apply', ('function', ['x', 'y'], ('|', (('var', 'x'), ('var', 'y')))), [self, expression(other)]))
    return Expression(('not', self))

