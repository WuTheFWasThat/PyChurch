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



