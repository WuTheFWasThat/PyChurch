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
    elif type(val) in [float]:
      self.type = 'float'
      # TODO: SHOULD DISTINGUISH BETWEEN SMOOTH COUNT (POSITIVE REAL) AND PROBABILITY 
    elif type(val) == bool:
      self.type = 'bool'
    elif isinstance(val, XRP):
      self.type = 'xrp'
      self.hash = random.randint(0, 2**32-1)
    else:
      # TODO: get rid of stack
      (self.vars, self.body, self.stack) = val 
      assert env is not None
      self.type = 'procedure'
      self.env = env 
      self.hash = random.randint(0, 2**32-1)

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
    if self.type == 'procedure' or self.type == 'xrp':
      return self.hash
    else: # Default hash is by identity, for XRPs
      return hash(self.val)

  def __eq__(self, other):
    other = value(other)
    if self.type != other.type:
      return False # change this perhaps? 
    elif self.type == 'procedure' or self.type == 'xrp':
      return self.hash == other.hash
    else:
      return self.val == other.val

  def __gt__(self, other):
    other = value(other)
    assert self.type in ['int', 'float']
    assert other.type in ['int', 'float']
    return self.val > other.val

  def __lt__(self, other):
    other = value(other)
    assert self.type in ['int', 'float']
    assert other.type in ['int', 'float']
    return self.val < other.val

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

def check_num(val):
  if not type(val) in [int, float]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  return

def check_int(val):
  if not type(val) in [int]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  return

def check_nat(val):
  if not type(val) in [int]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  if not 0 < val: 
    print "Value %s is not positive" % str(val)
    assert False
  return
  
def check_bool(val):
  if not type(val) in [bool]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  return

def check_prob(val):
  if not type(val) in [int, float]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  if not 0 <= val <= 1:
    print "Value %s is not a valid probability" % str(val)
    assert False
  if val == 0:
    return 2**(-32) 
  elif val == 1:
    return 1 - 2**(-32)
  return val

def check_pos(val):
  if not type(val) in [int, float]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  if not 0 < val: 
    print "Value %s is not positive" % str(val)
    assert False
  return

def check_nonneg(val):
  if not type(val) in [int, float]:
    print "Value %s has type %s" % (str(val), str(type(val))) 
    assert False
  if not 0 <= val: 
    print "Value %s is negative" % str(val)
    assert False
  return

class XRP:
  def __init__(self, start_state, sample, prob = None, inc = None, rem = None, name = 'XRP', deterministic = False):
    self.deterministic = deterministic
    self.sample = sample # function which takes state, args, and returns value 
    self.inc = inc # function which takes state, value, args, and returns state
    self.rem = rem # function which takes state, value, args, and returns state
    self.prob = prob # function which takes state, value, args, and returns probability
    self.state = start_state
    self.name = name
    return
  def apply(self, args = None):
    return sample(self.state, args)
  def incorporate(self, val, args = None):
    if hasattr(self, 'inc'):
      self.state = self.inc(self.state, val, args)
      return self.state
    else:
      return None
  def remove(self, val, args = None):
    if hasattr(self, 'rem'):
      self.state = self.rem(self.state, val, args)
      return self.state
    else:
      return None
  # SHOULD RETURN THE LOG PROBABILITY
  def prob(self, val, args = None):
    if hasattr(self, 'prob'):
      return self.prob(self.state, val, args)
    else:
      return 0
  def __str__(self):
    return self.name

