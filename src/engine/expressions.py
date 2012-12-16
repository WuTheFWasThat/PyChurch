from utils.rexceptions import RException
from values import *
from xrp import *

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

  # TODO: GET RID OF THIS!
  def replace(self, env, bound = {}, help = None):
    # For traces and reduced traces, help is an evalnode
    pass
  def __eq__(self, other):
    return OpExpression('=', [self, other])
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

  def replace(self, env, bound = {}, help = None):
    return self

  def __str__(self):
    return str(self.val)

class VarExpression(Expression):
  def __init__(self, name):
    self.initialize()
    self.type = 'variable'
    self.name = name

  def replace(self, env, bound = {}, help = None):
    if self.name in bound:
      return self
    (val, lookup_env) = env.lookup(self.name)
    if help is not None:
      lookup_env.add_lookup(self.name, help)
    return ConstExpression(val)
  
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

  def replace(self, env, bound = {}, help = None):
    # TODO hmm .. replace non-bound things in op?  causes recursion to break...
    children = [x.replace(env, bound, help) for x in self.children] 
    return ApplyExpression(self.op, children)
  
  def __str__(self):
    return '(%s %s)' % (str(self.op), str(self.children))

class FunctionExpression(Expression):
  def __init__(self, vars, body):
    self.initialize()
    self.type = 'function'
    self.vars = vars
    self.body = body 

  def replace(self, env, bound = {}, help = None):
    for var in self.vars:
      bound[var] = True
    body = self.body.replace(env, bound, help)
    return FunctionExpression(self.vars, body) 
    
  def __str__(self):
    return '(lambda %s %s)' % (str(self.vars), str(self.body))

class IfExpression(Expression):
  def __init__(self, cond, true, false):
    self.initialize()
    self.type = 'if'
    self.cond = cond
    self.true = true
    self.false = false

  def replace(self, env, bound = {}, help = None):
    cond = self.cond.replace(env, bound, help)
    true = self.true.replace(env, bound, help)
    false = self.false.replace(env, bound, help)
    return IfExpression(cond, true, false)
  
  def __str__(self):
    return '(if %s %s %s)' % (str(self.cond), str(self.true), str(self.false))

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

  def replace(self, env, bound = {}, help = None):
    expressions = [x.replace(env, bound, help) for x in self.expressions]
    for var in self.vars:
      bound[var] = True
    body = self.body.replace(env, bound, help)
    return LetExpression([(self.vars[i], expressions[i]) for i in range(len(expressions))], body) 

  def __str__(self):
    return '(let %s = %s in %s)' % (str(self.vars), str(self.expressions), str(self.body))

class OpExpression(Expression):
  def __init__(self, op, children):
    self.initialize()
    self.type = op
    self.children = children 

  def replace(self, env, bound = {}, help = None):
    children = [x.replace(env, bound, help) for x in self.children]
    return OpExpression(self.type, children)
  
  def __str__(self):
    return '(' + self.type + ' ' + ' '.join([str(x) for x in self.children]) + ')'

# TODO: get rid of this stuff?

def var(v):
  return VarExpression(v) 

def op(operator, children):
  return OpExpression(operator, children) 

def ifelse(ifvar, truevar, falsevar):
  return IfExpression(ifvar, truevar, falsevar)

def apply(f, args = []):
  return ApplyExpression(f, args)

def function(vars, body):
  return FunctionExpression(vars, body)

def let(letmap, body):
  return LetExpression(letmap, body)
  ## version of let which doesn't allow recursion
  #vars = []
  #args = []
  #for (var, arg) in letmap:
  #  vars.append(var)
  #  args.append(arg)
  #return apply(function(vars, body), args)

def negation(expr):
  return OpExpression('~', [expr])

def disjunction(exprs):
  return OpExpression('|', exprs) 

def conjunction(exprs):
  return OpExpression('&', exprs)

### Values ###

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

### DISTRIBUTIONS ### 

bernoulli_xrp = ConstExpression(XRPValue(bernoulli_XRP()))
def bernoulli(p):
  return ApplyExpression(bernoulli_xrp, [p])

beta_xrp = ConstExpression(XRPValue(beta_XRP()))
def beta(a, b): 
  return ApplyExpression(beta_xrp, [a, b])

gamma_xrp = ConstExpression(XRPValue(gamma_XRP()))
def gamma(a, b): 
  return ApplyExpression(gamma_xrp, [a, b])

uniform_xrp = ConstExpression(XRPValue(uniform_discrete_XRP()))
def uniform(n = None):
  if n is None:
    return beta(int_expr(1), int_expr(1))
  else:
    return ApplyExpression(uniform_xrp, [n])

gaussian_xrp = ConstExpression(XRPValue(gaussian_XRP()))
def gaussian(mu, sigma):
  return ApplyExpression(gaussian_xrp, [mu, sigma])

