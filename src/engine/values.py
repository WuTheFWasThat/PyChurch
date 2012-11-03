import utils.rrandom as rrandom 

class Value:
  pass 

class Procedure(Value):
  def __init__(self, vars, body, env):
    self.type = 'procedure'
    self.vars = vars
    self.body = body
    self.env = env 
    self.hash = rrandom.random.randint()
    self.str_hash = str(self.hash)
  def __str__(self):
    return 'procedure%s : %s' % (str(tuple(self.vars)), str(self.body))
  def __repr__(self):
    return self.__str__()
  def __hash__(self):
    return self.hash
  def __eq__(self, other):
    return (self.type == other.type) and (self.hash == other.hash)

class XRPValue(Value):
  def __init__(self, xrp):
    self.type = 'xrp'
    self.xrp = xrp 
    self.hash = rrandom.random.randint()
    self.str_hash = str(self.hash)
  def __str__(self):
    return 'xrp %s' % (str(self.xrp)) 
  def __repr__(self):
    return self.__str__()
  def __hash__(self):
    return self.hash
  def __eq__(self, other):
    return (self.type == other.type) and (self.hash == other.hash)

class BoolValue(Value):
  def __init__(self, bool):
    self.type = 'bool'
    self.bool = bool 
    self.str_hash = ("true" if self.bool else "false")
  def __str__(self):
    return str(self.bool)
  def __repr__(self):
    return self.__str__()
  def __hash__(self):
    return (1 if self.bool else 0)
  def __eq__(self, other):
    return (self.type == other.type) and (self.bool == other.bool)
  def __nonzero__(self):
    return self.bool

class NumValue(Value):
  def __init__(self, num):
    self.type = 'num'
    self.num = num
    self.str_hash = str(self.num)
  def __str__(self):
    return str(self.num)
  def __repr__(self):
    return self.__str__()
  def __hash__(self):
    return hash(self.num)
  def __eq__(self, other):
    return (self.type == other.type) and (self.num == other.num)
  def __gt__(self, other):
    return (self.type == other.type) and (self.num > other.num)
  def __ge__(self, other):
    return (self.type == other.type) and (self.num >= other.num)
  def __lt__(self, other):
    return (self.type == other.type) and (self.num < other.num)
  def __le__(self, other):
    return (self.type == other.type) and (self.num <= other.num)
  def __nonzero__(self):
    return (self.num > 0)

