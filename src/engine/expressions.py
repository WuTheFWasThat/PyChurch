from utils.rexceptions import RException
from values import *

#Class representing expressions 
class Expression:
  # Replaces variables with the values from the environment 
  def __init__(self):
    self.hashval = rrandom.random.randbelow()

  def initialize(self):
    # dummy values to prevent RPython typer from complaining 
    self.cond = Expression()
    self.true = Expression()
    self.false = Expression()

    self.op = Expression()
    self.vars = ['']

    self.body = Expression()

    self.children = [Expression()]
    self.expressions = [Expression()]

    # initialize hash value
    self.hashval = rrandom.random.randbelow()
    pass

  def __eq__(self, other):
    return ApplyExpression(var('='), [self, other])
  def __str__(self):
    return "Expression"
  def __repr__(self):
    return self.__str__()
  def __hash__(self):
    return self.hashval

class ConstExpression(Expression):
  def __init__(self, value):
    self.initialize()
    self.val = value
    self.type = 'value'

  def __str__(self):
    return str(self.val)

class VarExpression(Expression):
  def __init__(self, name):
    self.initialize()
    self.type = 'variable'
    self.name = name

  def __str__(self):
    return self.name

class ApplyExpression(Expression):
  def __init__(self, op, children):
    self.initialize()
    self.type = 'apply'
    self.op = op
    self.children = children
    if self.op.type == 'function' and len(self.op.vars) < len(self.children):
      raise RException('Applying function to too many arguments!')

  def __str__(self):
    return '(%s %s)' % (str(self.op), str(self.children))

class FunctionExpression(Expression):
  def __init__(self, vars, body):
    self.initialize()
    self.type = 'function'
    self.vars = vars
    self.body = body 

  def __str__(self):
    return '(lambda %s %s)' % (str(self.vars), str(self.body))

# TODO: get rid of
class IfExpression(Expression):
  def __init__(self, cond, true, false):
    self.initialize()
    self.type = 'if'
    self.cond = cond
    self.true = true
    self.false = false

  def __str__(self):
    return '(if %s %s %s)' % (str(self.cond), str(self.true), str(self.false))

def ifelse(ifvar, truevar, falsevar):
  return IfExpression(ifvar, truevar, falsevar)

class LetExpression(Expression):
  def __init__(self, bindings, body):
    self.initialize()
    self.type = 'let'
    self.vars = []
    self.expressions = []
    for (var, expr) in bindings:
      self.vars.append(var)
      self.expressions.append(expr)
    self.body = body

  def __str__(self):
    return '(let %s = %s in %s)' % (str(self.vars), str(self.expressions), str(self.body))

# For convenience:

def constant(v):
  return ConstExpression(v)

def num_expr(c):
  return constant(NumValue(c))

def int_expr(c):
  return constant(IntValue(c))

def nat_expr(c):
  return constant(NatValue(c))

def bool_expr(b):
  return constant(BoolValue(b))

def xrp(xrp):
  return constant(XRPValue(xrp))

def var(v):
  return VarExpression(v) 

def apply(f, args = []):
  return ApplyExpression(f, args)

def function(vars, body):
  return FunctionExpression(vars, body)

# TODO: get rid of this, use sugar
def let(letmap, body):
  return LetExpression(letmap, body)
  ## version of let which doesn't allow recursion
  #vars = []
  #args = []
  #for (var, arg) in letmap:
  #  vars.append(var)
  #  args.append(arg)
  #return apply(function(vars, body), args)

