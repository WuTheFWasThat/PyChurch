from traces import Traces
from reducedtraces import ReducedTraces
from expressions import *
from xrp import *
from utils.rexceptions import RException

class mem_proc_XRP(XRP):
  def __init__(self, procedure):
    self.deterministic = False

    self.engine = Traces() # TODO: allow use of reduced traces, other engines
    self.engine.assume('f', ConstExpression(procedure), 0)
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.argsdict = {}
    self.hash = rrandom.random.randbelow()
    self.ids = {} # args_hash -> directive id
    self.count = {} # args_hash -> number of applications with these args
    self.id = 0
  def next_id(self):
    self.id += 1
    return self.id
    
  def apply(self, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    if args_hash not in self.count:
      self.count[args_hash] = 0
      id = self.next_id()
      val = self.engine.predict(ApplyExpression(VarExpression('f'), [ConstExpression(x) for x in args]), id)
      self.ids[args_hash] = id
    else:
      id = self.ids[args_hash]
      val = self.engine.report_value(id)
    return val
  def incorporate(self, val, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    try:
      cur_val =  self.engine.report_value(self.ids[args_hash])
      assert (val.__eq__(cur_val)).bool
    except: 
      # TODO
      raise RException("Sorry!  Propagation sometimes forces mem's value.  Need to fix implementation")
    self.count[args_hash] = self.count[args_hash] + 1
  def remove(self, val, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    cur_val =  self.engine.report_value(self.ids[args_hash])
    assert (val.__eq__(cur_val)).bool

    args_hash = ','.join([x.str_hash for x in args])
    self.count[args_hash] = self.count[args_hash] - 1
    if self.count[args_hash] == 0:
      del self.count[args_hash]
      id = self.ids[args_hash]
      self.engine.forget(id)
      del self.ids[args_hash]
    return 
  def weight(self, args):
    return 0
  def prob(self, val, args = None):
    return 0
  def theta_mh_prop(self, args_list, vals):
    old_p, old_to_new_q, new_p, new_to_old_q = self.engine.reflip(self.engine.randomKey())
    new_vals = []
    for args in args_list:
      new_vals.append(self.apply(args))
    return new_vals, old_to_new_q, new_to_old_q
  def theta_mh_restore(self):
    self.engine.restore()
  def theta_mh_keep(self):
    self.engine.keep()
  def state_weight(self):
    return self.engine.weight()
  def theta_prob(self):
    return self.engine.p
  def __str__(self):
    return '(MEM\'d %s)' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.procmem = {}
  def apply(self, args = None):
    if len(args) != 1:
      raise RException("Mem takes exactly one argument")
    procedure = args[0]
    if procedure.type != 'procedure' and procedure.type != 'xrp':
      raise RException("Can only mem procedures")
    mem_proc = mem_proc_XRP(procedure)
    return XRPValue(mem_proc)
  def incorporate(self, val, args = None):
    if val.type != 'xrp':
      raise RException("mem should only return xrps")
    if val.xrp in self.procmem:
      raise RException("mem XRP proc has already been incorporated")
    self.procmem[val.xrp] = args[0]
  # TODO: What is going on here??
  def remove(self, val, args = None):
    pass
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def __str__(self):
    return 'mem'

