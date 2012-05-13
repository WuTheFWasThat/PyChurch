import random
from values import *

class beta_args_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    assert type(a) == int and a >= 0
    assert type(b) == int and b >= 0
    return value(random.betavariate(a, b))
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    (a , b) = (args[0].val, args[1].val)
    assert type(a) == int and a >= 0
    assert type(b) == int and b >= 0
    assert type(val.val) == float and 0 <= val.val <= 1
    log_prob = math.log(math.factorial(a + b - 1)) + (a - 1) * math.log(val.val)  + (b - 1) * math.log(1 - val.val) \
           - math.log(math.factorial(a - 1)) - math.log(math.factorial(b - 1))
    return log_prob
  def __str__(self):
    return 'beta'

class beta_no_args_XRP(XRP):
  def __init__(self, a, b):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    assert type(a) == int and a >= 0
    assert type(b) == int and b >= 0
    self.a, self.b = a, b 
    self.prob_help = math.log(math.factorial(a + b - 1)) - math.log(math.factorial(a - 1)) - math.log(math.factorial(b - 1))
    return
  def apply(self, args = None):
    if args != None:
      warnings.warn('Warning: beta_XRP has no need to take in arguments %s' % str(args))
    return value(random.betavariate(self.a, self.b))
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    if args != None:
      warnings.warn('Warning: beta_XRP has no need to take in arguments %s' % str(args))
    assert type(val.val) == float and 0 <= val.val <= 1
    log_prob = self.prob_help + (self.a - 1) * math.log(val.val) + (self.b - 1) * math.log(1 - val.val) 
    return log_prob
  def __str__(self):
    return 'beta(%d, %d)' % (self.a, self.b)

class beta_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    (a,b) = (args[0].val, args[1].val)
    assert type(a) == int and a >= 0
    assert type(b) == int and b >= 0
    return Value(beta_no_args_XRP(a, b)) 
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    return 1
  def __str__(self):
    return 'beta_XRP'

class bernoulli_args_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    p = args[0].val
    assert 0 <= p <= 1
    return value(random.random() < p)
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    p = args[0].val
    assert 0 <= p <= 1
    assert type(val.val) == bool
    if val.val:
      return math.log(p)
    else:
      return math.log(1.0 - p)
  def __str__(self):
    return 'bernoulli'

class bernoulli_no_args_XRP(XRP):
  def __init__(self, p):
    self.state = None
    self.p = p
    assert 0 <= p <= 1
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    return value(random.random() < self.p)
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    assert type(val.val) == bool
    if val.val:
      return math.log(self.p)
    else:
      return math.log(1.0 - self.p)
  def __str__(self):
    return 'bernoulli(%d)' % self.p

class beta_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    p = args[0].val
    assert 0 <= p <= 1
    return Value(bernoulli_no_args_XRP(p)) 
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    return 1
  def __str__(self):
    return 'bernoulli_XRP'

class uniform_args_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    n = args[0].val
    assert type(n) == int and n > 0
    return value(random.randint(0, n-1))
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    n = args[0].val
    assert type(n) == int and n > 0
    assert type(val.val) == int and 0 <= val.val < n
    return -math.log(n)
  def __str__(self):
    return 'uniform'

class uniform_no_args_XRP(XRP):
  def __init__(self, n):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    assert type(n) == int and n > 0
    self.n = n
    return
  def apply(self, args = None):
    return value(random.randint(0, self.n-1))
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    assert type(val.val) == int and 0 <= val.val < n
    return -math.log(self.n)
  def __str__(self):
    return 'uniform(%d)' % self.n

class uniform_XRP(XRP):
  def __init__(self):
    self.state = None
    self.hash = random.randint(0, 2**32 - 1)
    return
  def apply(self, args = None):
    n = args[0].val
    assert type(n) == int and n > 0
    return Value(uniform_no_args_XRP(n)) 
  def incorporate(self, val, args = None):
    return None
  def remove(self, val, args = None):
    return None
  def prob(self, val, args = None):
    return 1
  def __str__(self):
    return 'uniform_XRP'

class beta_bernoulli_1(XRP):
  def __init__(self, start_state = (1, 1)):
    (a, b) = start_state
    self.state = random.betavariate(a, b)
    assert 0 <= self.state <= 1
    self.hash = random.randint(0, 2**32 - 1)
  def apply(self, args = None):
    return value((random.random() < self.state))
  def incorporate(self, val, args = None):
    return self.state
  def remove(self, val, args = None):
    return self.state
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
    self.state = start_state
    self.hash = random.randint(0, 2**32 - 1)
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
      assert h > 0
      h -= 1
    else:
      assert t > 0
      t -= 1
    self.state = (h, t)
    return self.state
  def prob(self, val, args = None):
    assert type(val.val) == bool
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

