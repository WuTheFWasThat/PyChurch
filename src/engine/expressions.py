from values import *
from xrp import *

#Class representing expressions 
class Expression:
  # Initializes an expression, taking in a type string, and a list of other parameter arguments 
  def __init__(self, tup):
    self.tup = tup
    self.hashval = rrandom.random.randint()
    self.val = None
    self.children = []
    self.parents = []

    self.type = tup[0]
    if self.type in ['value', 'constant', 'const', 'c', 'val', 'procedure', 'xrp']:
      self.type = 'value'
    elif self.type in ['variable', 'var', 'v']:
      self.type = 'variable'
    elif self.type in ['apply', 'a']:
      self.type = 'apply'
    elif self.type in ['function', 'lambda', 'f']:
      self.type = 'function'
    elif self.type in ['cond', 'if', 'ifelse']:
      self.type = 'if'
    elif self.type in ['case', 'switch']:
      self.type = 'switch'
    elif self.type in ['let']:
      self.type = 'let'
    elif self.type in ['eq', 'equals', 'e', '=']: 
      self.type = '='
    elif self.type in ['l', 'less', '<']: 
      self.type = '<'
    elif self.type in ['g', 'greater', '>']: 
      self.type = '>'
    elif self.type in ['le', 'lessequals', '<=']: 
      self.type = '<='
    elif self.type in ['ge', 'greaterequals', '>=']: 
      self.type = '>='
    elif self.type in ['+', 'add', 'sum']: 
      self.type = 'add'
    elif self.type in ['-', 'subtract', 'sub']: 
      self.type = 'subtract'
    elif self.type in ['*', 'mul', 'multiply', 'product']: 
      self.type = 'multiply'
    elif self.type in ['|', 'or', 'disjunction']:
      self.type = '|'
    elif self.type in ['&', 'and', 'conjunction']:
      self.type = '&'
    elif self.type in ['^', 'xor']:
      self.type = '^'
    elif self.type in ['~', 'negation', 'not']: 
      self.type = '~'

    if self.type == 'value':
      if tup[1].__class__.__name__ == 'Value': 
        self.val = tup[1]
      else:
        self.val = Value(tup[1])
    elif self.type == 'variable':
      self.name = tup[1]
    elif self.type == 'if':
      self.cond = tup[1]
      self.true = tup[2]
      self.false = tup[3]
    elif self.type == 'switch':
      self.index = tup[1]
      self.children = tup[2] # list of expressions
      self.n = len(self.children)
    elif self.type == 'let':
      self.vars = []
      self.expressions = []
      for (var, expr) in tup[1]:
        self.vars.append(var)
        self.expressions.append(expr)
      self.body = tup[2]
    elif self.type == 'apply':
      self.op = tup[1]
      self.children = tup[2] # list of expressions
      if self.op.type == 'function' and len(self.op.vars) < len(self.children):
        raise Exception('Applying function to too many arguments!')
    elif self.type == 'function':
      self.vars = tup[1]
      self.body = tup[2]
    elif self.type in ['&', '|', '^']:
      self.children = tup[1] # list of expressions
    elif self.type == '~':
      self.negation = tup[1] # list of expressions
    elif self.type in ['=', '<=', '>=', '<', '>']:
      assert len(tup[1]) == 2
      self.children = tup[1] # list of expressions
    elif self.type == 'add': 
      self.children = tup[1] # list of expressions
    elif self.type == 'subtract': 
      assert len(tup[1]) == 2
      self.children = tup[1] # list of expressions
    elif self.type == 'multiply': 
      self.children = tup[1] # list of expressions
    else:
      raise Exception('Invalid type %s' % str(self.type))
    return

  # Replaces variables with the values from the environment 
  def replace(self, env, bound = {}):
    if self.type == 'value':
      return self
    elif self.type == 'variable':
      if self.name in bound:
        return self
      (val, lookup_env) = env.lookup(self.name)
      if val is None:
        return self
      else:
        return Expression(('value', val))
    elif self.type == 'if':
      cond = self.cond.replace(env, bound)
      true = self.true.replace(env, bound)
      false = self.false.replace(env, bound)
      return Expression(('if', cond, true, false)) 
    elif self.type == 'switch':
      index = self.index.replace(env, bound)
      children = [x.replace(env, bound) for x in self.children]
      return Expression(('switch', index, children)) 
    elif self.type == 'let':
      expressions = [x.replace(env, bound) for x in self.expressions]
      for var in self.vars:
        bound[var] = True
      body = self.body.replace(env, bound)
      return Expression(('let', [(self.vars[i], expressions[i]) for i in range(len(expressions))], body)) 
    elif self.type == 'apply':
      # hmm .. replace non-bound things in op?  causes recursion to break...
      children = [x.replace(env, bound) for x in self.children] 
      return Expression(('apply', self.op, children)) 
    elif self.type == 'function':
      # hmm .. replace variables?  maybe wipe those assignments out ...
      children = [x.replace(env, bound) for x in self.children] 
      for var in self.vars: # do we really want this?  probably.  (this is the only reason we use 'bound' at all
        bound[var] = True
      body = self.body.replace(env, bound)
      return Expression(('function', self.vars, body)) 
    elif self.type in ['=', '<', '>', '>=', '<=', '&', '^', '|', 'add', 'subtract', 'multiply']:
      children = [x.replace(env, bound) for x in self.children]
      return Expression((self.type, children))
    elif self.type == '~':
      return Expression(('not', self.negation.replace(env, bound)))
    else:
      raise Exception('Invalid expression type %s' % self.type)
  
  def str_op(self, children, opstring, funstring = None):
    if (len(children) < 5) or (funstring is None):
        return opstring.join(['(' + str(x) + ')' for x in self.children])
    else:
      return funstring + str(children)
    
  def __str__(self):
    if self.type == 'value':
      return str(self.val)
    elif self.type == 'variable':
      return self.name
    elif self.type == 'if':
      return 'if (%s), then (%s), else (%s)' % (str(self.cond), str(self.true), str(self.false))
    elif self.type == 'switch':
      return 'switch of (%s) into %s' % (str(self.index), str(self.children))
    elif self.type == 'let':
      return 'let %s = %s in (%s)' % (str(self.vars), str(self.expressions), str(self.body))
    elif self.type == 'apply':
      return '(%s)%s' % (str(self.op), str(self.children))
    elif self.type == 'function':
      return 'lambda%s : (%s)' % (str(tuple(self.vars)), str(self.body))
    elif self.type in ['=', '>', '<', '>=', '<=', '&', '^', '|']: 
      return self.str_op(self.children, self.type)
    elif self.type == '~':
      return '~(%s)' % (str(self.negation))
    elif self.type == 'add': 
      return self.str_op(self.children, '+', 'sum')
    elif self.type == 'subtract': 
      return self.str_op(self.children, '-', 'sub')
    elif self.type == 'multiply': 
      return self.str_op(self.children, '*', 'product')
    else:
      raise Exception('Expression with invalid type %s' % str(self.type))

  def __repr__(self):
    return self.__str__()
    #return '<Expression of type %s>' % (self.type)

  def __hash__(self):
    return self.hashval

  def rehash(self):
    self.hashval = rrandom.random.randint()

  def operate(self, other, opname):
    return Expression((opname, [self, other]))

  def __eq__(self, other):
    return self.operate(other, '=')
  def __lt__(self, other):
    return self.operate(other, '<')
  def __le__(self, other):
    return self.operate(other, '<=')
  def __gt__(self, other):
    return self.operate(other, '>')
  def __ge__(self, other):
    return self.operate(other, '>=')
  def __add__(self, other):
    return self.operate(other, 'add')
  def __sub__(self, other):
    return self.operate(other, 'subtract')
  def __mul__(self, other):
    return self.operate(other, 'multiply')
  def __and__(self, other):
    return self.operate(other, 'and')
  def __or__(self, other):
    return self.operate(other, 'or')
  def __xor__(self, other):
    return self.operate(other, 'xor')
  def __invert__(self):
    return Expression(('not', self))

def constant(c):
  return Expression(('value', Value(c))) 

def var(v):
  return Expression(('variable', v)) 

def apply(f, args = []):
  return Expression(('apply', f, args))

def ifelse(ifvar, truevar, falsevar):
  return Expression(('if', ifvar, truevar, falsevar))

def switch(switchvar, array):
  return Expression(('switch', switchvar, array))

def let(letmap, body):
  return Expression(('let', letmap, body))

def function(vars, body):
  return Expression(('function', vars, body))

def negation(expr):
  return Expression(('not', expr)) 

def disjunction(exprs):
  return Expression(('or', exprs)) 

def conjunction(exprs):
  return Expression(('or', exprs)) 

### XRP ###

def xrp(xrp):
  return Expression(('xrp', Value(xrp))) 

### DISTRIBUTIONS ### 

bernoulli_args_xrp = Expression(('xrp', Value(bernoulli_args_XRP())))
def bernoulli(p):
  return Expression(('apply', bernoulli_args_xrp, [p])) 

beta_args_xrp = Expression(('xrp', Value(beta_args_XRP())))
def beta(a, b): 
  return Expression(('apply', beta_args_xrp, [a, b]))

gamma_args_xrp = Expression(('xrp', Value(gamma_args_XRP())))
def gamma(a, b): 
  return Expression(('apply', gamma_args_xrp, [a, b]))

uniform_args_xrp = Expression(('xrp', Value(uniform_args_XRP())))
def uniform(n = None):
  if n is None:
    return beta(constant(1), constant(1))
  else:
    return Expression(('apply', uniform_args_xrp, [n]))

gaussian_args_xrp = Expression(('xrp', Value(gaussian_args_XRP())))
def gaussian(mu, sigma):
  return Expression(('apply', gaussian_args_xrp, [mu, sigma]))

