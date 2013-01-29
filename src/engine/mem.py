from traces import Traces
from reducedtraces import ReducedTraces
from expressions import *
from utils.rexceptions import RException

class mem_proc_XRP(XRP):
  def __init__(self, procedure, engine_type = "traces"):
    self.initialize()
    self.resample = True

    if engine_type == "traces":
      self.engine = Traces()
    elif engine_type == "reduced traces":
      self.engine = ReducedTraces()
    else:
      raise RException("Engine type not implemented")
    self.engine.assume('f', ConstExpression(procedure), 0)
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.argsdict = {}
    self.hash = rrandom.random.randbelow()
    self.ids = {} # args_hash -> directive id
    self.count = {} # args_hash -> number of applications with these args
    self.links = {} # args_hash -> set of evalnodes
    self.id = 0

  def next_id(self):
    self.id += 1
    return self.id
    
  def sample(self, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    if args_hash not in self.count:
      self.count[args_hash] = 0
      id = self.next_id()
      val = self.engine.predict(ApplyExpression(VarExpression('f'), [ConstExpression(x) for x in args]), id)
      self.engine.predicts[id].out_link = self
      self.ids[args_hash] = id
    else:
      id = self.ids[args_hash]
      # TODO get actual node, and evaluate (without reflip)
      val = self.engine.report_value(id)
    return val

  def incorporate(self, val, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    if not args_hash in self.ids:
      raise RException("Engine bug in mem.  Did not sample before incorporating?")
    # TODO get actual node, and evaluate (without reflip)
    cur_val =  self.engine.report_value(self.ids[args_hash])
    if not (val.__eq__(cur_val)).bool:
      raise RException("Engine bug in mem.  Incongruous values")
    self.count[args_hash] = self.count[args_hash] + 1

  def remove(self, val, args = None):
    args_hash = ','.join([x.str_hash for x in args])
    cur_val =  self.engine.report_value(self.ids[args_hash])
    #assert (val.__eq__(cur_val)).bool // Can be false when propagating new value!
    args_hash = ','.join([x.str_hash for x in args])
    self.count[args_hash] = self.count[args_hash] - 1
    if self.count[args_hash] == 0:
      # TODO unevaluate the node
      pass # self.engine.predicts[self.ids[args_hash]].

  def unsample(self, val, args):
    if self.count[args_hash] == 0:
      id = self.ids[args_hash]
      del self.count[args_hash]
      self.engine.forget(id)
      del self.ids[args_hash]

  def weight(self, args):
    return 0

  def prob(self, val, args = None):
    return 0

  def theta_mh_prop(self, args_list, vals):
    old_p, old_to_new_q, new_p, new_to_old_q = self.engine.reflip(self.engine.randomKey())
    new_vals = []
    for args in args_list:
      new_vals.append(self.sample(args))
    return new_vals, old_to_new_q, new_to_old_q

  def theta_mh_restore(self):
    self.engine.restore()

  def theta_mh_keep(self):
    self.engine.keep()

  def state_weight(self):
    return self.engine.weight()

  def theta_prob(self):
    return self.engine.p

  def make_link(self, evalnode, args):
    args_hash = ','.join([x.str_hash for x in args])
    if args_hash not in self.links:
      self.links[args_hash] = {}
    self.links[args_hash][evalnode] = True

  def break_link(self, evalnode, args):
    args_hash = ','.join([x.str_hash for x in args])
    if args_hash not in self.links:
      raise RException("Something went wrong breaking links in mem")
    if evalnode not in self.links[args_hash]:
      raise RException("Something went wrong breaking links in mem, 2")
    del self.links[args_hash][evalnode]
    evalnode.out_link = None

  def propagate_link(self, evalnode, val, restore_inactive):
    args_hash = ','.join([x.str_hash for x in evalnode.args])
    for new_evalnode in self.links[args_hash]:
      new_evalnode.val = val
      new_evalnode.propagate_up(restore_inactive)

  def __str__(self):
    return '(MEM\'d %s)' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self, engine_type = "traces"):
    self.initialize()
    self.resample = True
    self.engine_type = engine_type
  def sample(self, args = None):
    if len(args) != 1:
      raise RException("Mem takes exactly one argument")
    procedure = args[0]
    if procedure.type != 'procedure' and procedure.type != 'xrp':
      raise RException("Can only mem procedures")
    mem_proc = mem_proc_XRP(procedure, self.engine_type)
    return XRPValue(mem_proc)
  def incorporate(self, val, args = None):
    pass
  def remove(self, val, args = None):
    pass
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def __str__(self):
    return 'mem'

