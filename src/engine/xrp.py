import random
from values import *
import math

# GENERAL XRP DEFINITION

class XRP:
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    pass
  def incorporate(self, val, args = None):
    pass
  def remove(self, val, args = None):
    pass
  # SHOULD RETURN THE LOG PROBABILITY
  def prob(self, val, args = None):
    pass
  def __str__(self):
    return 'XRP'

# HELPERS

def check_prob(val):
  if not 0 <= val <= 1:
    print "Value %s is not a valid probability" % str(val)
    assert False
  if val == 0:
    return 2**(-32)
  elif val == 1:
    return 1 - 2**(-32)
  return val

def check_pos(val):
  if not 0 < val:
    print "Value %s is not positive" % str(val)
    assert False
  return

def check_nonneg(val):
  if not 0 <= val:
    print "Value %s is negative" % str(val)
    assert False
  return

# SPECIFIC XRPs

def dirichlet(params):
  sample = [random.gammavariate(a,1) for a in params]
  z = sum(sample) + 0.0
  return [v/z for v in sample]

class gaussian_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (mu, sigma) = (args[0].num, args[1].num)
    check_pos(sigma)
    return NumValue(random.normalvariate(mu, sigma))
  def prob(self, val, args = None):
    (mu , sigma) = (args[0].num, args[1].num + 0.0)
    check_pos(sigma)
    log_prob = - ((val.num - mu) / (sigma) )**2/ 2.0 - math.log(sigma) - math.log(2 * math.pi) / 2.0
    return log_prob
  def __str__(self):
    return 'normal'

class gaussian_no_args_XRP(XRP):
  def __init__(self, mu, sigma):
    self.deterministic = False
    self.state = None
    check_pos(sigma)
    (self.mu , self.sigma) = (mu, sigma + 0.0)
    self.prob_help = - math.log(sigma) - math.log(2 * math.pi) / 2.0
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gaussian_no_args_XRP has no need to take in arguments %s' % str(args))
    return NumValue(random.normalvariate(self.mu, self.sigma))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gaussian_no_args_XRP has no need to take in arguments %s' % str(args))
    log_prob = self.prob_help - ((val.num - self.mu) / self.sigma)**2 / 2.0 
    return log_prob
  def __str__(self):
    return 'gaussian(%f, %f)' % (self.mu, self.sigma)

class gen_gaussian_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (mu,sigma) = (args[0].num, args[1].num)
    check_pos(sigma)
    return NumValue(gaussian_no_args_XRP(mu, sigma)) 
  def __str__(self):
    return 'gaussian_XRP'

class array_XRP(XRP):
  def __init__(self, array):
    self.deterministic = True
    self.state = array
    self.n = len(self.state)
    return
  def apply(self, args = None):
    assert len(args) == 1
    i = args[0].num
    assert 0 <= i < self.n
    return self.state[i]
  def prob(self, val, args = None):
    assert len(args) == 1
    i = args[0].num
    assert 0 <= i < self.n
    assert val == self.state[i]
    return 0
  def __str__(self):
    return ('array(%s)' % str(self.state))

class dirichlet_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    for arg in args:
      check_pos(arg.num)
    probs = [float(p) for p in dirichlet([arg.num for arg in args])]
    return XRPValue(array_XRP(probs))
  def prob(self, val, args = None):
    assert val.type == 'xrp'
    probs = [x.num for x in val.xrp.state]
    for prob in probs:
      check_prob(prob)
    n = len(args)
    assert len(probs) == n

    alpha = 0
    for alpha_i in args:
      check_pos(alpha_i.num)
      alpha += alpha_i.num

    return math.log(math.gamma(alpha)) + sum((args[i].num - 1) * math.log(probs[i]) for i in xrange(n)) \
           - sum(math.log(math.gamma(args[i].num)) for i in xrange(n))

  def __str__(self):
    return 'dirichlet'

class dirichlet_no_args_XRP(XRP):
  def __init__(self, args):
    self.deterministic = False
    self.alphas = args
    self.alpha = 0
    for alpha_i in self.alphas:
      check_pos(alpha_i)
      self.alpha += alpha_i
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: dirichlet_no_args_XRP has no need to take in arguments %s' % str(args))
    probs = [NumValue(float(p)) for p in dirichlet(self.alphas)]
    return XRPValue(array_XRP(probs))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: dirichlet_no_args_XRP has no need to take in arguments %s' % str(args))
    assert val.type == 'xrp'
    probs = [x.num for x in val.xrp.state]
    for prob in probs:
      check_prob(prob)

    n = len(self.alphas)
    assert len(probs) == n

    return math.log(math.gamma(self.alpha)) + sum((self.alphas[i] - 1) * math.log(probs[i]) for i in xrange(n)) \
           - sum(math.log(math.gamma(self.alphas[i])) for i in xrange(n))
  def __str__(self):
    return 'dirichlet(%s)' % str(self.alphas)

class gen_dirichlet_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    return XRPValue(dirichlet_no_args_XRP(args)) 
  def __str__(self):
    return 'dirichlet_XRP'

class beta_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(random.betavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    v = check_prob(val.num)
    return math.log(math.gamma(a + b)) + (a - 1) * math.log(v)  + (b - 1) * math.log(1 - v) \
           - math.log(math.gamma(a)) - math.log(math.gamma(b))
  def __str__(self):
    return 'beta'

class beta_no_args_XRP(XRP):
  def __init__(self, a, b):
    self.deterministic = False
    self.state = None
    check_pos(a)
    check_pos(b)
    self.a, self.b = a, b 
    self.prob_help = math.log(math.gamma(a + b)) - math.log(math.gamma(a)) - math.log(math.gamma(b))
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: beta_no_args_XRP has no need to take in arguments %s' % str(args))
    return NumValue(random.betavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: beta_no_args_XRP has no need to take in arguments %s' % str(args))
    v = check_prob(val.num)
    return self.prob_help + (self.a - 1) * math.log(v) + (self.b - 1) * math.log(1 - v) 
  def __str__(self):
    return 'beta(%d, %d)' % (self.a, self.b)

class gen_beta_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return XRPValue(beta_no_args_XRP(a, b)) 
  def __str__(self):
    return 'beta_XRP'

class gamma_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(random.gammavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    check_pos(val.num)
    if val.num == 0:
      warnings.warn('gamma(%f, %f) returning %f' % (a, b, val.num))
      val.num = .0000000000000001
    return (a-1) * math.log(val.num) - ((val.num + 0.0) / b) - math.log(math.gamma(a)) - a * math.log(b)
  def __str__(self):
    return 'gamma'

class gamma_no_args_XRP(XRP):
  def __init__(self, a, b):
    self.deterministic = False
    self.state = None
    check_pos(a)
    check_pos(b)
    self.a, self.b = a, b 
    self.prob_help = - math.log(math.gamma(a)) - a * math.log(b)
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gamma_no_args_XRP has no need to take in arguments %s' % str(args))
    return NumValue(random.gammavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gamma_no_args_XRP has no need to take in arguments %s' % str(args))
    check_pos(val.num)
    if val.num == 0:
      warnings.warn('gamma(%f, %f) returning %f' % (a, b, val.num))
      val.num = .0000000000000001
    return self.prob_help + (self.a - 1) * math.log(val.num) - ((val.num + 0.0) / self.b)
  def __str__(self):
    return 'gamma(%d, %d)' % (self.a, self.b)

class gen_gamma_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return XRPValue(gamma_no_args_XRP(a, b)) 
  def __str__(self):
    return 'gamma_XRP'

class bernoulli_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    p = args[0].num
    p = check_prob(p)
    return BoolValue(rrandom.random.random() < p)
  def prob(self, val, args = None):
    p = args[0].num
    p = check_prob(p)
    if val.bool:
      return math.log(p)
    else:
      return math.log(1.0 - p)
  def __str__(self):
    return 'bernoulli'

class bernoulli_no_args_XRP(XRP):
  def __init__(self, p):
    self.deterministic = False
    self.state = None
    self.p = p
    p = check_prob(p)
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: bernoulli_no_args_XRP has no need to take in arguments %s' % str(args))
    return BoolValue(rrandom.random.random() < self.p)
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: bernoulli_no_args_XRP has no need to take in arguments %s' % str(args))
    if val.bool:
      return math.log(self.p)
    else:
      return math.log(1.0 - self.p)
  def __str__(self):
    return 'bernoulli(%f)' % self.p

class gen_bernoulli_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    p = args[0].num
    p = check_prob(p)
    return XRPValue(bernoulli_no_args_XRP(p)) 
  def __str__(self):
    return 'bernoulli_XRP'

class uniform_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    n = args[0].num
    check_nonneg(n)
    return NumValue(rrandom.random.randint(n-1))
  def prob(self, val, args = None):
    n = args[0].num
    check_nonneg(n)
    assert 0 <= val.num < n
    return -math.log(n)
  def __str__(self):
    return 'uniform'

class uniform_no_args_XRP(XRP):
  def __init__(self, n):
    self.deterministic = False
    self.state = None
    check_nonneg(n)
    self.n = n
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: uniform_no_args_XRP has no need to take in arguments %s' % str(args))
    return NumValue(rrandom.random.randint(self.n-1))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: uniform_no_args_XRP has no need to take in arguments %s' % str(args))
    assert 0 <= val.num < self.n
    return -math.log(self.n)
  def __str__(self):
    return 'uniform(%d)' % self.n

class gen_uniform_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    n = args[0].num
    check_nonneg(n)
    return XRPValue(uniform_no_args_XRP(n)) 
  def __str__(self):
    return 'uniform_XRP'

class beta_bernoulli_1(XRP):
  def __init__(self, start_state = (1, 1)):
    self.deterministic = False
    (a, b) = start_state
    self.state = random.betavariate(a, b)
    p = check_prob(self.state)
  def apply(self, args = None):
    return BoolValue((rrandom.random.random() < self.state))
  def prob(self, val, args = None):
    # PREPROCESS?
    if val.bool:
      return math.log(self.state)
    else:
      return math.log(1.0 - self.state)
  def __str__(self):
    return 'beta_bernoulli'

class beta_bernoulli_2(XRP):
  def __init__(self, start_state = (1, 1)):
    self.deterministic = False
    self.state = start_state
  def apply(self, args = None):
    (h, t) = self.state
    if (h | t == 0):
      val = (rrandom.random.random() < 0.5)
    else:
      val = (rrandom.random.random() * (h + t) < h)
    return BoolValue(val)
  def incorporate(self, val, args = None):
    (h, t) = self.state
    if val.bool:
      h += 1
    else:
      t += 1
    self.state = (h, t)
    return self.state
  def remove(self, val, args = None):
    (h, t) = self.state
    if val.num:
      check_nonneg(h)
      h -= 1
    else:
      check_nonneg(t)
      t -= 1
    self.state = (h, t)
    return self.state
  def prob(self, val, args = None):
    (h, t) = self.state
    if (h | t) == 0:
      return - math.log(2)
    else:
      if val.num:
        return math.log(h) - math.log(h + t)
      else:
        return math.log(t) - math.log(h + t)
  def __str__(self):
    return 'beta_bernoulli'
