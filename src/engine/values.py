import utils.rrandom as rrandom 
import utils.rhash as rhash
from utils.rexceptions import RException
import math

# transition // for inference on theta, the internal randomness generated during init
# marg (scoring total probability of all applications);
# propose (re-propose a particular application)


# class XRP:
#   def __init__(self, initargs):
#     #self.deterministic = False
#     #self.initargs = initargs
#     #self.state = None
#     raise RException("Not implemented")
#   def transition(self, args, vals, theta, initargs):
#     raise RException("Not implemented")
#   def joint(args, vals, state, initargs, theta):
#     raise RException("Not implemented")
#   def mhprop(args, oldval, state, initargs, theta)
#     # returns newval, q->, q-<
#     raise RException("Not implemented")
#   def __str__(self):
#     return 'XRP'

class XRP:
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    raise RException("Not implemented")
  def incorporate(self, val, args = None):
    pass
  def remove(self, val, args = None):
    pass
  ## SHOULD RETURN THE LOG PROBABILITY
  def prob(self, val, args = None):
    return 0
  def weight(self, args = None):
    return 1
  def __str__(self):
    return 'XRP'
  def mhprop(oldval, args): # TODO: theta
    # TODO.  look at reflip
    self.traces.remove_xrp(self)
    self.xrp.remove(self.val, self.args)
    p_uneval = self.xrp.prob(self.val, self.args)
    val = self.xrp.apply(self.args)
    p_eval = self.xrp.prob(val, self.args)
    self.xrp.incorporate(val, self.args)
    self.traces.add_xrp(self.args, self, self.xrp.weight(self.args))


    return val, p_eval, p_uneval
  def load_from_unweighted_XRP(self):
    # TODO
    pass
  def is_mem_proc(self):
    return False
  def is_mem(self):
    return False



# ** an xrp_state node in the trace contains:
#    - state
#    - init_args
#    - theta (any internal randomness, hidden from the enclosing Church engine and not managed by it)
# 
# initialize(init_args, xrp_state) --- constructs the contents of the state to be empty but have the right shape (ie enforces "empty" sufficient statistics, e.g. 0 values for all counts for a dirichlet-discrete). also must copy init_args into the state if they are not there or equal to the current one. optionally, gets to sample some randomness and store it in theta. 
# 
# reinitialize(old_init_args, new_init_args, xrp_state) --- "propagate" a change in init_args into the state. for typical XRPs, just copy in the new args. but for XRPs that have a theta, this might be a useful way to let them know that parameters/etc have changed.
# 
# overrideable: calculate_state_weight(xrp_state, init_args) --- calculate the weight for the state of this XRP. This weight determines how often the engine will perform transitions on any internal randomness hidden inside this XRP.
# 
# sample(xrp_state, args) -> val --- applies the XRP once based on the state and some args. notice this means sample can access theta's value, and the init_args, from the xrp_state node.
# 
# incorporate(xrp_state, args, val) --- incorporates val into state (e.g. increments sufficient statistics)
# 
# remove(xrp_state, args, val) --- removes val from state (e.g. decrements sufficient statistics)
# 
# calc_application_logprob(xrp_state, args, val) --- computes log marginal probability of val given state, args, init_args ***and theta***
# 
# overrideable: calc_application_weight(init_args, xrp_state, args) --- calculates a positive integer weight used by the engine to allocate Markov chain transition steps for inference. by default, always returns a constant of 1.
# 
# overrideable: application_mhpropose(xrp_state, args, old_val) -> (new_val, log_q->, log_q<-) --- performs an MH proposal and returns the new value along with the proposal probabilities in both directions, **and adjusts the state accordingly**
# default kernel on applications: before, app_mhprop was implicitly score remove sample score incorporate. now that's the default implementation of propose, but it can be overridden.
# 
# there is no default kernel on theta, since the user who makes use of theta needs to manage it themselves. an easy kernel (assuming the user can track P(theta|initargs, rest_of_state) internally --- application_logprob already gives them P(val|theta, args, initargs, rest_of_state)) is MH from the prior: remove all applications (tracking scores), re-init, re-add, accept or reject internally. [[FIXME: note for vkm to send to dan roy --- yura add asana task once you've revised this doc --- ask about slice sampling and mem-as-uncomputable-object here]]
# 
# default propagation on argument change to any application: remove the application, score, change the value, incorporate the application, and score
# 
# default propagation on init_arg change: remove all applications (calculating scores one by one), change the init arg, reincorporate all, calculating scores accordingly

class Value:
  def initialize(self):
    # dummy values to prevent RPython typer from complaining
    self.bool = False
    self.num = 0.0 
    self.int = 0 
    self.nat = 0 
    self.xrp = XRP()
    self.vars = ['']
    self.body = None
    self.env = None
  def __hash__(self):
    raise RException("Invalid operation")
  def __repr__(self):
    return self.__str__()
  def __eq__(self, other):
    return BoolValue(self is other)
  def __gt__(self, other):
    raise RException("Invalid operation")
  def __lt__(self, other):
    raise RException("Invalid operation")
  def __ge__(self, other):
    raise RException("Invalid operation")
  def __le__(self, other):
    raise RException("Invalid operation")
  def __add__(self, other):
    raise RException("Invalid operation")
  def __sub__(self, other):
    raise RException("Invalid operation")
  def __mul__(self, other):
    raise RException("Invalid operation")
  def __div__(self, other):
    raise RException("Invalid operation")
  def __pow__(self, other):
    raise RException("Invalid operation")
  def __mod__(self, other):
    raise RException("Invalid operation")
  def __and__(self, other):
    raise RException("Invalid operation")
  def __or__(self, other):
    raise RException("Invalid operation")
  def __xor__(self, other):
    raise RException("Invalid operation")
  def __inv__(self):
    raise RException("Invalid operation")
  def __abs__(self):
    raise RException("Invalid operation")
  def __int__(self):
    raise RException("Invalid operation")
  def __round__(self):
    raise RException("Invalid operation")
  def __floor__(self):
    raise RException("Invalid operation")
  def __ceil__(self):
    raise RException("Invalid operation")
  def __nonzero__(self):
    return BoolValue((self.num > 0))
  pass 

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
    return '(lambda %s : %s)' % (str(self.vars), str(self.body))
  def __hash__(self):
    return self.hash
  def __eq__(self, other):
    return BoolValue((self.type == other.type) and (self.hash == other.hash))

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
    return BoolValue((self.type == other.type) and (self.hash == other.hash))

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
    return BoolValue((self.type == other.type) and (self.bool == other.bool))
  def __and__(self, other):
    return BoolValue(self.bool and other.bool)
  def __or__(self, other):
    return BoolValue(self.bool or other.bool)
  def __xor__(self, other):
    return BoolValue(self.bool ^ other.bool)
  def __inv__(self):
    return BoolValue(not self.bool)
  def __nonzero__(self):
    return self.bool

# TODO: use this?
def MakeNumValue(val):
  if int(val) == val:
    if val >= 0:
      return NatValue(val)
    else:
      return IntValue(val)
  else:
    return NumValue(val)

class NumValue(Value):
  def __init__(self, num):
    self.initialize()
    self.type = 'num'
    self.num = num
    self.str_hash = str(self.num)
  def __str__(self):
    return str(self.num)
  def __hash__(self):
    return rhash.hash_float(self.num)
  def __eq__(self, other):
    return BoolValue((self.type == other.type) and (self.num == other.num))
  def __gt__(self, other):
    if other.type not in ['num', 'int', 'nat']:
      raise RException("Invalid comparison")
    return BoolValue((self.num > other.num))
  def __ge__(self, other):
    if other.type not in ['num', 'int', 'nat']:
      raise RException("Invalid comparison")
    return BoolValue((self.num >= other.num))
  def __lt__(self, other):
    if other.type not in ['num', 'int', 'nat']:
      raise RException("Invalid comparison")
    return BoolValue((self.num < other.num))
  def __le__(self, other):
    if other.type not in ['num', 'int', 'nat']:
      raise RException("Invalid comparison")
    return BoolValue((self.num <= other.num))
  def __add__(self, other):
    return NumValue(self.num + other.num)
  def __sub__(self, other):
    return NumValue(self.num - other.num)
  def __mul__(self, other):
    return NumValue(self.num * other.num)
  def __div__(self, other):
    return NumValue(self.num / (other.num + 0.0))
  def __pow__(self, other):
    return NumValue(math.pow(self.num, other.num))
  def __inv__(self):
    return NumValue(- self.num)
  def __abs__(self):
    return NumValue(abs(self.num))
  #def __mod__(self, other):
  #  return NumValue(self.num % other.nat)
  def __int__(self): # round towards zero
    val = int(self.num)
    if val < 0:
      return IntValue(val)
    else:
      return NatValue(val)
  def __round__(self): # round to nearest
    if self.num <= -0.5:
      return IntValue(int(self.num - 0.5))
    elif self.num >= 0:
      return NatValue(int(self.num + 0.5))
    else:
      return NatValue(0)
  def __floor__(self):
    val = int(math.floor(self.num))
    if val < 0:
      return IntValue(val)
    else:
      return NatValue(val)
  def __ceil__(self):
    val = int(math.ceil(self.num))
    if val < 0:
      return IntValue(val)
    else:
      return NatValue(val)

  def __nonzero__(self):
    return BoolValue((self.num > 0))

class IntValue(NumValue):
  def __init__(self, num):
    self.initialize()
    self.type = 'int'
    self.int = num
    self.num = num
    self.str_hash = str(self.int)
  def __hash__(self):
    return self.int
  def __add__(self, other):
    if other.type == 'int' or other.type == 'nat':
      intval = self.int + other.int
      if intval < 0:
        return IntValue(intval)
      else:
        return NatValue(intval)
    else:
      return NumValue(self.num + other.num)
  def __sub__(self, other):
    if other.type == 'int' or other.type == 'nat':
      intval = self.int - other.int
      if intval < 0:
        return IntValue(intval)
      else:
        return NatValue(intval)
    else:
      return NumValue(self.num - other.num)
  def __mul__(self, other):
    if other.type == 'int' or other.type == 'nat':
      intval = self.int * other.int
      if intval < 0:
        return IntValue(intval)
      else:
        return NatValue(intval)
    else:
      return NumValue(self.num * other.num)
  def __pow__(self, other):
    if other.type == 'nat':
      intval = 1
      for i in range(other.int):
        intval = intval * self.int
      if intval < 0:
        return IntValue(intval)
      else:
        return NatValue(intval)
    else:
      return NumValue(math.pow(self.num, other.num))
  def __mod__(self, other):
    return NatValue(self.int % other.nat)
  def __abs__(self):
    return NatValue(abs(self.int))
  def __inv__(self):
    return IntValue(- self.int)

  
class NatValue(IntValue):
  def __init__(self, num):
    self.initialize()
    self.type = 'nat'
    self.nat = num
    self.int = num
    self.num = num
    self.str_hash = str(self.int)

