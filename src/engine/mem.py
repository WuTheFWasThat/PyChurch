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
  def apply_mem(self, args = None, engine = None, help = None):
    raise RException("mem currently not supported")
    if len(args) != self.n:
      raise RException("Gave a mem'd procedure with %d arguments %d arguments instead" % (self.n, len(args)))
    addition = ','.join([x.str_hash for x in args])
    if engine.engine_type == 'reduced traces':
      if addition not in self.argsdict:
        evalnode = ReducedEvalNode(engine, engine.env, ApplyExpression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]))
        evalnode.mem = True
        self.argsdict[addition] = evalnode
        val = evalnode.evaluate()
      else:
        evalnode = self.argsdict[addition]
        val = evalnode.val
      return val
    elif engine.engine_type == 'traces':
      if addition not in self.argsdict:
        evalnode = EvalNode(engine, engine.env, ApplyExpression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]))
        evalnode.mem = True
        self.argsdict[addition] = evalnode
      else:
        evalnode = self.argsdict[addition]
      val = evalnode.evaluate(False)
      return val
    elif engine.engine_type == 'randomdb':
      # help is call_stack for db
      if addition in self.argsdict:
        (val, count) = self.argsdict[addition]
      else:
        val = engine.db.evaluate(ApplyExpression(ConstExpression(self.procedure), [ConstExpression(arg) for arg in args]), stack = help + [-1, 'mem', self.procedure.hash, addition]) 
    else:
      raise RException("Invalid engine type %s" % engine.engine_type)
    return val
  def incorporate(self, val, args = None):
    return self.incorporate_mem(val, args)
  def incorporate_mem(self, val, args = None, engine = None, help = None):
    raise RException("mem currently not supported")
    addition = ','.join([x.str_hash for x in args])
    # TODO:  assert value is correct
    if engine.engine_type == 'reduced traces':
      # help is evalnode
      if addition not in self.argsdict:
        raise RException("Should only incorporate additions that have already been applied")
      evalnode = self.argsdict[addition]
      if help not in evalnode.mem_calls:
        evalnode.mem_calls[help] = 1
      else:
        evalnode.mem_calls[help] += 1
    elif engine.engine_type == 'traces':
      # help is evalnode
      if addition not in self.argsdict:
        raise RException("Should only incorporate additions that have already been applied")
      evalnode = self.argsdict[addition]
      if help in evalnode.mem_calls:
        raise RException("Should only add a given evalnode once, as a mem_call")
      evalnode.mem_calls[help] = True
    elif engine.engine_type == 'randomdb':
      if addition not in self.argsdict:
        self.argsdict[addition] = (val, 1)
      else:
        (oldval, oldcount) = self.argsdict[addition]
        if oldval != val:
          raise RException("Old mem value disagrees with new mem value")
        self.argsdict[addition] = (oldval, oldcount + 1)
    else:
      raise RException("Invalid engine type %s" % engine.engine_type)
  def remove(self, val, args = None):
    return self.remove_mem(val, args)
  def remove_mem(self, val, args = None, engine = None, help = None):
    raise RException("mem currently not supported")
    addition = ','.join([x.str_hash for x in args])
    if addition not in self.argsdict:
      raise RException("Should only remove additions that have been applied/incorporated")
    if engine.engine_type == 'reduced traces':
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
    elif engine.engine_type == 'traces':
      if help is None:
        raise RException("remove_mem needs to be passed an evalnode")
      evalnode = self.argsdict[addition]
      if help not in evalnode.mem_calls:
        raise RException("Should only remove evalnodes which called mem with the right arguments")
      del evalnode.mem_calls[help]
      if len(evalnode.mem_calls) == 0:
        evalnode.unevaluate()
    elif engine.engine_type == 'randomdb':
      (oldval, oldcount) = self.argsdict[addition]
      if oldval != val:
        raise RException("%s is not the mem'd value of %s!" % (val.__str__(), oldval.__str__()))
      if oldcount == 1:
        del self.argsdict[addition]
      else:
        self.argsdict[addition] = (oldval, oldcount - 1)
    else:
      raise RException("Invalid engine type %s" % engine.engine_type)
  def prob(self, val, args = None):
    return 0 
  def is_mem_proc(self):
    return True
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
    pass
    #if val.type != 'xrp':
    #  raise RException("Mem should return XRPs")
    #if val.xrp not in self.procmem:
    #  raise RException("mem XRP proc has not been incorporated, or already been removed")
    #self.procmem[val.xrp] = args[0]

  #def remove(self, val, args = None):
  #  if val.type != 'xrp':
  #    raise RException("Mem should return XRPs")
  #  if val.xrp not in self.procmem:
  #    raise RException("mem XRP proc has not been incorporated, or already been removed")
  #  # unevaluate val's evalnodes
  #  if engine.engine_type == 'traces':
  #    for args in val.xrp.argsdict:
  #      evalnode = val.xrp.argsdict[args]
  #      evalnode.unevaluate()
  #  elif engine.engine_type == 'reduced traces':
  #    for args in val.xrp.argsdict:
  #      evalnode = val.xrp.argsdict[args]
  #      evalnode.unevaluate()
  #  elif engine.engine_type == 'randomdb':
  #    pass
  #  else:
  #    raise RException("Invalid engine type %s" % engine.engine_type)
  #  del self.procmem[val.xrp]
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def is_mem(self):
    return True
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def is_mem(self):
    return True
  def __str__(self):
    return 'mem'

