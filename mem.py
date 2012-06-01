from directives import *

class mem_proc_XRP(XRP):
  def __init__(self, procedure):
    self.procedure = procedure
    self.n = len(procedure.vars)
    self.state = {}
  def apply(self, args = None):
    assert len(args) == self.n and all([args[i].__class__.__name__ == 'Value' for i in xrange(self.n)])
    if tuple(args) in self.state:
      (val, count) = self.state[tuple(args)]
    else:
      newenv = self.procedure.env.spawn_child()
      for i in range(self.n):
        newenv.set(self.procedure.vars[i], args[i])
      val = evaluate(self.procedure.body, newenv, reflip = True)
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
    return 'Memoization of procedure %s XRP' % str(self.procedure)

class mem_XRP(XRP):
  def __init__(self):
    self.state = {}
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

sticks_expr = mem(function('j', beta(1.0, 'concentration')))
atoms_expr = mem(function('j', apply('basemeasure')))

loop_body_expr = function('j', ifelse( bernoulli(apply('sticks', 'j')), apply('atoms', 'j'), apply('loophelper', var('j') + 1))) 
loop_expr = apply(  function(['sticks', 'atoms'], loop_body_expr), [sticks_expr , atoms_expr])
assume('loophelper', function(['concentration', 'basemeasure'], loop_expr))
assume( 'DP', function(['concentration', 'basemeasure'], apply(apply('loophelper', ['concentration', 'basemeasure']), 1)))



