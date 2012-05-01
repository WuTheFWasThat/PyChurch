import random
from values import *

class beta_XRP(XRP):
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

class bernoulli_XRP(XRP):
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
    assert type(p) == float and 0 <= p <= 1
    assert type(val.val) == bool
    if val.val:
      return math.log(p)
    else:
      return math.log(1.0 - p)
  def __str__(self):
    return 'bernoulli'

class uniform_XRP(XRP):
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

