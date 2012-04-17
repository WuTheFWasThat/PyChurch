from expressions import *

# Class representing environments
class Environment:
  def __init__(self, parent = None):
    # The parent environment
    self.parent = parent
    # Dictionary from names to values
    self.assignments = {}
    return

  def set(self, name, expression):
    self.assignments[name] = expression

  def lookup(self, name):
    if name in self.assignments:
      return self.assignments[name]
    else:
      if self.parent is None:
        return None
      else:
        return self.parent.lookup(name)

  def spawn_child(self): 
    return Environment(self)

# Class representing random db
class RandomDB:
  def __init__(self, noise_xrp):
    self.db = {}
    self.noise_xrp = noise_xrp  
    self.count = 0
    self.memory = []
    self.uneval_p = 1
    self.eval_p = 1
    return
  
  # implement tree data-structure?
  def insert(self, stack, xrp, value, args, memorize = True):
    assert value.__class__.__name__ == 'Value'
    if self.has(stack):
      self.remove(stack)
    prob = xrp.prob(value, args)
    xrp.incorporate(value, args)
    self.db[tuple(stack)] = (xrp, value, prob, args)
    if xrp is not self.noise_xrp:
      self.count += 1
      self.eval_p *= prob 
    if memorize:
      self.memory.append(('insert', stack, xrp, value, args))

  def save(self):
    self.memory = []
    self.uneval_p = 1
    self.eval_p = 1

  def restore(self):
    self.memory.reverse()
    for (type, stack, xrp, value, args) in self.memory:
      if type == 'insert':
        self.remove(stack, False)
      else:
        assert type == 'remove'
        self.insert(stack, xrp, value, args, False)

  def remove(self, stack, memorize = True):
    assert self.has(stack)
    (xrp, value, prob, args) = self.get(stack)
    if xrp is not self.noise_xrp:
      self.count -= 1
      assert self.count >= 0
      self.uneval_p *= prob
    xrp.remove(value, args)
    del self.db[tuple(stack)]
    if memorize:
      self.memory.append(('remove', stack, xrp, value, args))

  def has(self, stack):
    return tuple(stack) in self.db

  def get(self, stack):
    if tuple(stack) in self.db:
      return self.db[tuple(stack)]
    else:
      return None

  def get_val(self, stack):
    return self.get(tuple(stack))[1]

  def random_stack(self):
    keys = self.db.keys()
    index = random.randint(0, len(self.db)-1)
    return list(keys[index])

  def prob(self):
    ans = 1
    for key in self.db:
      (xrp, value, prob, args) = self.db[key]
      ans *= prob
    return ans

  def unevaluate(self, uneval_stack):
    to_delete = []
    for tuple_stack in self.db:
      stack = list(tuple_stack) 
      if len(stack) >= len(uneval_stack) and stack[:len(uneval_stack)] == uneval_stack:
        to_delete.append(tuple_stack)
    for tuple_stack in to_delete:
      self.remove(tuple_stack)

  def reset(self):
    self.db = {}
    self.count = 0
    self.save()

# Class representing observations
class Observations:
  def __init__(self, noise_xrp):
    self.noise_xrp = noise_xrp  
    self.obs = {}

  def observe(self, expr, val, args = []):
    if expr in self.obs: 
      warnings.warn('Reboserving %s' % str(expr))
    noisy_expr = ifelse(apply(self.noise_xrp, args), (expression(expr) == val), True)
    self.obs[expr] = (noisy_expr, value(val), args)
    return noisy_expr

  def has(self, expr):
    return expr in self.obs

  def get(self, expr):
    return self.obs[expr]

  def get_noisy(self, expr):
    return self.obs[expr][0]

  def get_val(self, expr):
    return self.obs[expr][1]

  def get_args(self, expr):
    return self.obs[expr][2]

  def forget(self, expr):
    if self.has(expr):
      val = self.get_val(expr)
      args = self.get_args(expr)
      self.noise_xrp.remove(val, args)
      del self.obs[expr]

class Directives_Memory:
  def __init__(self):
    self.assumes = []
    self.observes = {}
    self.vars = {}

  def reset(self):
    self.__init__()

  def add(self, type, tup): 
    if type == 'assume':
      (varname, expr) = tup
      self.assumes.append(tup)
      self.vars[varname] = expr
    else:
      assert type == 'observe'
      (expr, obs_val, args) = tup
      if expr in self.observes:
        warnings.warn('Already observed %s' % str(expr))
      self.observes[expr] = (value(obs_val), args)
  
  def forget(self, expr):
    assert expr in self.observes
    del self.observes[expr]


# The global environment. Has assignments of names to expressions, and parent pointer 
env = Environment()

noise_xrp = beta_bernoulli_1((10000, 1)) 

# A dictionary mapping expressions to values
obs = Observations(noise_xrp) 

# Table storing a list of (xrp, value, probability) tuples
db = RandomDB(noise_xrp)

# Global memory.  List of (directive type, args)
mem = Directives_Memory() 
