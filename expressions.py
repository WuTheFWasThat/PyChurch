import random
import warnings
from values import *
from xrp import *

def expression(tup):
  if tup.__class__.__name__ == 'Expression':
    return tup 
  else:
    return Expression(tup)

#Class Class representing expressions 
class Expression:
  # Initializes an expression, taking in a type string, and a list of other parameter arguments 
  def __init__(self, tup):
    self.tup = tup
    self.hashval = random.randint(0, 2**64-1)
    self.val = None
    self.children = []
    self.parents = []
    self.dbstack = []

    if tup.__class__.__name__ == 'str':
      self.type = 'variable' 
      self.name = tup 
      return
    elif tup.__class__.__name__ == 'XRP':
      self.type = 'xrp'
      self.xrp = tup 
      return
    elif tup.__class__.__name__ != 'tuple':
      self.type = 'value'
      self.val = value(tup)
      return

    self.type = tup[0]
    if self.type in ['xrp']:
      self.type = 'xrp'
    if self.type in ['constant', 'const', 'c', 'val', 'procedure']:
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
    elif self.type in ['add', 'sum']: 
      self.type = 'add'
    elif self.type in ['subtract', 'sub']: 
      self.type = 'subtract'
    elif self.type in ['mul', 'multiply', 'product']: 
      self.type = 'multiply'
    elif self.type in ['|', 'or']:
      self.type = '|'
    elif self.type in ['&', 'and']:
      self.type = '&'
    elif self.type in ['~', 'negation', 'not']: 
      self.type = '~'

    if self.type == 'xrp':
      self.xrp = tup[1]
    elif self.type == 'value':
      if tup[1].__class__.__name__ == 'Value': 
        self.val = tup[1]
      else:
        self.val = Value(tup[1])
    elif self.type == 'variable':
      self.name = tup[1]
      if type(self.name).__name__ != 'str':
        warnings.warn('Variable must be string')
    elif self.type == 'if':
      self.cond = expression(tup[1])
      self.true = expression(tup[2])
      self.false = expression(tup[3])
    elif self.type == 'switch':
      self.index = expression(tup[1])
      self.children = [expression(x) for x in tup[2]]
      self.n = len(self.children)
    elif self.type == 'apply':
      self.op = expression(tup[1])
      if type(tup[2]) == list or type(tup[2]) == tuple:
        self.children = [expression(x) for x in tup[2]]
      else:
        if len(tup) == 3:
          self.children = [expression(tup[2])]
        else:
          self.children = []
      if self.op.type == 'function' and len(self.op.vars) < len(self.children):
        warnings.warn('Applying function to too many arguments!')
    elif self.type == 'function':
      if type(tup[1]) == list or type(tup[1]) == tuple:
        self.vars = list(tup[1])
      else:
        self.vars = [tup[1]]
      self.body = expression(tup[2])
    elif self.type in ['&', '|']:
      self.children = [expression(x) for x in tup[1]]
    elif self.type == '~':
      self.negation = expression(tup[1])
    elif self.type in ['=', '<=', '>=', '<', '>']:
      assert len(tup[1]) == 2
      self.children = [expression(x) for x in tup[1]]
    elif self.type == 'add': 
      self.children = [expression(x) for x in tup[1]]
    elif self.type == 'subtract': 
      assert len(tup[1]) == 2
      self.children = [expression(x) for x in tup[1]]
    elif self.type == 'multiply': 
      self.children = [expression(x) for x in tup[1]]
    else:
      warnings.warn('Invalid type %s' % str(self.type))
    return

  def str_op(self, children, opstring, funstring = None):
    if (len(children) < 5) or (funstring is None):
        return opstring.join(['(' + str(x) + ')' for x in self.children])
    else:
      return funstring + str(children)
    
  def __str__(self):
    if self.type == 'xrp':
      return '%s' % (str(self.xrp))
    elif self.type == 'value':
      return str(self.val)
    elif self.type == 'variable':
      return self.name
    elif self.type == 'if':
      return 'if (%s), then (%s), else (%s)' % (str(self.cond), str(self.true), str(self.false))
    elif self.type == 'switch':
      return 'switch of (%s) into (%s)' % (str(self.index), str(self.children))
    elif self.type == 'apply':
      return '(%s)%s' % (str(self.op), str(self.children))
    elif self.type == 'function':
      return 'lambda%s : (%s)' % (str(tuple(self.vars)), str(self.body))
    elif self.type in ['=', '>', '<', '>=', '<=', '&', '|']: 
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
      warnings.warn('Invalid type %s' % str(self.type))
      return 'Invalid Expression'

  def __repr__(self):
    return self.__str__()
    #return '<Expression of type %s>' % (self.type)

  def __hash__(self):
    return self.hashval

  def rehash(self):
    self.hashval = random.randint(0, 2**64-1)

  def operate(self, other, opname):
    return Expression((opname, [self, expression(other)]))

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
  def __invert__(self):
    return Expression(('not', self))

def xrp(xrp):
  return expression(('xrp', xrp)) 

bernoulli_args_xrp = bernoulli_args_XRP() 
def bernoulli(p):
  return expression(('apply',  bernoulli_args_xrp, p)) 

beta_args_xrp = beta_args_XRP() 
def beta(a, b): 
  return expression(('apply', beta_args_xrp, [a, b])) 

uniform_args_xrp = uniform_args_XRP() 
def uniform(n):
  return expression(('apply', ('xrp', uniform_args_xrp), n)) 

gaussian_args_xrp = gaussian_args_XRP() 
def gaussian(n):
  return expression(('apply', ('xrp', gaussian_args_xrp), n)) 

def constant(c):
  return expression(('value', c)) 

def var(v):
  return expression(('variable', v)) 

def apply(f, args = []):
  return expression(('apply', f, args))

def ifelse(ifvar, truevar, falsevar):
  return expression(('if', ifvar, truevar, falsevar))

def switch(switchvar, array):
  return expression(('switch', switchvar, array))

def function(vars, body):
  return expression(('function', vars, body))

