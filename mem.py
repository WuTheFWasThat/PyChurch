from directives import *

# THIS XRP IMPLEMENTATION IS NOT INDEPENDENT OF DIRECTIVES IMPLEMENTATION 
class mem_proc_XRP(XRP):
  def __init__(self, procedure):
    self.deterministic = False
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.state = {}
  def apply(self, args = None, call_stack = None):
    assert len(args) == self.n and all([args[i].__class__.__name__ == 'Value' for i in xrange(self.n)])
    assert type(call_stack) == list 
    if tuple(args) in self.state:
      (val, count) = self.state[tuple(args)]
    else:
      val = evaluate(apply(self.procedure, args), stack = call_stack + [-1, 'mem', hash(self.procedure), tuple(args)]) 
    return val
  def incorporate(self, val, args = None):
    if tuple(args) not in self.state:
      self.state[tuple(args)] = (val, 1)
    else:
      (oldval, oldcount) = self.state[tuple(args)]
      assert oldval == val
      self.state[tuple(args)] = (oldval, oldcount + 1)
    return self.state
  def remove(self, val, args = None):
    assert tuple(args) in self.state
    (oldval, oldcount) = self.state[tuple(args)]
    assert oldval == val
    if oldcount == 1:
      del self.state[tuple(args)]
    else:
      self.state[tuple(args)] = (oldval, oldcount - 1)
    return self.state
  def prob(self, val, args = None):
    return 0 
  def __str__(self):
    return 'Memoization of %s XRP' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = {}
  def apply(self, args = None):
    assert len(args) == 1
    procedure = args[0]
    assert procedure.__class__.__name__ == 'Value' and procedure.type == 'procedure'
    if procedure not in self.state:
      mem_proc = mem_proc_XRP(procedure)
      assert mem_proc.__class__.__name__ == 'mem_proc_XRP'
      return value(mem_proc)
    # TODO: do i really want to remember?
    else:
      return self.state[procedure]
  def incorporate(self, val, args = None):
    self.state[args[0]] = val
    return self.state
  def remove(self, val, args = None):
    if args[0] in self.state:
      del self.state[args[0]]
    else:
      warnings.warn('Couldn\'t remove procedure %s from mem_XRP' % (str(args[0])))
    return self.state
  def prob(self, val, args = None):
    return 0 # correct since other flips will be added to db? 
  def __str__(self):
    return 'Memoization XRP'

mem_xrp = mem_XRP()
def mem(function):
  return expression(('apply', mem_xrp, function))

class CRP_XRP(XRP):
  def __init__(self, alpha):
    self.deterministic = False
    self.state = {}
    check_pos(alpha)
    self.alpha = alpha
    self.weight = alpha
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    x = random.random() * self.weight
    for id in self.state:
      x -= self.state[id]
      if x <= 0:
        return id
    return value(random.randint(0, 2**32-1))
  def incorporate(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    self.weight += 1
    if val in self.state:
      self.state[val] += 1
    else:
      self.state[val] = 1
    return self.state
  def remove(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    if val in self.state:
      if self.state[val] == 1:
        del self.state[val]
      else:
        assert self.state[val] > 1
        self.state[val] -= 1
        self.weight -= 1
    else:
      warnings.warn('Warning: CRP_XRP cannot remove the value %d, as it has state %s' % (str(val), str(self.state)))
    return self.state
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    if val in self.state:
      return math.log(self.state[val]) - math.log(self.weight)
    else:
      return math.log(self.alpha) - math.log(self.weight)
  def __str__(self):
    return 'CRP(%f)' % (self.alpha)

class gen_CRP_XRP(XRP):
  def __init__(self):
    self.state = None
    return
  def apply(self, args = None):
    alpha = args[0].val
    check_pos(alpha)
    return Value(CRP_XRP(alpha)) 
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    return 0
  def __str__(self):
    return 'CRP_XRP'

crp_xrp = gen_CRP_XRP()
def CRP(alpha):
  return expression(('apply', crp_xrp, alpha))

