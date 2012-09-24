import random
from values import *

class gaussian_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (mu, sigma) = (args[0].val, args[1].val)
    check_num(mu)
    check_pos(sigma)
    return value(random.normalvariate(mu, sigma))
  def prob(self, val, args = None):
    (mu , sigma) = (args[0].val, args[1].val + 0.0)
    check_num(mu)
    check_pos(sigma)
    check_num(val.val)
    log_prob = - ((val.val - mu) / (sigma) )**2/ 2.0 - math.log(sigma) - math.log(2 * math.pi) / 2.0
    return log_prob
  def __str__(self):
    return 'normal'

class gaussian_no_args_XRP(XRP):
  def __init__(self, mu, sigma):
    self.deterministic = False
    self.state = None
    check_num(mu)
    check_pos(sigma)
    (self.mu , self.sigma) = (mu, sigma + 0.0)
    self.prob_help = - math.log(sigma) - math.log(2 * math.pi) / 2.0
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: gaussian_no_args_XRP has no need to take in arguments %s' % str(args))
    return value(random.normalvariate(self.mu, self.sigma))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: gaussian_no_args_XRP has no need to take in arguments %s' % str(args))
    check_num(val.val)
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
    check_num(mu)
    check_pos(sigma)
    return Value(gaussian_no_args_XRP(mu, sigma)) 
  def __str__(self):
    return 'gaussian_XRP'

class beta_args_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    self.state = None
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    return value(random.betavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].val, args[1].val)
    check_pos(a)
    check_pos(b)
    check_prob(val.val)
    if val.val == 0:
      warnings.warn('beta(%f, %f) returning %f' % (a, b, val.val))
      val.val = .0000000000000001
    elif val.val == 1:
      warnings.warn('beta(%f, %f) returning %f' % (a, b, val.val))
      val.val = .9999999999999999
    return math.log(math.gamma(a + b)) + (a - 1) * math.log(val.val)  + (b - 1) * math.log(1 - val.val) \
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
      warnings.warn('Warning: beta_no_args_XRP has no need to take in arguments %s' % str(args))
    return value(random.betavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: beta_no_args_XRP has no need to take in arguments %s' % str(args))
    check_prob(val.val)
    if val.val == 0:
      warnings.warn('beta(%f, %f) returning %f' % (a, b, val.val))
      val.val = .0000000000000001
    elif val.val == 1:
      warnings.warn('beta(%f, %f) returning %f' % (a, b, val.val))
      val.val = .9999999999999999
    return self.prob_help + (self.a - 1) * math.log(val.val) + (self.b - 1) * math.log(1 - val.val) 
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
    return value(random.gammavariate(a, b))
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
      warnings.warn('Warning: gamma_no_args_XRP has no need to take in arguments %s' % str(args))
    return value(random.gammavariate(self.a, self.b))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: gamma_no_args_XRP has no need to take in arguments %s' % str(args))
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
    check_prob(p)
    return value(random.random() < p)
  def prob(self, val, args = None):
    p = args[0].val
    check_prob(p)
    check_bool(val.val)
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
    check_prob(p)
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: bernoulli_no_args_XRP has no need to take in arguments %s' % str(args))
    return value(random.random() < self.p)
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: bernoulli_no_args_XRP has no need to take in arguments %s' % str(args))
    check_bool(val.val)
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
    check_prob(p)
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
    check_nat(n)
    return value(random.randint(0, n-1))
  def prob(self, val, args = None):
    n = args[0].val
    check_nat(n)
    assert type(val.val) == int and 0 <= val.val < n
    return -math.log(n)
  def __str__(self):
    return 'uniform'

class uniform_no_args_XRP(XRP):
  def __init__(self, n):
    self.deterministic = False
    self.state = None
    check_nat(n)
    self.n = n
    return
  def apply(self, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: uniform_no_args_XRP has no need to take in arguments %s' % str(args))
    return value(random.randint(0, self.n-1))
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      warnings.warn('Warning: uniform_no_args_XRP has no need to take in arguments %s' % str(args))
    assert type(val.val) == int and 0 <= val.val < self.n
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
    check_nat(n)
    return Value(uniform_no_args_XRP(n)) 
  def __str__(self):
    return 'uniform_XRP'

class beta_bernoulli_1(XRP):
  def __init__(self, start_state = (1, 1)):
    self.deterministic = False
    (a, b) = start_state
    self.state = random.betavariate(a, b)
    check_prob(self.state)
  def apply(self, args = None):
    return value((random.random() < self.state))
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
      val = (random.random() < 0.5)
    else:
      val = (random.random() * (h + t) < h)
    return value(val)
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
      check_nat(h)
      h -= 1
    else:
      check_nat(t)
      t -= 1
    self.state = (h, t)
    return self.state
  def prob(self, val, args = None):
    check_bool(val.val) 
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

