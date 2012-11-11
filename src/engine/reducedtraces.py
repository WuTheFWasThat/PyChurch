from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict

try:
  from pypy.rlib.jit import JitDriver
  jitdriver = JitDriver(greens = [], reds=['node'])
  
  def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

  use_jit = True
except:
  use_jit = False

# THEN, in REFLIP:

# Class representing environments
class EnvironmentNode(Environment):
  def __init__(self, parent = None):
    self.parent = parent # The parent environment
    self.assignments = {} # Dictionary from names to values

    self.assumes = {}
    self.lookups = {} # just a set
    return

  def add_assume(self, name, evalnode):
    if name in self.assumes:
      raise Exception("Already assumed something with this name")
    self.assumes[name] = evalnode

  def add_lookup(self, name, evalnode):
    if name not in self.lookups:
      self.lookups[name] = {}
    self.lookups[name][evalnode] = True

  def rem_lookup(self, name, evalnode):
    del self.lookups[name][evalnode]

  def get_lookups(self, name, evalnode):
    if self.assumes[name] is not evalnode:
      raise Exception("Wrong evalnode getting lookups for %s" % name)
    if name in self.lookups:
      return self.lookups[name]
    else:
      return {}

  def spawn_child(self): 
    return EnvironmentNode(self)

class ReducedEvalNode:
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.active = False # Whether this node is currently activated

    self.parent = None 
    self.children = {} 
    self.active_children = {} 
    # relative path -> evalnode

    self.mem = False # Whether this is the root of a mem'd procedure's application
    self.mem_calls = {} # just a set

    self.env = env # Environment in which this was evaluated
    self.lookups = {} 
    self.assume = False
    self.assume_name = None
    self.sample = False

    self.observed = False
    self.observe_val = None 

    self.xrp_applies = [] 
    # (xrp, args) list

    self.random_xrp_apply = False
    self.xrp = XRP()
    self.args = None
    self.p = 0

    self.expression = expression
    self.type = expression.type

    self.val = None
    return

  def get_child(self, addition, env, subexpr):
    if addition not in self.children:
      evalnode = self.spawnchild(addition, env, subexpr)
    else:
      evalnode = self.children[addition]
      if not evalnode.active:
        if evalnode.random_xrp_apply:
          evalnode.evaluate(evalnode.val)
        else:
          evalnode.evaluate()
      assert addition not in self.active_children 
      self.active_children[addition] = evalnode

    evalnode.env = env
    evalnode.expression = subexpr
    return evalnode
  
  def spawnchild(self, addition, env, subexpr):
    child = ReducedEvalNode(self.traces, env, subexpr)
    child.parent = self
    self.children[addition] = child # make sure this is correct
    self.active_children[addition] = child # make sure this is correct
    child.evaluate()
    return child

  def add_assume(self, name, env):
    assert env == self.env
    self.assume_name = name
    self.assume = True

  def observe(self, obs_val):
    self.observed = True
    self.observe_val = obs_val

  def addlookup(self, name, env):
    self.lookups[name] = env 
    env.add_lookup(name, self)

  def clearlookups(self):
    for name in self.lookups:
      env = self.lookups[name]
      env.rem_lookup(name, self)
    self.lookups = {}

  def setargs(self, args):
    assert self.type == 'apply'
    self.args = args

  def propogate_to(self, evalnode):
    assert evalnode.active
    if evalnode.random_xrp_apply:
      evalnode.evaluate(evalnode.val)
    else:
      evalnode.evaluate()
      evalnode.propogate_up()

  def propogate_up(self):
    # NOTE: with multiple parents, could this re-evaluate things in the wrong order and screw things up?
    assert self.active

    if self.assume:
      assert self.parent is None
      # lookups can be affected *while* propogating up. 
      lookup_nodes = []
      for evalnode in self.env.get_lookups(self.assume_name, self):
        lookup_nodes.append(evalnode)
      for evalnode in lookup_nodes:
        self.propogate_to(evalnode)
    elif self.parent is not None:
      self.propogate_to(self.parent)

    if self.mem:
      # self.mem_calls can be affected *while* propogating up.  However, if new links are created, they'll use the new value
      for evalnode in self.mem_calls.keys():
        self.propogate_to(evalnode)

  def unevaluate(self):
    # NOTE:  We may want to remove references to nodes when we unevaluate, such as when we have arguments
    # drawn from some continuous domain
    assert self.active

    expr = self.expression

    self.clearlookups()

    for addition in self.active_children:
      child = self.active_children[addition]
      assert child.active
      child.unevaluate()
    self.active_children = {}

    for (xrp, args) in self.xrp_applies:
      self.remove_xrp(xrp, args)
    self.xrp_applies = []
      
    if self.random_xrp_apply:
      self.remove_xrp(self.xrp, self.args)
      self.traces.remove_xrp(self)
    else:
      assert self.assume or self.sample or self.mem

    self.active = False
    return

  def remove_xrp(self, xrp, args):
    if xrp.is_mem():
      xrp.remove_mem(self.val, args, self)
    else:
      xrp.remove(self.val, args)
    prob = xrp.prob(self.val, self.args)
    self.traces.uneval_p += prob
    self.traces.p -= prob

  def add_xrp(self, xrp, val, args):
    prob = xrp.prob(val, args)
    self.p = prob
    self.traces.eval_p += prob
    self.traces.p += prob
    if xrp.is_mem():
      xrp.incorporate_mem(val, args, self)
    else:
      xrp.incorporate(val, args)

  # reflips own XRP, possibly with a forced value
  def apply_random_xrp(self, xrp, args, xrp_force_val = None):
    assert self.random_xrp_apply
    if self.active:
      self.remove_xrp(self.xrp, self.args)
      self.traces.remove_xrp(self)

    self.xrp = xrp
    self.args = args

    if xrp_force_val is None:
      val = self.xrp.apply(self.args)
    else:
      val = xrp_force_val
    self.add_xrp(self.xrp, val, self.args)
    self.traces.add_xrp(self.args, self)
    return val

  def evaluate(self, xrp_force_val = None):
    expr = self.expression
    env = self.env

    old_active_children = self.active_children
    self.active_children = {}

    if self.observed:
      xrp_force_val = self.observe_val

    if expr.type == 'apply':
      n = len(expr.children)
      op = self.evaluate_recurse(expr.op, env, addition = 0)

      if op.type == 'xrp' and not op.xrp.deterministic:
        args = [self.evaluate_recurse(expr.children[i], env, addition = i+1)  for i in range(n)]
        self.random_xrp_apply = True

        val = self.apply_random_xrp(op.xrp, args, xrp_force_val)
        
    if not self.random_xrp_apply:
      if xrp_force_val is not None:
        raise Exception("Can only force non-deterministic XRP applications")
      val = self.evaluate_recurse(expr, env)
      assert self.assume or self.mem or self.sample

    if self.assume:
      assert self.parent is None
      self.env.set(self.assume_name, val) # Environment in which this was evaluated

    self.val = val
    self.active = True

    for addition in old_active_children:
      if addition not in self.active_children:
        evalnode = self.children[addition]
        evalnode.unevaluate()

    return val

  def get_args_addition(self, args):
    hashval = 0
    for arg in args:
      hashval = rrandom.intmask((rrandom.r_uint(arg.__hash__()) * rrandom.r_uint(12345) + rrandom.r_uint(hashval)) % rrandom.r_uint(18446744073709551557))
    return hashval
    
  def binary_op_evaluate(self, expr, env, hashval, reflip):
    val1 = self.evaluate_recurse(expr.children[0], env, hashval, 0, reflip)
    val2 = self.evaluate_recurse(expr.children[1], env, hashval, 1, reflip)
    return (val1 , val2)

  def children_evaluate(self, expr, env, hashval, reflip):
    return [self.evaluate_recurse(expr.children[i], env, hashval, i, reflip) for i in range(len(expr.children))]
  
  # reflip = 1 # reflip all
  #          0 # reflip nothing

  def evaluate_recurse(self, expr, env, hashval = 0, addition = None, reflip = False):
    if addition is not None:
      hashval = rrandom.intmask((rrandom.r_uint(hashval) * rrandom.r_uint(67890) + rrandom.r_uint(addition)) % rrandom.r_uint(18446744073709551557))

    if expr.type == 'value':
      val = expr.val
    elif expr.type == 'variable':
      (val, lookup_env) = env.lookup(expr.name)
      self.addlookup(expr.name, lookup_env)
    elif expr.type == 'if':
      cond = self.evaluate_recurse(expr.cond, env, hashval, 0, reflip)
      if cond.bool:
        val = self.evaluate_recurse(expr.true, env, hashval, 1, reflip)
      else:
        val = self.evaluate_recurse(expr.false, env, hashval, 2, reflip)
    elif expr.type == 'let':
      # TODO: this really is a let*
      n = len(expr.vars)
      assert len(expr.expressions) == n
      values = []
      new_env = env
      for i in range(n): # Bind variables
        new_env = new_env.spawn_child()
        val = self.evaluate_recurse(expr.expressions[i], new_env, hashval, i+1, reflip)
        values.append(val)
        new_env.set(expr.vars[i], values[i])
        if val.type == 'procedure':
          val.env = new_env
      new_body = expr.body.replace(new_env)
      val = self.evaluate_recurse(new_body, new_env, hashval, 0, reflip)

    elif expr.type == 'apply':
      n = len(expr.children)
      op = self.evaluate_recurse(expr.op, env, hashval, 0, reflip)
      args = [self.evaluate_recurse(expr.children[i], env, hashval, i + 1, reflip) for i in range(n)]

      if op.type == 'procedure':
        if n != len(op.vars):
          raise Exception('Procedure should have %d arguments.  \nVars were \n%s\n, but had %d children.' % (n, op.vars, len(expr.children)))
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        addition = self.get_args_addition(args)
        val = self.evaluate_recurse(op.body, new_env, hashval, addition, reflip)
      elif op.type == 'xrp':
        xrp = op.xrp
        if not xrp.deterministic:
          child = self.get_child(hashval, env, expr)
          val = child.val
        else:
          val = xrp.apply(args)
          self.add_xrp(xrp, val, args)
          self.xrp_applies.append((xrp,args))
        self.xrp = xrp
        assert val is not None
      else:
        raise Exception('Must apply either a procedure or xrp.  Instead got expression %s' % str(op))

    elif expr.type == 'function':
      n = len(expr.vars)
      new_env = env.spawn_child()
      bound = {}
      for i in range(n): # Bind variables
        bound[expr.vars[i]] = True
      procedure_body = expr.body.replace(new_env, bound)
      val = Procedure(expr.vars, procedure_body, env)
    elif expr.type == '=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, reflip)
      val = val1.__eq__(val2)
    elif expr.type == '<':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, reflip)
      val = val1.__lt__(val2)
    elif expr.type == '>':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, reflip)
      val = val1.__gt__(val2)
    elif expr.type == '<=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, reflip)
      val = val1.__le__(val2)
    elif expr.type == '>=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, reflip)
      val = val1.__ge__(val2)
    elif expr.type == '&':
      vals = self.children_evaluate(expr, env, hashval, reflip)
      andval = BoolValue(True)
      for x in vals:
        andval = andval.__and__(x)
      val = andval
    elif expr.type == '^':
      vals = self.children_evaluate(expr, env, hashval, reflip)
      xorval = BoolValue(True)
      for x in vals:
        xorval = xorval.__xor__(x)
      val = xorval
    elif expr.type == '|':
      vals = self.children_evaluate(expr, env, hashval, reflip)
      orval = BoolValue(False)
      for x in vals:
        orval = orval.__or__(x)
      val = orval
    elif expr.type == '~':
      negval = self.evaluate_recurse(expr.children[0] , env, hashval, 0, reflip)
      val = negval.__inv__()
    elif expr.type == '+':
      vals = self.children_evaluate(expr, env, hashval, reflip)
      sum_val = NatValue(0)
      for x in vals:
        sum_val = sum_val.__add__(x)
      val = sum_val
    elif expr.type == '-':
      val1 = self.evaluate_recurse(expr.children[0] , env, hashval, 0, reflip)
      val2 = self.evaluate_recurse(expr.children[1] , env, hashval, 1, reflip)
      val = val1.__sub__(val2)
    elif expr.type == '*':
      vals = self.children_evaluate(expr, env, hashval, reflip)
      prod_val = NatValue(1)
      for x in vals:
        prod_val = prod_val.__mul__(x)
      val = prod_val
    elif expr.type == '/':
      val1 = self.evaluate_recurse(expr.children[0] , env, hashval, 0, reflip)
      val2 = self.evaluate_recurse(expr.children[1] , env, hashval, 1, reflip)
      val = val1.__div__(val2)
    else:
      raise Exception('Invalid expression type %s' % expr.type)

    return val

  def reflip(self, xrp_force_val = None):
    #if use_jit:
    #  jitdriver.jit_merge_point(node=self.val)
    assert self.active
    self.val = self.apply_random_xrp(self.xrp, self.args, xrp_force_val)
    if self.assume:
      assert self.parent is None
      self.env.set(self.assume_name, self.val) # Environment in which this was evaluated

    self.propogate_up()
    return self.val

  def str_helper(self, n = 0, verbose = True):
    string = "\n" + (' ' * n) + "|- "
    if self.assume_name is not None:
      string += self.assume_name 
    elif verbose:
      string += str(self.expression)
    else:
      string += self.type 
    if not self.active:
      string += ", INACTIVE"
    else:
      string += ", VALUE = " + str(self.val)
      for key in self.children:
        child = self.children[key]
        string += child.str_helper(n + 2)
    return string

  def __str__(self):
    if self.assume_name is None:
      return ("EvalNode of type %s, with expression %s and value %s" % (self.type, str(self.expression), str(self.val)))
    else:
      return ("EvalNode %s" % (self.assume_name))

class ReducedTraces(Engine):
  def __init__(self, env):
    self.assumes = []
    self.observes = {} # just a set

    self.db = RandomChoiceDict() 

    env.reset()
    self.env = env

    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0
    return

  def assume(self, name, expr):
    evalnode = ReducedEvalNode(self, self.env, expr)
    self.env.add_assume(name, evalnode)
    evalnode.add_assume(name, self.env)

    self.assumes.append(evalnode)
    val = evalnode.evaluate()
    return val

  def sample(self, expr):
    evalnode = ReducedEvalNode(self, self.env, expr)
    evalnode.sample = True
    val = evalnode.evaluate()
    evalnode.unevaluate()
    return val  

  def observe(self, expr, obs_val, id):
    evalnode = ReducedEvalNode(self, self.env, expr)

    assert id not in self.observes
    self.observes[id] = evalnode

    evalnode.observe(obs_val)
    evalnode.evaluate()

    return evalnode

  def forget(self, id):
    assert id in self.observes
    evalnode = self.observes[id]
    evalnode.unevaluate()
    del self.observes[id]
    return

  def rerun(self, reflip):
    # TODO: fix this
    for assume_node in self.assumes:
      assert assume_node.active
      assume_node.evaluate()
    for observe_node in self.observes.values():
      assert observe_node.active
      observe_node.evaluate()

  def reflip(self, reflip_node):
    debug = False

    if debug:
      old_self = self.__str__()

    assert reflip_node.random_xrp_apply
    assert reflip_node.val is not None
    
    self.eval_p = 0
    self.uneval_p = 0

    old_p = self.p
    old_val = reflip_node.val
    new_to_old_q = reflip_node.p
    old_to_new_q = - math.log(self.db.__len__())
    new_val = reflip_node.reflip()
    new_to_old_q -= math.log(self.db.__len__())
    old_to_new_q += reflip_node.p

    if debug:
      print "\n-----------------------------------------\n"
      print old_self
      print "\nCHANGING ", reflip_node, "\n  FROM  :  ", old_val, "\n  TO   :  ", new_val, "\n"
      if old_val == new_val:
        print "SAME VAL"
        print "new:\n", self
        return
  
    new_p = self.p
    eval_p = self.eval_p
    uneval_p = self.uneval_p
    if debug:
      print "new db", self
      print "\nq(old -> new) : ", math.exp(old_to_new_q)
      print "q(new -> old) : ", math.exp(new_to_old_q )
      print "p(old) : ", math.exp(old_p)
      print "p(new) : ", math.exp(new_p)
      print 'transition prob : ',  math.exp(new_p + new_to_old_q - old_p - old_to_new_q) , "\n"

    self.eval_p = 0
    self.uneval_p = 0
  
    p = rrandom.random.random()
    if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
      new_val = reflip_node.reflip(old_val)

      if debug: 
        print 'restore'
        #print "original uneval", math.exp(uneval_p)
        #print "original eval", math.exp(eval_p)
        #print "new uneval", math.exp(self.uneval_p)
        #print "new eval", math.exp(self.eval_p)

      #assert self.p == old_p
      #assert self.uneval_p  + uneval_p == eval_p + self.eval_p

      #assert self.uneval_p == eval_p
      #assert self.eval_p == uneval_p
      # May not be true, because sometimes things get removed then incorporated
    if debug:
      print "new:\n", self

  # Add an XRP application node to the db
  def add_xrp(self, args, evalnodecheck = None):
    evalnodecheck.setargs(args)
    assert not self.db.__contains__(evalnodecheck)
    self.db.__setitem__(evalnodecheck, True)

  def remove_xrp(self, evalnode):
    assert self.db.__contains__(evalnode)
    self.db.__delitem__(evalnode)

  def infer(self):
    try:
      evalnode = self.db.randomKey()
    except:
      # No coin flips!
      return
    self.reflip(evalnode)

  def reset(self):
    self.__init__(self.env)
    
  def __str__(self):
    string = "EvalNodeTree:"
    # Ignore default assumes
    for i in range(len(self.assumes)):
      evalnode = self.assumes[i]
      if i > 7:
        string += evalnode.str_helper()
    for id in self.observes:
      evalnode = self.observes[id]
      string += evalnode.str_helper()
    return string
