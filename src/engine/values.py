import utils.rrandom as rrandom 
from declarations import  Value

class Procedure(Value):
  def __init__(self, vars, body, env):
    self.initialize()
    self.type = 'procedure'
    self.vars = vars
    self.body = body
    self.env = env 
    self.hash = rrandom.random.randbelow()
    self.str_hash = str(self.hash)
  def __str__(self):
    return 'procedure%s : %s' % (str(self.vars), str(self.body))
  def __hash__(self):
    return self.hash
  def __eq__(self, other):
    return (self.type == other.type) and (self.hash == other.hash)

class XRPValue(Value):
  def __init__(self, xrp):
    self.initialize()
    self.type = 'xrp'
    self.xrp = xrp 
    self.hash = rrandom.random.randbelow()
    self.str_hash = str(self.hash)
  def __str__(self):
    return 'xrp %s' % (str(self.xrp)) 
  def __hash__(self):
    return self.hash
  def __eq__(self, other):
    return (self.type == other.type) and (self.hash == other.hash)

class BoolValue(Value):
  def __init__(self, bool):
    self.initialize()
    self.type = 'bool'
    self.bool = bool 
    self.str_hash = ("true" if self.bool else "false")
  def __str__(self):
    return str(self.bool)
  def __hash__(self):
    return (1 if self.bool else 0)
  def __eq__(self, other):
    return (self.type == other.type) and (self.bool == other.bool)
  def __nonzero__(self):
    return self.bool

class NumValue(Value):
  def __init__(self, num):
    self.initialize()
    self.type = 'num'
    self.num = num
    self.str_hash = str(self.num)
  def __str__(self):
    return str(self.num)
  def __hash__(self):
    return hash(self.num)
  def __eq__(self, other):
    return (self.type == other.type) and (self.num == other.num)
  def gt(self, other):
    return (self.type == other.type) and (self.num > other.num)
  def ge(self, other):
    return (self.type == other.type) and (self.num >= other.num)
  def lt(self, other):
    return (self.type == other.type) and (self.num < other.num)
  def le(self, other):
    return (self.type == other.type) and (self.num <= other.num)
  def __nonzero__(self):
    return (self.num > 0)

class IntValue(NumValue):
  def __init__(self, num):
    self.initialize()
    self.type = 'num'
    self.int = num
    self.num = num
    self.str_hash = str(self.int)

class NonnegIntValue(IntValue):
  def __init__(self, num):
    self.initialize()
    self.type = 'num'
    self.nonnegint = num
    self.int = num
    self.num = num
    self.str_hash = str(self.int)

