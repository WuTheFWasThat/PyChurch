from values import *
import math
from utils.rexceptions import RException

# HELPERS

def check_prob(val):
  if not 0 <= val <= 1:
    raise RException("Value %s is not a valid probability" % str(val))
  if val == 0:
    return 2**(-32)
  elif val == 1:
    return 1 - 2**(-32)
  return val

def check_pos(val):
  if not 0 < val:
    raise RException("Value %s is not positive" % str(val))

def sum(array):
  ans = 0
  for x in array:
    ans += x
  return ans

# taken from Wikipedia's page on Lanczos approximation, but only works on real numbers

def math_gamma(z):
  g = 7
  p = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
       771.32342877765313, -176.61502916214059, 12.507343278686905,
       -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
 
  if z < 0.5:
      return math.pi / (math.sin(math.pi * z) * math_gamma(1-z))
  else:
      z -= 1
      x = p[0]
      for i in range(1, g+2):
          x += p[i]/(z+i)
      t = z + g + 0.5
      return math.sqrt(2*math.pi) * math.pow(t, (z+0.5)) * math.exp(-t) * x

def dirichlet(params):
  sample = [rrandom.random.gammavariate(a,1) for a in params]
  z = sum(sample) + 0.0
  return [v/z for v in sample]

def sample_categorical(probs):
  (i, v) = (0, rrandom.random.random())
  while probs[i] < v:
    v -= probs[i]
    i += 1
  return i

# GENERALLY USEFUL XRPs

class categorical_no_args_XRP(XRP):
  def __init__(self, probs):
    self.deterministic = False
    self.state = None
    self.probs = [check_prob(p) for p in probs]
    if not .999 <= sum(self.probs) <= 1.001:
      raise RException("Categorical probabilities must sum to 1")
    self.n = len(self.probs)
    return
  def apply(self, args = None):
    i = sample_categorical(self.probs)
    if args != None and len(args) != 0:
      raise RException("categorical_no_args_XRP has no need to take arguments")
    return IntValue(i)
  def prob(self, val, args = None):
    if args != None and len(args) != 0:
      raise RException("categorical_no_args_XRP has no need to take arguments")
    if not 0 <= val.int < self.n:
      raise RException("Categorical should only return values between 0 and %d" % self.n)
    log_prob = math.log(self.probs[val.int])
    return log_prob
  def __str__(self):
    return 'categorical(%f, %f)' % (self.mu, self.sigma)

class make_symmetric_categorical_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    return
  def apply(self, args = None):
    n = args[0].num
    return XRPValue(categorical_no_args_XRP([1 / (n + 0.0)] * n)) 
  def __str__(self):
    return 'make_symmetric_categorical_XRP'

class gaussian_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    (mu, sigma) = (args[0].num, args[1].num)
    check_pos(sigma)
    return NumValue(rrandom.random.normalvariate(mu, sigma))
  def prob(self, val, args = None):
    (mu , sigma) = (args[0].num, args[1].num + 0.0)
    check_pos(sigma)
    log_prob = - math.pow((val.num - mu) / sigma, 2)/ 2.0 - math.log(sigma) - math.log(2 * math.pi) / 2.0
    return log_prob
  def __str__(self):
    return 'normal'

class array_XRP(XRP):
  def __init__(self, array):
    self.deterministic = True
    self.array = array
    self.n = len(self.array)
    return
  def apply(self, args = None):
    if len(args) != 1:
      raise RException("Should have 1 argument, not %d" % len(args))
    i = args[0].nat
    if not 0 <= i < self.n:
      raise RException("Index must from 0 to %d - 1" % self.n)
    return self.array[i]
  def prob(self, val, args = None):
    if len(args) != 1:
      raise RException("Should have 1 argument, not %d" % len(args))
    i = args[0].nat
    if not 0 <= i < self.n:
      raise RException("Index must from 0 to %d - 1" % self.n)
    if val != self.array[i]:
      raise RException("Array at index %d should've been %s" % (i, val.__str__()))
    return 0
  def __str__(self):
    return ('array(%s)' % str(self.array))

class beta_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(rrandom.random.betavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    v = check_prob(val.num)
    return math.log(math_gamma(a + b)) + (a - 1) * math.log(v)  + (b - 1) * math.log(1 - v) \
           - math.log(math_gamma(a)) - math.log(math_gamma(b))
  def __str__(self):
    return 'beta'

class gamma_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(rrandom.random.gammavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    check_pos(val.num)
    if val.num == 0:
      val.num = .0000000000000001
    return (a-1) * math.log(val.num) - ((val.num + 0.0) / b) - math.log(math_gamma(a)) - a * math.log(b)
  def __str__(self):
    return 'gamma'

class bernoulli_XRP(XRP):
  def __init__(self):
    self.deterministic = False
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

class uniform_discrete_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    n = args[0].nat
    return NatValue(rrandom.random.randbelow(n))
  def prob(self, val, args = None):
    n = args[0].nat
    if not 0 <= val.nat < n:
      raise RException("uniform_args_XRP should return something between 0 and %d, not %d" % (n, val.nat))
    return -math.log(n)
  def __str__(self):
    return 'uniform'

### MORE SPECIFIC XRPs

class beta_bernoulli_XRP(XRP):
  def __init__(self, start_state = (1, 1)):
    self.deterministic = False
    (self.h, self.t) = start_state
  def apply(self, args = None):
    if (self.h | self.t == 0):
      val = (rrandom.random.random() < 0.5)
    else:
      val = (rrandom.random.random() * (self.h + self.t) < self.h)
    return BoolValue(val)
  def incorporate(self, val, args = None):
    if val.bool:
      self.h += 1
    else:
      self.t += 1
  def remove(self, val, args = None):
    if val.num:
      if not self.h > 0:
        raise RException("Removing too many heads from beta_bernoulli")
      self.h -= 1
    else:
      if not self.t > 0:
        raise RException("Removing too many tails from beta_bernoulli")
      self.t -= 1
  def prob(self, val, args = None):
    if (self.h | self.t) == 0:
      return - math.log(2)
    else:
      if val.num:
        return math.log(self.h) - math.log(self.h + self.t)
      else:
        return math.log(self.t) - math.log(self.h + self.t)
  def __str__(self):
    return 'beta_bernoulli'

class make_beta_bernoulli_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    return
  def apply(self, args = None):
    (h, t) = (args[0].nat, args[1].nat)
    return XRPValue(beta_bernoulli_XRP((h, t))) 
  def __str__(self):
    return 'beta_bernoulli_make_XRP'

class dirichlet_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    for arg in args:
      check_pos(arg.num)
    probs = [NumValue(p) for p in dirichlet([arg.num for arg in args])]
    return XRPValue(array_XRP(probs))
  def prob(self, val, args = None):
    if val.type != 'xrp':
      raise RException("Returned value should have been an array XRP")
    probs = [x.num for x in val.xrp.array]
    for prob in probs:
      check_prob(prob)
    n = len(args)
    if len(probs) != n:
      raise RException("Number of arguments, %d, should've been the dimension %d" % (n, len(probs)))

    alpha = 0
    for alpha_i in args:
      check_pos(alpha_i.num)
      alpha += alpha_i.num

    return math.log(math_gamma(alpha)) + sum([(args[i].num - 1) * math.log(probs[i]) for i in range(n)]) \
           - sum([math.log(math_gamma(args[i].num)) for i in range(n)])

  def __str__(self):
    return 'dirichlet'

class dirichlet_multinomial_XRP(XRP):
  def __init__(self, args):
    self.deterministic = False
    self.alphas = args
    self.n = len(self.alphas)
    self.alpha = 0
    for alpha_i in self.alphas:
      check_pos(alpha_i)
      self.alpha += alpha_i
    return
  def apply(self, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_no_args_XRP has no need to take in arguments %s' % str(args))
    probs = [x / (self.alpha + 0.0) for x in self.alphas]
    return NatValue(sample_categorical(probs))
  def incorporate(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_multinomial has no need to take in arguments %s' % str(args))
    if val.int < 0 or val.int >= self.n:
      raise RException('dirichlet_multinomial should return something in [0, ..., %d], not %d' % (self.n - 1, val.int))
    self.alphas[val.int] += 1
    self.alpha += 1
  def prob(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_multinomial has no need to take in arguments %s' % str(args))
    if val.int < 0 or val.int >= self.n:
      raise RException('dirichlet_multinomial should return something in [0, ..., %d], not %d' % (self.n - 1, val.int))

    return math.log(self.alphas[val.int]) - math.log(self.alpha)
  def __str__(self):
    return 'dirichlet_multinomial(%s)' % str(self.alphas)

class symmetric_dirichlet_XRP(XRP):
  def __init__(self):
    self.deterministic = False
    return
  def apply(self, args = None):
    (alpha, n) = (args[0], args[1])
    probs = [NumValue(p) for p in dirichlet([alpha.num] * n.nat)]
    return XRPValue(array_XRP(probs))
  def prob(self, val, args = None):
    (alpha, n) = (args[0], args[1])
    if val.type != 'xrp':
      raise RException("Returned value should have been an array XRP")
    probs = [x.num for x in val.xrp.array]
    for prob in probs:
      check_prob(prob)
    if n.nat != len(args):
      raise RException("Number of arguments, %d, should've been the dimension %d" % (len(args), n.nat))
    if len(probs) != n.nat:
      raise RException("Number of arguments, %d, should've been the dimension %d" % (n.nat, len(probs)))
    return math.log(math_gamma(alpha.num * n.nat)) + (alpha.num - 1) * sum([math.log(probs[i]) for i in range(n.num)]) \
           - n.nat * math.log(math_gamma(alpha.num))

class make_symmetric_dirichlet_multinomial_XRP(XRP):
  def __init__(self):
    self.deterministic = True
    return
  def apply(self, args = None):
    if len(args) != 2:
      raise RException("Symmetric dirichlet generator takes two arguments, alpha and n")
    (alpha, n) = (args[0], args[1])
    return XRPValue(dirichlet_multinomial_XRP([alpha.num] * n.nat)) 
  def __str__(self):
    return 'symmetric_dirichlet_multinomial_make_XRP'

