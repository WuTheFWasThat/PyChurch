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
      val = evaluate(apply(self.procedure, args), stack = ['xrp', hash(self), tuple(args)])
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

class CRP_XRP(XRP):
  def __init__(self, alpha):
    self.state = {}
    check_num(alpha)
    self.state[0] = alpha
    self.weight = alpha
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    x = random.random(0, 1) * self.weight
    for id in self.state:
      x -= self.state[id]
      if x <= 0:
        if x == 0:
          return random.randint(0, 2**32-1)
        else:
          return id
    warnings.warn('Warning: CRP_XRP had total_weight %s and has state %s' % (str(self.weight), str(self.state))) 
    assert False
  def incorporate(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    assert val != 0
    self.weight += 1
    if val in self.state:
      self.state[val] += 1
    else:
      self.state[val] = 1
    return self.state
  def remove(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    assert val != 0
    if val in self.state:
      if self.state[val] == 1
        del self.state[val]
      else:
        assert self.state[val] > 1
        self.state[val] -= 1
        self.weight -= 1
    else:
      warnings.warn('Warning: CRP_XRP cannot remove the value %d, as it has state %s' % (str(val), str(self.state)))
    return None
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: CRP_XRP has no need to take in arguments %s' % str(args))
    check_num(val.val)
    log_prob = self.prob_help - ((val.val - self.mu) / self.sigma)**2 / 2.0 
    return log_prob
  def __str__(self):
    return 'gaussian(%f, %f)' % (self.mu, self.sigma)

class gen_gaussian_XRP(XRP):
  def __init__(self):
    self.state = None
    return
  def apply(self, args = None):
    (mu,sigma) = (args[0].val, args[1].val)
    check_num(mu)
    check_pos(sigma)
    return Value(CRP_XRP(mu, sigma)) 
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    return 0
  def __str__(self):
    return 'gaussian_XRP'

class gen_CRP_XRP(XRP):

  assume('DP', \
         function(['concentration', 'basemeasure'], \
                  let([('sticks', mem(function('j', beta(1, 'concentration')))),
                       ('atoms',  mem(function('j', apply('basemeasure')))),
                       ('loop', \
                        function('j', \
                                 ifelse(bernoulli(apply('sticks', 'j')), \
                                        apply('atoms', 'j'), \
                                        apply('loop', var('j')+1)))) \
                      ], \
                      function([], apply('loop', 1))))) 

  assume('DPmem', \
         function(['concentration', 'proc'], \
                  let([('restaurants', \
                        mem( function('args', apply('DP', ['concentration', function([], apply('proc', 'args'))]))))], \
                      function('args', apply('restaurants', 'args')))))
