import random
from values import *
import math

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
    (mu, sigma) = (args[0].val, args[1].val)
    check_pos(sigma)
    return Value(random.normalvariate(mu, sigma))
  def prob(self, val, args = None):
    (mu , sigma) = (args[0].val, args[1].val + 0.0)
    check_pos(sigma)
    log_prob = - ((val.val - mu) / (sigma) )**2/ 2.0 - math.log(sigma) - math.log(2 * math.pi) / 2.0
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
    return Value(random.normalvariate(self.mu, self.sigma))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gaussian_no_args_XRP has no need to take in arguments %s' % str(args))
    log_prob = self.prob_help - ((val.val - self.mu) / self.sigma)**2 / 2.0 
    return log_prob
  def __str__(self):
    return 'gaussian(%f, %f)' % (self.mu, self.sigma)

class gen_gaussian_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (mu,sigma) = (args[0].val, args[1].val)
    check_pos(sigma)
    return Value(gaussian_no_args_XRP(mu, sigma)) 
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
    i = args[0].val
    assert 0 <= i < self.n
    return self.state[i]
  def prob(self, val, args = None):
    assert len(args) == 1
    i = args[0].val
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
      check_pos(arg.val)
    probs = [float(p) for p in dirichlet([arg.val for arg in args])]
    return Value(array_XRP(probs))
  def prob(self, val, args = None):
    assert val.type == 'xrp'
    assert isinstance(val.val, array_XRP)
    probs = [x.val for x in val.val.state]
    for prob in probs:
      check_prob(prob)
    n = len(args)
    assert len(probs) == n

    alpha = 0
    for alpha_i in args:
      check_pos(alpha_i.val)
      alpha += alpha_i.val

    return math.log(math.gamma(alpha)) + sum((args[i].val - 1) * math.log(probs[i]) for i in xrange(n)) \
           - sum(math.log(math.gamma(args[i].val)) for i in xrange(n))

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
    probs = [Value(float(p)) for p in dirichlet(self.alphas)]
    return Value(array_XRP(probs))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: dirichlet_no_args_XRP has no need to take in arguments %s' % str(args))
    assert val.type == 'xrp'
    assert isinstance(val.val, array_XRP)
    probs = [x.val for x in val.val.state]
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
    return Value(dirichlet_no_args_XRP(args)) 
  def __str__(self):
    return 'dirichlet_XRP'

class beta_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    return Value(random.betavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    v = check_prob(val.val)
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
    return Value(random.betavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: beta_no_args_XRP has no need to take in arguments %s' % str(args))
    v = check_prob(val.val)
    return self.prob_help + (self.a - 1) * math.log(v) + (self.b - 1) * math.log(1 - v) 
  def __str__(self):
    return 'beta(%d, %d)' % (self.a, self.b)

class gen_beta_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    return Value(beta_no_args_XRP(a, b)) 
  def __str__(self):
    return 'beta_XRP'

class gamma_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    return Value(random.gammavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    check_pos(val.val)
    if val.val == 0:
      warnings.warn('gamma(%f, %f) returning %f' % (a, b, val.val))
      val.val = .0000000000000001
    return (a-1) * math.log(val.val) - ((val.val + 0.0) / b) - math.log(math.gamma(a)) - a * math.log(b)
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
    return Value(random.gammavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: gamma_no_args_XRP has no need to take in arguments %s' % str(args))
    check_pos(val.val)
    if val.val == 0:
      warnings.warn('gamma(%f, %f) returning %f' % (a, b, val.val))
      val.val = .0000000000000001
    return self.prob_help + (self.a - 1) * math.log(val.val) - ((val.val + 0.0) / self.b)
  def __str__(self):
    return 'gamma(%d, %d)' % (self.a, self.b)

class gen_gamma_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    return Value(gamma_no_args_XRP(a, b)) 
  def __str__(self):
    return 'gamma_XRP'

class bernoulli_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    p = args[0].val
    p = check_prob(p)
    return Value(rrandom.random.random() < p)
  def prob(self, val, args = None):
    p = args[0].val
    p = check_prob(p)
    if val.val:
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
    return Value(rrandom.random.random() < self.p)
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: bernoulli_no_args_XRP has no need to take in arguments %s' % str(args))
    if val.val:
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
    p = args[0].val
    p = check_prob(p)
    return Value(bernoulli_no_args_XRP(p)) 
  def __str__(self):
    return 'bernoulli_XRP'

class uniform_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    n = args[0].val
    check_nonneg(n)
    return Value(rrandom.random.randint(n-1))
  def prob(self, val, args = None):
    n = args[0].val
    check_nonneg(n)
    assert 0 <= val.val < n
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
    return Value(rrandom.random.randint(self.n-1))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise Exception('Warning: uniform_no_args_XRP has no need to take in arguments %s' % str(args))
    assert 0 <= val.val < self.n
    return -math.log(self.n)
  def __str__(self):
    return 'uniform(%d)' % self.n

class gen_uniform_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    self.state = None
    return
  def apply(self, args = None):
    n = args[0].val
    check_nonneg(n)
    return Value(uniform_no_args_XRP(n)) 
  def __str__(self):
    return 'uniform_XRP'

class beta_bernoulli_1(XRP):
  def __init__(self, start_state = (1, 1)):
    self.deterministic = False
    (a, b) = start_state
    self.state = random.betavariate(a, b)
    p = check_prob(self.state)
  def apply(self, args = None):
    return Value((rrandom.random.random() < self.state))
  def prob(self, val, args = None):
    # PREPROCESS?
    if val.val:
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
    return Value(val)
  def incorporate(self, val, args = None):
    (h, t) = self.state
    if val.val:
      h += 1
    else:
      t += 1
    self.state = (h, t)
    return self.state
  def remove(self, val, args = None):
    (h, t) = self.state
    if val.val:
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
      if val.val:
        return math.log(h) - math.log(h + t)
      else:
        return math.log(t) - math.log(h + t)
  def __str__(self):
    return 'beta_bernoulli'
