import utils.rrandom as rrandom 

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
      self.hash = rrandom.random.randint()
    else:
      (self.vars, self.body) = val 
      assert env is not None
      self.type = 'procedure'
      self.env = env 
      self.hash = rrandom.random.randint()

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
    if self.type != other.type:
      return False # change this perhaps? 
    elif self.type == 'procedure' or self.type == 'xrp':
      return self.hash == other.hash
    else:
      return self.val == other.val

  def __gt__(self, other):
    assert self.type in ['int', 'float']
    assert other.type in ['int', 'float']
    return self.val > other.val

  def __lt__(self, other):
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

def check_prob(val):
  if not 0 <= val <= 1:
    print "Value %s is not a valid probability" % str(val)
    assert False
  if val == 0:
    return 2**(-32) 
  elif val == 1:
    return 1 - 2**(-32)
  return val

def check_pos(val):
  if not 0 < val: 
    print "Value %s is not positive" % str(val)
    assert False
  return

def check_nonneg(val):
  if not 0 <= val: 
    print "Value %s is negative" % str(val)
    assert False
  return

class XRP:
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    pass
  def incorporate(self, val, args = None):
    pass
  def remove(self, val, args = None):
    pass
  # SHOULD RETURN THE LOG PROBABILITY
  def prob(self, val, args = None):
    pass
  def __str__(self):
    return 'XRP'

