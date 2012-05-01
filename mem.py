from directives import *

class mem_proc_XRP(XRP):
  def __init__(self, procedure):
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.state = {}
    self.hash = random.randint(0, 2**32 - 1)
  def apply(self, args = None):
    assert len(args) == self.n and all([args[i].__class__.__name__ == 'Value' for i in xrange(self.n)])
    if tuple(args) in self.state:
      val = self.state[tuple(args)]
    else:
      newenv = self.procedure.env.spawn_child()
      for i in range(self.n):
        newenv.set(self.procedure.vars[i], args[i])
      val = evaluate(self.procedure.body, newenv, reflip = True)
    return val
  def incorporate(self, val, args = None):
    self.state[tuple(args)] = val
    return self.state
  def remove(self, val, args = None):
    if tuple(args) in self.state:
      assert self.state[tuple(args)] == val
      del self.state[tuple(args)]
    else:
      # REMOVE DOESN'T STRICTLY UNDO ONE APPLY...
      #warnings.warn('Couldn\'t remove %s' % (str(args)))
      pass
    return self.state
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def __str__(self):
    return 'Memoization of procedure %s XRP' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self):
    self.state = {}
    self.hash = random.randint(0, 2**32 - 1)
  def apply(self, args = None):
    procedure = args[0]
    assert procedure.__class__.__name__ == 'Value' and procedure.type == 'procedure'
    if procedure not in self.state:
      return value(mem_proc_XRP(procedure))
    else:
      return self.state[procedure]
  def incorporate(self, val, args = None):
    self.state[args[0]] = val
    return self.state
  def remove(self, val, args = None):
    if args in self.state:
      del self.state[args[0]]
    else:
      warnings.warn('Couldn\'t remove procedure %s from mem_XRP' % (str(args[0])))
    return self.state
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def __str__(self):
    return 'Memoization XRP'

