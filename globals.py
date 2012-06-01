from expressions import *
from random_choice_dict import *
import sys

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
  def __init__(self):
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    self.count = 0
    self.memory = []
    # ALWAYS WORKING WITH LOG PROBABILITIES
    self.uneval_p = 0
    self.eval_p = 0
    return

  # implement tree data-structure?
  def insert(self, stack, xrp, value, args, is_obs_noise = False, memorize = True):
    assert value.__class__.__name__ == 'Value'
    if self.has(stack):
      self.remove(stack)
    prob = xrp.prob(value, args)
    xrp.incorporate(value, args)
    if is_obs_noise:
      self.db_noise[tuple(stack)] = (xrp, value, prob, args, True)
    else:
      self.db[tuple(stack)] = (xrp, value, prob, args, False)
    if not is_obs_noise:
      self.count += 1
      self.eval_p += prob # hmmm.. 
    if memorize:
      self.memory.append(('insert', stack, xrp, value, args, is_obs_noise))

  def save(self):
    self.memory = []
    self.uneval_p = 0
    self.eval_p = 0

  def restore(self):
    self.memory.reverse()
    for (type, stack, xrp, value, args, is_obs_noise) in self.memory:
      if type == 'insert':
        self.remove(stack, False)
      else:
        assert type == 'remove'
        self.insert(stack, xrp, value, args, False, is_obs_noise)

  def remove(self, stack, memorize = True):
    assert self.has(stack)
    (xrp, value, prob, args, is_obs_noise) = self.get(stack)
    if not is_obs_noise:
      self.count -= 1
      assert self.count >= 0
      self.uneval_p += prob # previously unindented...
    xrp.remove(value, args)
    if is_obs_noise:
      del self.db_noise[tuple(stack)]
    else:
      del self.db[tuple(stack)]
    if memorize:
      self.memory.append(('remove', stack, xrp, value, args, is_obs_noise))

  def has(self, stack):
    stack = tuple(stack)
    return ((stack in self.db) or (stack in self.db_noise)) 

  def get(self, stack):
    if tuple(stack) in self.db:
      return self.db[tuple(stack)]
    elif tuple(stack) in self.db_noise:
      return self.db_noise[tuple(stack)]
    else:
      warnings.warn('Failed to get stack %s' % str(stack))
      return None

  def get_val(self, stack):
    return self.get(tuple(stack))[1]

  def random_stack(self):
    #keys = self.db.keys()
    #index = random.randint(0, len(self.db)-1)
    #return list(keys[index])
    return self.db.randomKey()

  # gets log probability
  def prob(self):
    ans = 0
    for key in self.db:
      (xrp, value, prob, args, is_obs_noise) = self.db[key]
      ans += prob
    for key in self.db_noise:
      (xrp, value, prob, args, is_obs_noise) = self.db_noise[key]
      ans += prob
    #  print '  ', xrp, prob
    #print ans 
    return ans

  def unevaluate(self, uneval_stack, args = None):
    if args is not None:
      args = tuple(args)

    to_delete = []

    def unevaluate_helper(tuple_stack):
      stack = list(tuple_stack) 
      if len(stack) >= len(uneval_stack) and stack[:len(uneval_stack)] == uneval_stack:
        if args is None:
          to_delete.append(tuple_stack)
        else:
          assert len(stack) > len(uneval_stack)
          if stack[len(uneval_stack)] == args:
            to_delete.append(tuple_stack)

    for tuple_stack in self.db:
      unevaluate_helper(tuple_stack)
    for tuple_stack in self.db_noise:
      unevaluate_helper(tuple_stack)
    for tuple_stack in to_delete:
      self.remove(tuple_stack)

  def reset(self):
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    self.count = 0
    self.save()

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
      (expr, obs_val) = tup
      if expr.hashval in self.observes:
        warnings.warn('Already observed %s' % str(expr))
      self.observes[expr.hashval] = tup 
  
  def forget(self, hashval):
    assert hashval in self.observes
    del self.observes[hashval]


# The global environment. Has assignments of names to expressions, and parent pointer 
env = Environment()

# Table storing a list of (xrp, value, probability) tuples
db = RandomDB()

# Global memory.  List of (directive type, args)
mem = Directives_Memory() 

sys.setrecursionlimit(10000)

