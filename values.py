import random
import warnings
import math

def value(tup):
  if tup.__class__.__name__ == 'Value':
    return tup 
  else:
    return Value(tup)

class Value:
  def __init__(self, val, env = None):
    self.val = val 
    if type(val) in [int, long]:
      #assert val >= 0
      self.type = 'int'
    elif type(val) == float:
      self.type = 'float'
      # SHOULD DISTINGUISH BETWEEN SMOOTH COUNT (POSITIVE REAL) AND PROBABILITY 
    elif type(val) == bool:
      self.type = 'bool'
    elif isinstance(val, XRP):
      self.type = 'xrp'
    else:
      (self.vars, self.body) = val 
      assert env is not None
      self.type = 'procedure'
      self.env = env 
      self.hash = hash((tuple(self.vars), self.body, frozenset(self.env.assignments.items()))) 

  def __str__(self):
    if self.type == 'procedure':
      return 'procedure%s : %s' % (str(tuple(self.vars)), str(self.body))
    elif self.type == 'xrp':
      return 'xrp %s' % (str(self.val)) 
    else:
      return str(self.val)

  def __repr__(self):
    return self.__str__()

  def __hash__(self):
    if self.type == 'procedure':
      return self.hash 
    else:
      return hash(self.val)

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
    return Value(self.val & other.val)
  def __xor__(self, other):
    return Value(self.val ^ other.val)
  def __or__(self, other):
    return Value(self.val | other.val)
  def __invert__(self):
    return Value(~self.val)
  def __nonzero__(self):
    return bool(self.val)

class XRP:
  def __init__(self, start_state, sample, prob = None, inc = None, rem = None, name = 'XRP'):
    self.sample = sample # function which takes state, args, and returns value 
    self.inc = inc # function which takes state, value, args, and returns state
    self.rem = rem # function which takes state, value, args, and returns state
    self.prob = prob # function which takes state, value, args, and returns probability
    self.state = start_state
    self.name = name
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    return sample(self.state, args)
  def incorporate(self, val, args = None):
    if self.inc != None:
      self.state = self.inc(self.state, val, args)
      return self.state
    else:
      return None
  def remove(self, val, args = None):
    if self.rem != None:
      self.state = self.rem(self.state, val, args)
      return self.state
    else:
      return None
  # SHOULD RETURN THE LOG PROBABILITY
  def prob(self, val, args = None):
    if self.prob != None:
      return self.prob(self.state, val, args)
    else:
      return 0
  def __str__(self):
    return self.name
  def __hash__(self):
    return self.hash

