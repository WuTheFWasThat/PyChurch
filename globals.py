from expressions import *
from random_choice_dict import *
import sys

# Class representing environments
class Environment:
  def __init__(self, parent = None):
    self.parent = parent # The parent environment
    self.assignments = {} # Dictionary from names to values
    self.children = set() 
    if parent is not None:
      self.parent.children.add(self)

    self.assumes = {}
    self.lookups = {}
    return

  def reset(self):
    assert self.parent is None
    self.__init__()

  def set(self, name, value):
    assert value is not None
    self.assignments[name] = value

  def lookup(self, name):
    if name in self.assignments:
      return (self.assignments[name], self)
    else:
      if self.parent is None:
        warnings.warn('Variable %s undefined in env:\n%s' % (name, str(env)))
        assert False
      else:
        return self.parent.lookup(name)

  def add_assume(self, name, evalnode):
    self.assumes[name] = evalnode
    evalnode.add_assume(name, self)

  def add_lookup(self, name, evalnode):
    assert evalnode.traces.has(evalnode)
    if name in self.lookups:
      self.lookups[name].add(evalnode)
    else:
      self.lookups[name] = set([evalnode])

  def rem_lookup(self, name, evalnode):
    assert name in self.lookups
    self.lookups[name].remove(evalnode)

  def get_lookups(self, name, evalnode):
    assert name in self.assumes
    assert self.assumes[name] is evalnode
    if name in self.lookups:
      return self.lookups[name]
    else:
      return set()

  def spawn_child(self): 
    return Environment(self)

  def __setitem__(self, name, value):
    self.set(name, value) 

  def __getitem__(self, name):
    return self.lookup(name) 

  def __str__(self):
    return self.assignments.__str__()

class EvalNode:
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.active = False # Whether this node is currently activated

    self.parent = None 
    self.children = {} 
    self.applychildren = {} 

    self.mem = False # Whether this is the root of a mem'd procedure's application
    self.mem_calls = set()

    self.env = env # Environment in which this was evaluated
    self.lookup = None 
    self.assume = False
    self.assume_name = None

    self.observed = False
    self.observe_val = None 

    self.random_xrp_apply = False
    self.xrp_apply = False
    self.procedure_apply = False
    self.args = None

    self.expression = expression
    self.type = expression.type

    self.val = None
    return

  def get_child(self, addition, env, subexpr):
    if type(addition) == tuple:
      if addition not in self.applychildren:
        self.spawnchild(addition, env, subexpr, True)
      return self.applychildren[addition]
    else:
      if addition not in self.children:
        self.spawnchild(addition, env, subexpr, False)
      return self.children[addition]
  
  def spawnchild(self, addition, env, subexpr, is_apply):
    child = EvalNode(self.traces, env, subexpr)
    child.parent = self
    if is_apply:
      self.applychildren[addition] = child
    else:
      self.children[addition] = child
    self.traces.add_node(child)

  def add_assume(self, name, env):
    assert env == self.env
    self.assume_name = name
    self.assume = True

  def observe(self, obs_val):
    self.observed = True
    self.observe_val = obs_val

  def setlookup(self, env):
    assert self.expression.type == 'variable'
    self.lookup = env 
    env.add_lookup(self.expression.name, self)

  def remlookup(self, name, env):
    self.lookup = None
    env.rem_lookup(name, self)

  def setargs(self, args):
    assert self.type == 'apply'
    self.args = args

  def propogate_up(self):
    assert self.active

    oldval = self.val
    if self.observed:
      assert self.random_xrp_apply
      val = self.evaluate(reflip = 0.5, xrp_force_val = self.observe_val)
      assert val == oldval
      # TODO: might this be wrong initially? 
    else:
      if self.random_xrp_apply:
        val = self.evaluate(reflip = 0.5, xrp_force_val = self.val)
        assert val == oldval
      else:
        val = self.evaluate(reflip = 0.5, xrp_force_val = None)

      if self.assume:
        assert self.parent is None
        for evalnode in self.env.get_lookups(self.assume_name, self):
          assert self.traces.has(evalnode)
          evalnode.propogate_up()
      elif self.parent is not None:
        self.parent.propogate_up()
    if self.mem:
      # self.mem_calls can actually be affected while propogating up.  However, if new links are created, they'll use the new value
      for evalnode in list(self.mem_calls):
        evalnode.propogate_up()

    self.val = val
    return self.val

  def unevaluate(self):
    if not self.active:
      return
    expr = self.expression
    if self.type == 'variable':
      # Don't remove reference value.
      assert self.lookup
      self.remlookup(expr.name, self.lookup)
    elif self.type == 'apply':
      n = len(expr.children)
      for i in range(n):
        self.get_child(i, self.env, expr.children[i]).unevaluate()
      self.get_child(-2, self.env, expr.op).unevaluate()
      if self.procedure_apply: 
        assert (-1, tuple(hash(x) for x in self.args)) in self.applychildren
        self.applychildren[(-1, tuple(hash(x) for x in self.args))].unevaluate()
        #self.get_child((-1, tuple(hash(x) for x in self.args)), self.env, op.body).unevaluate()
      else:
        assert self.xrp_apply
        self.remove_xrp(self.xrp, self.args)
    else:
      for x in self.children:
        self.children[x].unevaluate()

    self.active = False
    return self.val

  def remove_xrp(self, xrp, args):
    assert self.active
    if xrp.__class__.__name__ == 'mem_proc_XRP':
      xrp.remove(self.val, args, self)
    else:
      xrp.remove(self.val, args)
    prob = xrp.prob(self.val, self.args)
    self.traces.uneval_p += prob
    self.traces.p -= prob
    if ((not xrp.deterministic) and (not xrp.__class__.__name__ == 'mem_proc_XRP')):
      self.traces.remove_xrp(self)

  def add_xrp(self, xrp, val, args):
    prob = xrp.prob(val, args)
    self.traces.eval_p += prob
    self.traces.p += prob
    if xrp.__class__.__name__ == 'mem_proc_XRP':
      xrp.incorporate(val, args, self)
    else:
      xrp.incorporate(val, args)

    if ((not xrp.deterministic) and (not xrp.__class__.__name__ == 'mem_proc_XRP')):
      self.random_xrp_apply = True
      self.traces.add_xrp(args, self)

  # reflip = 1 # reflip all
  #          0.5 # reflip current, but don't recurse
  #          0 # reflip nothing
  def evaluate(self, reflip = False, xrp_force_val = None):
    if not self.traces.has(self):
      assert False
    if reflip == False and self.active:
      assert self.val is not None
      return self.val

    expr = self.expression

    def evaluate_recurse(subexpr, env, addition):
      val = self.get_child(addition, env, subexpr).evaluate(reflip == True)
      return val
  
    def binary_op_evaluate(op):
      val1 = evaluate_recurse(expr.children[0], self.env, 0).val
      val2 = evaluate_recurse(expr.children[1], self.env, 1).val
      return Value(op(val1 , val2))

    def list_op_evaluate(op):
      vals = [evaluate_recurse(expr.children[i], self.env, i).val for i in xrange(len(expr.children))]
      return Value(reduce(op, vals))
  
    if xrp_force_val is not None:
      assert self.type == 'apply'

    if self.type == 'value':
      val = expr.val
    elif self.type == 'variable':
      # TODO : is this right?
      (val, lookup_env) = self.env.lookup(expr.name)
      self.setlookup(lookup_env)
    elif self.type == 'if':
      cond = evaluate_recurse(expr.cond, self.env, -1)
      assert type(cond.val) in [bool]
      if cond.val:
        self.get_child(0, self.env, expr.false).unevaluate()
        val = evaluate_recurse(expr.true, self.env, 1)
      else:
        self.get_child(1, self.env, expr.true).unevaluate()
        val = evaluate_recurse(expr.false, self.env, 0)
    elif self.type == 'switch':
      index = evaluate_recurse(expr.index, self.env, -1)
      assert type(index.val) in [int]
      assert 0 <= index.val < expr.n
      for i in range(expr.n):
        if i != index.val:
          self.get_child(i, self.env, expr.children[i]).unevaluate()
      val = evaluate_recurse(self.children[index.val] , self.env, index.val)
    elif self.type == 'let':
      # TODO: think more about the behavior with environments here...
      
      n = len(expr.vars)
      assert len(expr.expressions) == n
      values = []
      new_env = self.env
      for i in range(n): # Bind variables
        new_env = new_env.spawn_child()
        val = evaluate_recurse(expr.expressions[i], new_env, i)
        values.append(val)
        new_env.set(expr.vars[i], values[i])
        if val.type == 'procedure':
          val.env = new_env
      new_body = expr.body.replace(new_env)
      val = evaluate_recurse(new_body, new_env, -1)

    elif self.type == 'apply':
      n = len(expr.children)
      args = [evaluate_recurse(expr.children[i], self.env, i) for i in range(n)]
      op = evaluate_recurse(expr.op, self.env, -2)
      if op.type == 'procedure':
        self.procedure_apply = True
        for x in self.applychildren:
          if x != tuple(hash(x) for x in args):
            self.applychildren[x].unevaluate()

        if n != len(op.vars):
          warnings.warn('Procedure should have %d arguments.  \nVars were \n%s\n, but children were \n%s.' % (n, op.vars, self.chidlren))
          assert False
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        val = evaluate_recurse(op.body, new_env, (-1, tuple(hash(x) for x in args)))
      elif op.type == 'xrp':
        self.xrp_apply = True
        xrp = op.val

        if xrp_force_val != None:
          assert reflip != True
          assert not xrp.__class__.__name__ == 'mem_proc_XRP'
          assert not xrp.deterministic
          val = xrp_force_val
          if self.active:
            self.remove_xrp(xrp, self.args)
          self.add_xrp(xrp, val, args)
        elif self.observed:
          val = self.observe_val
          assert not xrp.__class__.__name__ == 'mem_proc_XRP'
          assert not xrp.deterministic
          if self.active:
            self.remove_xrp(xrp, self.args)
          self.add_xrp(xrp, val, args)
        elif xrp.deterministic or (not reflip):
          if self.active:
            val = self.val
          else:
            val = value(xrp.apply(args))
            self.add_xrp(xrp, val, args)
        else: # not deterministic, needs reflipping
          if self.active:
            self.remove_xrp(xrp, self.args)
          val = value(xrp.apply(args))
          self.add_xrp(xrp, val, args)

        self.xrp = xrp
        assert val is not None
      else:
        warnings.warn('Must apply either a procedure or xrp')

      self.args = args
    elif self.type == 'function':
      val = self.val
      n = len(expr.vars)
      new_env = env.spawn_child()
      for i in range(n): # Bind variables
        new_env.set(expr.vars[i], expr.vars[i])
      procedure_body = expr.body.replace(new_env)
      val = Value((expr.vars, procedure_body), env)
      #TODO: SET SOME RELATIONSHIP HERE?  If body contains reference to changed var...
    elif self.type == '=':
      val = binary_op_evaluate(lambda x, y : x == y)
    elif self.type == '<':
      val = binary_op_evaluate(lambda x, y : x < y)
    elif self.type == '>':
      val = binary_op_evaluate(lambda x, y : x > y)
    elif self.type == '<=':
      val = binary_op_evaluate(lambda x, y : x <= y)
    elif self.type == '>=':
      val = binary_op_evaluate(lambda x, y : x >= y)
    elif self.type == '&':
      val = list_op_evaluate(lambda x, y : x & y)
    elif self.type == '^':
      val = list_op_evaluate(lambda x, y : x ^ y)
    elif self.type == '|':
      val = list_op_evaluate(lambda x, y : x | y)
    elif self.type == '~':
      negval = evaluate_recurse(expr.negation , self.env, 0).val
      val = Value(not negval)
    elif self.type == 'add':
      val = list_op_evaluate(lambda x, y : x + y)
    elif self.type == 'subtract':
      val1 = evaluate_recurse(expr.children[0] , self.env, 0).val
      val2 = evaluate_recurse(expr.children[1] , self.env, 1).val
      val = Value(val1 - val2)
    elif self.type == 'multiply':
      val = list_op_evaluate(lambda x, y : x * y)
    else:
      warnings.warn('Invalid expression type %s' % self.type)
      assert False

    self.val = val
    self.active = True

    if self.assume:
      assert self.parent is None
      self.env.set(self.assume_name, val) # Environment in which this was evaluated

    return val

  def reflip(self, force_val = None):
    self.evaluate(reflip = 0.5, xrp_force_val = force_val)
    self.propogate_up()
    return self.val

  def str_helper(self, n = 0, verbose = True):
    string = "\n" + (' ' * n) + "|- "
    if verbose:
      string += str(self.expression)
    else:
      string += self.type 
    if not self.active:
      string += ", INACTIVE"
    else:
      string += ", VALUE = " + str(self.val)
      for key in self.children:
        string += self.children[key].str_helper(n + 2)
      for key in self.applychildren:
        string += self.applychildren[key].str_helper(n + 2)
    return string

  def __str__(self):
    return ("EvalNode of type %s, with expression %s and value %s" % (self.type, str(self.expression), str(self.val)))

class Traces:
  def __init__(self, env):
    self.evalnodes = set() 

    # set of evalnodes with no parents
    self.roots = set() 

    self.db = RandomChoiceDict() 

    self.global_env = env

    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0
    return

  def assume(self, name, expr):
    evalnode = EvalNode(self, self.global_env, expr)
    self.add_node(evalnode)

    self.roots.add(evalnode)
    val = evalnode.evaluate()
    self.global_env.add_assume(name, evalnode)
    self.global_env.set(name, val)
    return val

  def observe(self, expr, obs_val):
    evalnode = EvalNode(self, self.global_env, expr)
    self.add_node(evalnode)

    evalnode.observe(obs_val)
    self.roots.add(evalnode)
    evalnode.evaluate()

    return evalnode

  def rerun(self, reflip):
    for root in self.roots:
      root.evaluate(reflip)

  def has(self, evalnode):
    return evalnode in self.evalnodes

  def reflip(self, reflip_node):
    debug = True

    if debug:
      print "\n-----------------------------------------\n"
      print self

    assert reflip_node.type == 'apply'
    assert reflip_node.val is not None
    
    self.eval_p = 0
    self.uneval_p = 0

    old_p = self.p
    old_val = reflip_node.val
    old_count = len(self.db)
    new_val = reflip_node.reflip()
    new_count = len(self.db)

    assert -2 in reflip_node.children
    assert reflip_node.children[-2].val.type == 'xrp'
    xrp = reflip_node.children[-2].val.val

    #print old_val, old_count, new_val, new_count

    print "\nCHANGING ", reflip_node, "\n  TO   :  ", new_val, "\n"
    if debug:
      if old_val == new_val:
        print "SAME VAL"
        return
  
    new_p = self.p
    uneval_p = self.uneval_p
    eval_p = self.eval_p
    new_to_old_q = - math.log(new_count) 
    old_to_new_q = - math.log(old_count)
    if debug:
      print "new db", self
      print "\nq(old -> new) : ", old_to_new_q
      print "q(new -> old) : ", new_to_old_q 
      print "p(old) : ", old_p
      print "p(new) : ", new_p
      print 'log transition prob : ',  new_p + new_to_old_q - old_p - old_to_new_q , "\n"
  
    if old_p * old_to_new_q > 0:
      p = random.random()
      if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
        if debug: 
          print 'restore'
        new_val = reflip_node.reflip(old_val)
        #assert self.p == old_p
        #assert self.uneval_p == eval_p
        #assert self.eval_p == uneval_p
  
    if debug: 
      print "new ", self

    # ENVELOPE CALCULATION?

  def evaluate(self, expression, reflip = False):
    assert False
    stack = ['expr', expression.hashval]
    evalnode = self.get_or_make(stack, expression)
    self.roots.add(evalnode)
    val = evalnode.evaluate(reflip)
    return val

  def add_node(self, evalnode):
    assert not self.has(evalnode)
    self.evalnodes.add(evalnode)

  # Add an XRP application node to the db
  def add_xrp(self, args, evalnodecheck = None):
    assert evalnodecheck in self.evalnodes
    evalnodecheck.setargs(args)
    self.db[evalnodecheck] = True

  def remove_xrp(self, evalnode):
    assert self.has(evalnode)
    assert evalnode in self.db
    del self.db[evalnode] 

  def random_node(self):
    evalnode = self.db.randomKey()
    return evalnode

  def reset(self):
    self.__init__(self.global_env)
    
  def __str__(self):
    string = "EvalNodeTree:"
    for evalnode in self.roots:
      string += evalnode.str_helper()
    return string

# Class representing random db
class RandomDB:
  def __init__(self):
    #self.db = {} 
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    # TODO: remove count
    self.count = 0
    assert self.count == len(self.db)
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
      self.db_noise[stack] = (xrp, value, args, True)
    else:
      self.db[stack] = (xrp, value, args, False)
    if not is_obs_noise:
      self.count += 1
      self.eval_p += prob # hmmm.. 
      assert self.count == len(self.db)
    if memorize:
      self.memory.append(('insert', stack, xrp, value, args, is_obs_noise))

  def remove(self, stack, memorize = True):
    stack = tuple(stack)
    assert self.has(stack)
    (xrp, value, args, is_obs_noise) = self.get(stack)
    xrp.remove(value, args)
    prob = xrp.prob(value, args)
    self.p -= prob
    if is_obs_noise:
      del self.db_noise[stack]
    else:
      del self.db[stack]
      self.count -= 1
      assert self.count >= 0
      self.uneval_p += prob # previously unindented...
    assert self.count == len(self.db)
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
    key = self.db.randomKey()
    return key

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
    assert self.count == len(self.db)
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

# The traces datastructure. 
# DAG of two interlinked trees: 
#   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
#   2. environments
# crosslinked by symbol lookup nodes and by the env argument to eval
traces = Traces(env)

# Table storing a list of (xrp, value, probability) tuples
db = RandomDB()

# Global memory.  List of (directive type, args)
mem = Directives_Memory() 

sys.setrecursionlimit(10000)

use_traces = True
