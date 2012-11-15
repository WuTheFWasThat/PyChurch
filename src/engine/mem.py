import directives 
from traces import EvalNode
from reducedtraces import ReducedEvalNode
from expressions import *
from xrp import *
from utils.rexceptions import RException

# THIS XRP IMPLEMENTATION IS NOT INDEPENDENT OF DIRECTIVES IMPLEMENTATION 
class mem_proc_XRP(XRP):
  def __init__(self, procedure):
    self.deterministic = True
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.argsdict = {}
    self.hash = rrandom.random.randbelow()
  def apply(self, args = None):
    return self.apply_mem(args)
  def apply_mem(self, args = None, help = None):
    if len(args) != self.n:
      raise RException("Gave a mem'd procedure with %d arguments %d arguments instead" % (self.n, len(args)))
    addition = ','.join([x.str_hash for x in args])
    if directives.engine_type == 'reduced traces':
      if addition not in self.argsdict:
        evalnode = ReducedEvalNode(directives.engine, directives.engine.env, ApplyExpression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]))
        evalnode.mem = True
        self.argsdict[addition] = evalnode
        val = evalnode.evaluate()
      else:
        evalnode = self.argsdict[addition]
        val = evalnode.val
      return val
    elif directives.engine_type == 'traces':
      if addition not in self.argsdict:
        evalnode = EvalNode(directives.engine, directives.engine.env, ApplyExpression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]))
        evalnode.mem = True
        self.argsdict[addition] = evalnode
      else:
        evalnode = self.argsdict[addition]
      val = evalnode.evaluate(False)
      return val
    elif directives.engine_type == 'randomdb':
      # help is call_stack for db
      if addition in self.argsdict:
        (val, count) = self.argsdict[addition]
      else:
        val = directives.db.evaluate(ApplyEpxression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]), stack = help + [-1, 'mem', self.procedure.hash, addition]) 
    else:
      raise RException("Invalid engine type %s" % directives.engine_type)
    return val
  def incorporate(self, val, args = None):
    return self.incorporate_mem(val, args)
  def incorporate_mem(self, val, args = None, help = None):
    addition = ','.join([x.str_hash for x in args])
    if directives.engine_type == 'reduced traces':
      # help is evalnode
      if addition not in self.argsdict:
        raise RException("Should only incorporate additions that have already been applied")
      evalnode = self.argsdict[addition]
      if help not in evalnode.mem_calls:
        evalnode.mem_calls[help] = 1
      else:
        evalnode.mem_calls[help] += 1
    elif directives.engine_type == 'traces':
      # help is evalnode
      if addition not in self.argsdict:
        raise RException("Should only incorporate additions that have already been applied")
      evalnode = self.argsdict[addition]
      if help in evalnode.mem_calls:
        raise RException("Should only add a given evalnode once, as a mem_call")
      evalnode.mem_calls[help] = True
    elif directives.engine_type == 'randomdb':
      if addition not in self.argsdict:
        self.argsdict[addition] = (val, 1)
      else:
        (oldval, oldcount) = self.argsdict[addition]
        if oldval != val:
          raise RException("Old mem value disagrees with new mem value")
        self.argsdict[addition] = (oldval, oldcount + 1)
    else:
      raise RException("Invalid engine type %s" % directives.engine_type)
  def remove(self, val, args = None):
    return self.remove_mem(val, args)
  def remove_mem(self, val, args = None, help = None):
    addition = ','.join([x.str_hash for x in args])
    if addition not in self.argsdict:
      raise RException("Should only remove additions that have been applied/incorporated")
    if directives.engine_type == 'reduced traces':
      if help is None:
        raise RException("remove_mem needs to be passed an evalnode")
      evalnode = self.argsdict[addition]
      if help not in evalnode.mem_calls:
        raise RException("Should only remove evalnodes which called mem with the right arguments")
      if evalnode.mem_calls[help] == 1:
        del evalnode.mem_calls[help]
      else:
        evalnode.mem_calls[help] -= 1
      if len(evalnode.mem_calls) == 0:
        evalnode.unevaluate()
    elif directives.engine_type == 'traces':
      if help is None:
        raise RException("remove_mem needs to be passed an evalnode")
      evalnode = self.argsdict[addition]
      if help not in evalnode.mem_calls:
        raise RException("Should only remove evalnodes which called mem with the right arguments")
      del evalnode.mem_calls[help]
      if len(evalnode.mem_calls) == 0:
        evalnode.unevaluate()
    elif directives.engine_type == 'randomdb':
      (oldval, oldcount) = self.argsdict[addition]
      if oldval != val:
        raise RException("%s is not the mem'd value of %s!" % (val.__str__(), oldval.__str__()))
      if oldcount == 1:
        del self.argsdict[addition]
      else:
        self.argsdict[addition] = (oldval, oldcount - 1)
    else:
      raise RException("Invalid engine type %s" % directives.engine_type)
  def prob(self, val, args = None):
    return 0 
  def is_mem_proc(self):
    return True
  def __str__(self):
    return 'Memoization of %s XRP' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.procmem = {}
  def apply(self, args = None):
    if len(args) != 1:
      raise RException("Mem takes exactly one argument")
    procedure = args[0]
    if procedure.type != 'procedure':
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
    if val.type != 'xrp':
      raise RException("Mem should return XRPs")
    if val.xrp not in self.procmem:
      raise RException("mem XRP proc has not been incorporated, or already been removed")
    self.procmem[val.xrp] = args[0]
  def remove(self, val, args = None):
    if val.type != 'xrp':
      raise RException("Mem should return XRPs")
    if val.xrp not in self.procmem:
      raise RException("mem XRP proc has not been incorporated, or already been removed")
    # unevaluate val's evalnodes
    if directives.engine_type == 'traces':
      for args in val.xrp.argsdict:
        evalnode = val.xrp.argsdict[args]
        evalnode.unevaluate()
    elif directives.engine_type == 'reduced traces':
      for args in val.xrp.argsdict:
        evalnode = val.xrp.argsdict[args]
        evalnode.unevaluate()
    elif directives.engine_type == 'randomdb':
      pass
    else:
      raise RException("Invalid engine type %s" % directives.engine_type)
    del self.procmem[val.xrp]
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
    # unevaluate val's evalnodes
    if directives.engine_type == 'traces':
      for args in val.xrp.argsdict:
        evalnode = val.xrp.argsdict[args]
        evalnode.unevaluate()
    elif directives.engine_type == 'reduced traces':
      for args in val.xrp.argsdict:
        evalnode = val.xrp.argsdict[args]
        evalnode.unevaluate()
    elif directives.engine_type == 'randomdb':
      pass
    else:
      raise RException("Invalid engine type %s" % directives.engine_type)
    del self.procmem[val.xrp]
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def is_mem(self):
    return True
  def __str__(self):
    return 'Memoization XRP'

class CRP_XRP(XRP):
  def __init__(self, alpha):
    self.deterministic = False
    self.tables = {}
    check_pos(alpha)
    self.alpha = alpha
    self.weight = alpha
    return
  def apply(self, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    x = rrandom.random.random() * self.weight
    for id in self.tables:
      x -= self.tables[id]
      if x <= 0:
        return NatValue(id)
    return NatValue(rrandom.random.randbelow())
  def incorporate(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    self.weight += 1
    if val.nat in self.tables:
      self.tables[val.nat] += 1
    else:
      self.tables[val.nat] = 1
  def remove(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    if val.nat in self.tables:
      if self.tables[val.nat] == 1:
        del self.tables[val.nat]
      else:
        if not self.tables[val.nat] > 1:
          raise RException("Removing from an empty table")
        self.tables[val.nat] -= 1
        self.weight -= 1
    else:
      raise RException('CRP_XRP cannot remove the value %d, as it has state %s' % (val.nat, str(self.tables.keys())))
  def prob(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    if val.nat in self.tables:
      return math.log(self.tables[val.nat]) - math.log(self.weight)
    else:
      return math.log(self.alpha) - math.log(self.weight)
  def __str__(self):
    return 'CRP(%f)' % (self.alpha)

class gen_CRP_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    return
  def apply(self, args = None):
    alpha = args[0].num
    check_pos(alpha)
    return XRPValue(CRP_XRP(alpha)) 
  def prob(self, val, args = None):
    return 0
  def __str__(self):
    return 'CRP_XRP'

