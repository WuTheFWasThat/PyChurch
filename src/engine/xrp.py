from basic_xrps import *

# HELPERS

def check_prob(val):
  if not 0 <= val <= 1:
    raise RException("Value %s is not a valid probability" % str(val))
  return val

def ensure_prob(val):
  check_prob(val)
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

def sample_categorical(probs, z = 1):
  # z should be sum of probs
  (i, v) = (0, rrandom.random.random() * z)
  while probs[i] < v:
    v -= probs[i]
    i += 1
  return i

# GENERALLY USEFUL XRPs

class noisy_negate_XRP(XRP):
  def sample(self, args = None):
    if len(args) != 2:
      raise RException("noisy_negate must take 2 arguments")
    (b, p) = (args[0].bool, args[1].num)
    p = ensure_prob(p)
    if rrandom.random.random() < p:
      return BoolValue(not args[0].bool)
    else:
      return BoolValue(args[0].bool)
  def prob(self, val, args = None):
    if len(args) != 2:
      raise RException("noisy_negate must take 2 arguments")
    (b, p) = (args[0].bool, args[1].num)
    p = ensure_prob(p)
    if val.bool ^ b:
      return math.log(p)
    else:
      return math.log(1-p)
  def __str__(self):
    return 'noisy_negate_XRP'

class noisy_XRP(XRP):
  def sample(self, args = None):
    if len(args) != 2:
      raise RException("noisy must take 2 arguments")
    (b, p) = (args[0].bool, args[1].num)
    p = ensure_prob(p)
    if b:
      return BoolValue(True)
    else:
      return BoolValue(rrandom.random.random() < p)
  def prob(self, val, args = None):
    if len(args) != 2:
      raise RException("noisy must take 2 arguments")
    (b, p) = (args[0].bool, args[1].num)
    p = ensure_prob(p)
    if b:
      if not val.bool:
        raise RException("Should have returned true")
      return 0
    else:
      if val.bool:
        return math.log(p)
      else:
        return math.log(1-p)
  def __str__(self):
    return 'noisy_XRP'

class array_XRP(XRP):
  def __init__(self, array, i_start = 0):
    self.initialize()
    self.resample = True
    self.array = array
    self.n = len(self.array)
    self.i_start = i_start;
    return
  def sample(self, args = None):
    if len(args) != 1:
      raise RException("Should have 1 argument, not %d" % len(args))
    i = args[0].nat + self.i_start
    if not 0 <= i < self.n:
      raise RException("Index %d out of bounds in array %s" % (args[0].nat, self.__str__()))
    return self.array[i]
  def prob(self, val, args = None):
    if len(args) != 1:
      raise RException("Should have 1 argument, not %d" % len(args))
    i = args[0].nat + self.i_start
    if not 0 <= i < self.n:
      raise RException("Index %d out of bounds in array %s" % (args[0].nat, self.__str__()))
    if val != self.array[i]:
      raise RException("Array at index %d should've been %s" % (args[0].nat, val.__str__()))
    return 0
  def __str__(self):
    return str(self.array[self.i_start:])

class rest_array_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def sample(self, args):
    check_num_args(args, 1)
    return XRPValue(array_XRP(args[0].xrp.array, args[0].xrp.i_start + 1))
  def __str__(self):
    return 'rest'

class make_array_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  def sample(self, args = None):
    return XRPValue(array_XRP(args)) 
  def __str__(self):
    return 'array_make_XRP'

class make_symmetric_array_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  def sample(self, args = None):
    (el, n)  = (args[0], args[1].nat)
    return XRPValue(array_XRP([el] * n)) 
  def __str__(self):
    return 'array_make_XRP'

class categorical_XRP(XRP):
  def sample(self, args = None):
    probs = [check_prob(x.num) for x in args]
    if not .999 <= sum(probs) <= 1.001:
      raise RException("Categorical probabilities must sum to 1")
    i = sample_categorical(probs)
    return IntValue(i)
  def prob(self, val, args = None):
    probs = [check_prob(x.num) for x in args]
    if not .999 <= sum(probs) <= 1.001:
      raise RException("Categorical probabilities must sum to 1")
    if not 0 <= val.int < len(probs):
      raise RException("Categorical should only return values between 0 and %d" % len(probs))
    log_prob = math.log(probs[val.int])
    return log_prob
  def __str__(self):
    return 'categorical_XRP'

# DISTRIBUTIONS

class gaussian_XRP(XRP):
  def sample(self, args = None):
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

class beta_XRP(XRP):
  def sample(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(rrandom.random.betavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    v = ensure_prob(val.num)
    return math.log(math_gamma(a + b)) + (a - 1) * math.log(v)  + (b - 1) * math.log(1 - v) \
           - math.log(math_gamma(a)) - math.log(math_gamma(b))
  def __str__(self):
    return 'beta'

class gamma_XRP(XRP):
  def sample(self, args = None):
    (a,b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    return NumValue(rrandom.random.gammavariate(a, b))
  def prob(self, val, args = None):
    (a , b) = (args[0].num, args[1].num)
    check_pos(a)
    check_pos(b)
    check_pos(val.num)
    return (a-1) * math.log(val.num) - ((val.num + 0.0) / b) - math.log(math_gamma(a)) - a * math.log(b)
  def __str__(self):
    return 'gamma'

class bernoulli_XRP(XRP):
  def sample(self, args = None):
    if len(args) == 0:
      p = 0.5
    elif len(args) == 1:
      p = args[0].num
      p = check_prob(p)
    else:
      raise RException("bernoulli_XRP has no need to take in more than 1 argument")
    return BoolValue(rrandom.random.random() < p)
  def prob(self, val, args = None):
    if len(args) == 0:
      p = 0.5
    elif len(args) == 1:
      p = args[0].num
      p = check_prob(p)
    else:
      raise RException("bernoulli_XRP has no need to take in more than 1 argument")
    if val.bool:
      return math.log(p)
    else:
      return math.log(1.0 - p)
  def __str__(self):
    return 'bernoulli'

class uniform_discrete_XRP(XRP):
  def sample(self, args = None):
    n = args[0].nat
    return NatValue(rrandom.random.randbelow(n))
  def prob(self, val, args = None):
    n = args[0].nat
    if not 0 <= val.nat < n:
      raise RException("uniform_discrete_XRP should return something between 0 and %d, not %d" % (n, val.nat))
    return -math.log(n)
  def __str__(self):
    return 'uniform'

### MORE SPECIFIC XRPs

class beta_bernoulli_XRP(XRP):
  def __init__(self, array):
    self.initialize()
    self.resample = False
    self.array = array
    self.n = len(array)
    self.z = sum(array)
  def sample(self, args = None):
    check_num_args(args, 0)
    if (self.z == 0):
      val = rrandom.random.randbelow(self.n)
    else:
      val = sample_categorical(self.array, self.z)
    return NatValue(val)
  def incorporate(self, val, args = None):
    check_num_args(args, 0)
    self.array[val.nat] += 1
    self.z += 1
  def remove(self, val, args = None):
    check_num_args(args, 0)
    self.array[val.nat] -= 1
    if self.array[val.nat] < 0:
      raise RException("Something went wrong in beta_bernoulli")
    self.z -= 1
  def prob(self, val, args = None):
    check_num_args(args, 0)
    return math.log(self.array[val.nat]) - math.log(self.z)
  def __str__(self):
    return 'beta_bernoulli(%s)' % str(self.array)

class make_beta_bernoulli_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  # TODO: decide convention on heads/tails
  def sample(self, args = None):
    if len(args) == 1:
      array = [arg.nat for arg in args[0].xrp.array]
    else:
      array = [arg.nat for arg in args]
    return XRPValue(beta_bernoulli_XRP(array)) 
  def __str__(self):
    return 'beta_bernoulli_make_XRP'

class dirichlet_XRP(XRP):
  def sample(self, args = None):
    array_xrp = args[0]
    probs = [NumValue(p) for p in dirichlet([alpha_i.num for alpha_i in array_xrp.xrp.array])]
    return XRPValue(array_XRP(probs))
  def prob(self, val, args = None):
    array_xrp = args[0]
    array = array_xrp.xrp.array
    n = len(array)

    if val.type != 'xrp':
      raise RException("Returned value should have been an array XRP")
    probs = [x.num for x in val.xrp.array]
    for prob in probs:
      check_prob(prob)
    if n != len(probs):
      raise RException("Number of arguments, %d, should've been the dimension %d" % (n, len(probs)))

    alpha = 0
    for alpha_i in array:
      check_pos(alpha_i.num)
      alpha += alpha_i.num

    return math.log(math_gamma(alpha)) + sum([(array[i].num - 1) * math.log(probs[i]) for i in range(n)]) \
           - sum([math.log(math_gamma(array[i].num)) for i in range(n)])
  def __str__(self):
    return 'dirichlet'

class dirichlet_multinomial_XRP(XRP):
  def __init__(self, args):
    self.initialize()
    self.alphas = args
    self.n = len(self.alphas)
    self.alpha = 0
    for alpha_i in self.alphas:
      check_pos(alpha_i)
      self.alpha += alpha_i
    return
  def sample(self, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_no_args_XRP has no need to take in arguments %s' % str(args))
    return NatValue(sample_categorical(self.alphas, self.alpha))
  def incorporate(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_multinomial has no need to take in arguments %s' % str(args))
    if val.int < 0 or val.int >= self.n:
      raise RException('dirichlet_multinomial should return something in [0, ..., %d], not %d' % (self.n - 1, val.int))
    self.alphas[val.int] += 1
    self.alpha += 1
  def remove(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_multinomial has no need to take in arguments %s' % str(args))
    if val.int < 0 or val.int >= self.n:
      raise RException('dirichlet_multinomial should return something in [0, ..., %d], not %d' % (self.n - 1, val.int))
    if self.alphas[val.int] < 1:
      raise RException('Alpha should not drop below 0')
    self.alphas[val.int] -= 1
    self.alpha -= 1
  def prob(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('dirichlet_multinomial has no need to take in arguments %s' % str(args))
    if val.int < 0 or val.int >= self.n:
      raise RException('dirichlet_multinomial should return something in [0, ..., %d], not %d' % (self.n - 1, val.int))

    return math.log(self.alphas[val.int]) - math.log(self.alpha)
  def __str__(self):
    return 'dirichlet_multinomial(%s)' % str(self.alphas)

class make_dirichlet_multinomial_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  def sample(self, args = None):
    if len(args) != 1:
      raise RException("Dirichlet generator takes one argument, an array_XRP")
    array_xrp = args[0]
    return XRPValue(dirichlet_multinomial_XRP([alpha_i.num for alpha_i in array_xrp.xrp.array]))
  def __str__(self):
    return 'dirichlet_multinomial_make_XRP'

class symmetric_dirichlet_XRP(XRP):
  def sample(self, args = None):
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
    if len(probs) != n.nat:
      raise RException("Number of arguments, %d, should've been the dimension %d" % (n.nat, len(probs)))
    return math.log(math_gamma(alpha.num * n.nat)) + (alpha.num - 1) * sum([math.log(probs[i]) for i in range(n.num)]) \
           - n.nat * math.log(math_gamma(alpha.num))
  def __str__(self):
    return 'symmetric_dirichlet_multinomial'

class make_symmetric_dirichlet_multinomial_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  def sample(self, args = None):
    if len(args) != 2:
      raise RException("Symmetric dirichlet generator takes two arguments, alpha and n")
    (alpha, n) = (args[0], args[1])
    return XRPValue(dirichlet_multinomial_XRP([alpha.num] * n.nat)) 
  def __str__(self):
    return 'symmetric_dirichlet_multinomial_make_XRP'

class CRP_XRP(XRP):
  def __init__(self, alpha):
    self.initialize()
    self.tables = {}
    check_pos(alpha)
    self.alpha = alpha
    self.z = alpha
    return
  def sample(self, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    x = rrandom.random.random() * self.z
    for id in self.tables:
      x -= self.tables[id]
      if x <= 0:
        return NatValue(id)
    return NatValue(rrandom.random.randbelow())
  def incorporate(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    self.z += 1
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
        self.z -= 1
    else:
      raise RException('CRP_XRP cannot remove the value %d, as it has state %s' % (val.nat, str(self.tables.keys())))
  def prob(self, val, args = None):
    if args is not None and len(args) != 0:
      raise RException('CRP_XRP has no need to take in arguments %s' % str(args))
    if val.nat in self.tables:
      return math.log(self.tables[val.nat]) - math.log(self.z)
    else:
      return math.log(self.alpha) - math.log(self.z)
  def __str__(self):
    return 'CRP(%f)' % (self.alpha)


class gen_CRP_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
    return
  def sample(self, args = None):
    alpha = args[0].num
    check_pos(alpha)
    return XRPValue(CRP_XRP(alpha))
  def prob(self, val, args = None):
    return 0
  def __str__(self):
    return 'CRP_XRP'
