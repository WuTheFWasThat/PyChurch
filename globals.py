from expressions import *
from random_choice_dict import *
import sys

# Class representing environments
class Environment:
  def __init__(self, parent = None):
    self.parent = parent # The parent environment
    self.assignments = {} # Dictionary from names to values
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

  def __setitem__(self, name, expression):
    self.set(name, expression) 

  def __getitem__(self, name):
    self.lookup(name) 

# Class representing random db
class RandomDB:
  def __init__(self):
    #self.db = {} 
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    self.count = 0
    self.memory = []
    # ALWAYS WORKING WITH LOG PROBABILITIES
    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0 
    return

  def insert(self, stack, xrp, value, args, is_obs_noise = False, memorize = True):
    stack = tuple(stack)
    assert value.__class__.__name__ == 'Value'
    if self.has(stack):
      self.remove(stack)
    prob = xrp.prob(value, args)
    self.p += prob
    xrp.incorporate(value, args)
    if is_obs_noise:
      self.db_noise[stack] = (xrp, value, prob, args, True)
    else:
      self.db[stack] = (xrp, value, prob, args, False)
    if not is_obs_noise:
      self.count += 1
      self.eval_p += prob # hmmm.. 
    if memorize:
      self.memory.append(('insert', stack, xrp, value, args, is_obs_noise))

  def remove(self, stack, memorize = True):
    stack = tuple(stack)
    assert self.has(stack)
    (xrp, value, prob, args, is_obs_noise) = self.get(stack)
    self.p -= prob
    if not is_obs_noise:
      self.count -= 1
      assert self.count >= 0
      self.uneval_p += prob # previously unindented...
    xrp.remove(value, args)
    if is_obs_noise:
      del self.db_noise[stack]
    else:
      del self.db[stack]
    if memorize:
      self.memory.append(('remove', stack, xrp, value, args, is_obs_noise))

  def has(self, stack):
    stack = tuple(stack)
    return ((stack in self.db) or (stack in self.db_noise)) 

  def get(self, stack):
    stack = tuple(stack)
    if stack in self.db:
      return self.db[stack]
    elif stack in self.db_noise:
      return self.db_noise[stack]
    else:
      warnings.warn('Failed to get stack %s' % str(stack))
      return None

  def random_stack(self):
    #return list(random.choice(self.db.keys()))
    return self.db.randomKey()

  #def prob(self):
  #  ans = 0
  #  for key in self.db:
  #    (xrp, value, prob, args, is_obs_noise) = self.db[key]
  #    ans += prob
  #  for key in self.db_noise:
  #    (xrp, value, prob, args, is_obs_noise) = self.db_noise[key]
  #    ans += prob
  #  return ans 

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
          if stack[len(uneval_stack)] != args:
            to_delete.append(tuple_stack)

    for tuple_stack in self.db:
      unevaluate_helper(tuple_stack)
    for tuple_stack in self.db_noise:
      unevaluate_helper(tuple_stack)

    for tuple_stack in to_delete:
      self.remove(tuple_stack)

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
        self.insert(stack, xrp, value, args, is_obs_noise, False)

  def reset(self):
    #self.db = {} 
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    self.count = 0
    self.save()
    self.p = 0

  def __str__(self):
    string = 'DB with state:'
    string += '\n  Regular Flips:'
    for s in self.db:
      string += '\n    %s <- %s' % (self.db[s][1].val, s) 
    string += '\n  Observe Flips:'
    for s in self.db_noise:
      string += '\n    %s <- %s' % (self.db_noise[s][1].val, s) 
    return string

  def __contains__(self, stack):
    return self.has(self, stack)

  def __getitem__(self, stack):
    return self.get(self, stack)

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
