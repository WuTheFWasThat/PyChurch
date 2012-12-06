from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict
import utils.rhash as rhash
from utils.rexceptions import RException

# The reduced traces datastructure. 

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
      raise RException("Already assumed something with this name")
    self.assumes[name] = evalnode

  def add_lookup(self, name, evalnode):
    if name not in self.lookups:
      self.lookups[name] = {}
    self.lookups[name][evalnode] = True

  def rem_lookup(self, name, evalnode):
    del self.lookups[name][evalnode]

  def get_lookups(self, name, evalnode):
    if self.assumes[name] is not evalnode:
      raise RException("Wrong evalnode getting lookups for %s" % name)
    if name in self.lookups:
      return self.lookups[name]
    else:
      return {}

  def spawn_child(self): 
    return EnvironmentNode(self)

class ReducedEvalNode:
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.parent = None 

    self.mem = False # Whether this is the root of a mem'd procedure's application
    self.mem_calls = {} # just a set

    self.env = env # Environment in which this was evaluated

    self.assume = False
    self.assume_name = None
    self.predict = False

    self.observed = False
    self.observe_val = None 

    self.expression = expression
    self.type = expression.type

    self.hashval = rrandom.random.randbelow()
    self.reset()
    return

  # Reset things that have to do with current run, but not with program
  def reset(self):
    self.active = False # Whether this node is currently activated

    self.children = {}  
    self.active_children = {}  
    # relative path -> evalnode

    self.lookups = {}  

    self.xrp_applies = []  
    # (xrp, args) list
    self.random_xrp_apply = False
    self.xrp = XRP()
    self.args = None
    self.p = 0

    self.val = None

  def get_child(self, addition, env, subexpr, restore):
    if addition not in self.children:
      evalnode = self.spawnchild(addition, env, subexpr)
    else:
      evalnode = self.children[addition]
      if not evalnode.active:
        if evalnode.random_xrp_apply:
          if restore:
            evalnode.evaluate(evalnode.val, restore)
          else:
            evalnode.evaluate()
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

  def propagate_to(self, evalnode, restore_inactive):
    assert evalnode.active
    if evalnode.random_xrp_apply:
      evalnode.evaluate(evalnode.val, restore_inactive)
    else:
      evalnode.evaluate(None, restore_inactive)
      evalnode.propagate_up(restore_inactive)

  # restore_inactive:  whether to restore or to reflip inactive nodes that get activated
  def propagate_up(self, restore_inactive = False):
    # NOTE: with multiple parents, could this re-evaluate things in the wrong order and screw things up?
    assert self.active

    if self.assume:
      assert self.parent is None
      # lookups can be affected *while* propagating up. 
      lookup_nodes = []
      for evalnode in self.env.get_lookups(self.assume_name, self):
        lookup_nodes.append(evalnode)
      for evalnode in lookup_nodes:
        self.propagate_to(evalnode, restore_inactive)
    elif self.parent is not None:
      self.propagate_to(self.parent, restore_inactive)

    if self.mem:
      # self.mem_calls can be affected *while* propagating up.  However, if new links are created, they'll use the new value
      for evalnode in self.mem_calls.keys():
        self.propagate_to(evalnode, restore_inactive)

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

    for (xrp, val, args) in self.xrp_applies:
      self.remove_xrp(xrp, val, args)
    self.xrp_applies = []
      
    if self.random_xrp_apply:
      self.remove_xrp(self.xrp, self.val, self.args)
      self.traces.remove_xrp(self)
    else:
      assert self.assume or self.predict or self.mem

    self.active = False
    return

  def remove_xrp(self, xrp, val, args, called = False):
    if xrp.is_mem_proc():
      xrp.remove_mem(val, args, self.traces, self)
    else:
      xrp.remove(val, args)
    prob = xrp.prob(val, args)
    if not self.observed:
      self.traces.uneval_p += prob
    self.traces.p -= prob

  def add_xrp(self, xrp, val, args):
    prob = xrp.prob(val, args)
    if not self.observed:
      self.traces.eval_p += prob
    self.traces.p += prob
    self.p = prob
    if xrp.is_mem_proc():
      xrp.incorporate_mem(val, args, self.traces, self)
    else:
      xrp.incorporate(val, args)

  # reflips own XRP, possibly with a forced value
  def apply_random_xrp(self, xrp, args, xrp_force_val = None):
    assert self.random_xrp_apply
    if self.active:
      self.remove_xrp(self.xrp, self.val, self.args, True)
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

  def evaluate(self, xrp_force_val = None, restore = False):
    expr = self.expression
    env = self.env

    old_active_children = self.active_children
    self.active_children = {}

    if self.observed:
      xrp_force_val = self.observe_val

    for (xrp, val, args) in self.xrp_applies:
      self.remove_xrp(xrp, val, args)
    self.xrp_applies = []

    # TODO: use directive ids... and something else for mems?
    val = self.evaluate_recurse(expr, env, 0, 0, xrp_force_val, restore)

    if not self.random_xrp_apply:
      if xrp_force_val is not None:
        raise RException("Can only force non-deterministic XRP applications")
      assert self.assume or self.mem or self.predict

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

  def binary_op_evaluate(self, expr, env, hashval, restore):
    val1 = self.evaluate_recurse(expr.children[0], env, hashval, 1, None, restore)
    val2 = self.evaluate_recurse(expr.children[1], env, hashval, 2, None, restore)
    return (val1 , val2)

  def children_evaluate(self, expr, env, hashval, restore):
    return [self.evaluate_recurse(expr.children[i], env, hashval, i+1, None, restore) for i in range(len(expr.children))]
  
  def evaluate_recurse(self, expr, env, hashval, addition, xrp_force_val = None, restore = False):
    hashval = rhash.hash_pair(hashval, addition)

    if expr.type == 'value':
      val = expr.val
    elif expr.type == 'variable':
      (val, lookup_env) = env.lookup(expr.name)
      self.addlookup(expr.name, lookup_env)
    elif expr.type == 'if':
      cond = self.evaluate_recurse(expr.cond, env, hashval, 1, None, restore)
      if cond.bool:
        val = self.evaluate_recurse(expr.true, env, hashval, 2, None, restore)
      else:
        val = self.evaluate_recurse(expr.false, env, hashval, 3, None, restore)
    elif expr.type == 'let':
      # TODO: this really is a let*
      # Does environment stuff work properly?
      n = len(expr.vars)
      assert len(expr.expressions) == n
      values = []
      new_env = env
      for i in range(n): # Bind variables
        new_env = new_env.spawn_child()
        val = self.evaluate_recurse(expr.expressions[i], new_env, hashval, i+2, None, restore)
        values.append(val)
        new_env.set(expr.vars[i], values[i])
        if val.type == 'procedure':
          val.env = new_env
      new_body = expr.body.replace(new_env, {}, self)
      val = self.evaluate_recurse(new_body, new_env, hashval, 1, None, restore)

    elif expr.type == 'apply':
      n = len(expr.children)
      op = self.evaluate_recurse(expr.op, env, hashval, 1, None, restore)
      args = [self.evaluate_recurse(expr.children[i], env, hashval, i+2, None, restore) for i in range(n)]

      if op.type == 'procedure':
        if n != len(op.vars):
          raise RException('Procedure should have %d arguments.  \nVars were \n%s\n, but had %d children.' % (n, op.vars, len(expr.children)))
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        addition = rhash.hash_many([x.__hash__() for x in args])
        val = self.evaluate_recurse(op.body, new_env, hashval, addition, None, restore)
      elif op.type == 'xrp':
        xrp = op.xrp
        if not xrp.deterministic:
          if hashval == 0:
            self.random_xrp_apply = True
            val = self.apply_random_xrp(xrp, args, xrp_force_val)
          else:
            child = self.get_child(hashval, env, expr, restore)
            val = child.val
        else:
          if xrp.is_mem_proc():
            val = xrp.apply_mem(args, self.traces)
          else:
            val = xrp.apply(args)
          self.add_xrp(xrp, val, args)
          if not xrp.is_mem_proc(): # NOTE: I think this is okay
            self.xrp_applies.append((xrp, val, args))
        assert val is not None
      else:
        raise RException('Must apply either a procedure or xrp.  Instead got expression %s' % str(op))

    elif expr.type == 'function':
      n = len(expr.vars)
      new_env = env.spawn_child()
      bound = {}
      for i in range(n): # Bind variables
        bound[expr.vars[i]] = True
      procedure_body = expr.body.replace(new_env, bound, self)
      val = Procedure(expr.vars, procedure_body, env)
    elif expr.type == '=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, restore)
      val = val1.__eq__(val2)
    elif expr.type == '<':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, restore)
      val = val1.__lt__(val2)
    elif expr.type == '>':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, restore)
      val = val1.__gt__(val2)
    elif expr.type == '<=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, restore)
      val = val1.__le__(val2)
    elif expr.type == '>=':
      (val1, val2) = self.binary_op_evaluate(expr, env, hashval, restore)
      val = val1.__ge__(val2)
    elif expr.type == '&':
      vals = self.children_evaluate(expr, env, hashval, restore)
      andval = BoolValue(True)
      for x in vals:
        andval = andval.__and__(x)
      val = andval
    elif expr.type == '^':
      vals = self.children_evaluate(expr, env, hashval, restore)
      xorval = BoolValue(True)
      for x in vals:
        xorval = xorval.__xor__(x)
      val = xorval
    elif expr.type == '|':
      vals = self.children_evaluate(expr, env, hashval, restore)
      orval = BoolValue(False)
      for x in vals:
        orval = orval.__or__(x)
      val = orval
    elif expr.type == '~':
      negval = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = negval.__inv__()
    elif expr.type == 'abs':
      orig_val = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = orig_val.__abs__()
    elif expr.type == 'int':
      orig_val = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = orig_val.__int__()
    elif expr.type == 'round':
      orig_val = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = orig_val.__round__()
    elif expr.type == 'floor':
      orig_val = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = orig_val.__floor__()
    elif expr.type == 'ceil':
      orig_val = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val = orig_val.__ceil__()
    elif expr.type == '+':
      vals = self.children_evaluate(expr, env, hashval, restore)
      sum_val = NatValue(0)
      for x in vals:
        sum_val = sum_val.__add__(x)
      val = sum_val
    elif expr.type == '-':
      val1 = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val2 = self.evaluate_recurse(expr.children[1] , env, hashval, 2, None, restore)
      val = val1.__sub__(val2)
    elif expr.type == '*':
      vals = self.children_evaluate(expr, env, hashval, restore)
      prod_val = NatValue(1)
      for x in vals:
        prod_val = prod_val.__mul__(x)
      val = prod_val
    elif expr.type == '/':
      val1 = self.evaluate_recurse(expr.children[0] , env, hashval, 1, None, restore)
      val2 = self.evaluate_recurse(expr.children[1] , env, hashval, 2, None, restore)
      val = val1.__div__(val2)
    elif expr.type == '%':
      val1 = self.evaluate_recurse(expr.children[0], env, hashval, 1, None, restore)
      val2 = self.evaluate_recurse(expr.children[1], env, hashval, 2, None, restore)
      val = val1.__mod__(val2)
    else:
      raise RException('Invalid expression type %s' % expr.type)

    return val

  def reflip(self, xrp_force_val = None, restore_inactive = False):

    assert self.active
    self.val = self.apply_random_xrp(self.xrp, self.args, xrp_force_val)
    if self.assume:
      assert self.parent is None
      self.env.set(self.assume_name, self.val) # Environment in which this was evaluated

    self.propagate_up(restore_inactive)
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
  def __init__(self):
    self.engine_type = 'reduced traces'

    self.assumes = {} # id -> evalnode
    self.observes = {} # id -> evalnode
    self.predicts = {} # id -> evalnode
    self.directives = []

    self.db = RandomChoiceDict() 

    self.env = EnvironmentNode()

    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0

    self.made_proposals = 0
    self.accepted_proposals = 0
    
    self.mhstats_details = False
    self.mhstats = {}

    self.hashval = rrandom.random.randbelow()
    return

  def mhstats_on(self):
    self.mhstats_details = True

  def mhstats_off(self):
    self.mhstats_details = False

  def mhstats_aggregated(self):
    d = {}
    d['made-proposals'] = self.made_proposals
    d['accepted-proposals'] = self.accepted_proposals
    return d

  def mhstats_detailed(self):
    return self.mhstats

  def get_log_score(self, id):
    if id == -1:
      return self.p
    else:
      return self.observes[id].p

  def random_choices(self):
    return self.db.__len__()

  def assume(self, name, expr, id = -1):
    evalnode = ReducedEvalNode(self, self.env, expr)
    self.env.add_assume(name, evalnode)
    evalnode.add_assume(name, self.env)

    if id != -1:
      self.assumes[id] = evalnode
      assert id == len(self.directives)
      self.directives.append('assume')
    val = evalnode.evaluate()
    return val

  def predict(self, expr, id):
    evalnode = ReducedEvalNode(self, self.env, expr)

    assert id == len(self.directives)
    self.directives.append('predict')
    self.predicts[id] = evalnode

    evalnode.predict = True
    val = evalnode.evaluate()
    return val

  def observe(self, expr, obs_val, id):
    evalnode = ReducedEvalNode(self, self.env, expr)

    assert id == len(self.directives)
    self.directives.append('observe')
    self.observes[id] = evalnode

    evalnode.observed = True
    evalnode.observe_val = obs_val

    val = evalnode.evaluate()
    return val

  def forget(self, id):
    if id in self.observes:
      d = self.observes
    elif id in self.predicts:
      d = self.predicts
    else:
      raise RException("Can only forget predicts and observes")
    evalnode = d[id]
    evalnode.unevaluate()
    #del d[id]
    return

  def report_value(self, id):
    node = self.get_directive_node(id)
    if not node.active:
      raise RException("Error.  Perhaps this directive was forgotten?")
    val = node.val
    return val

  def get_directive_node(self, id):
    if self.directives[id] == 'assume':
      node = self.assumes[id]
    elif self.directives[id] == 'observe':
      node = self.observes[id]
    else:
      assert self.directives[id] == 'predict'
      node = self.predicts[id]
    return node

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
    old_to_new_q = - math.log(self.random_choices())
    new_val = reflip_node.reflip()
    new_to_old_q = - math.log(self.random_choices())

    old_to_new_q += self.eval_p
    new_to_old_q += self.uneval_p

    if debug:
      print "\n-----------------------------------------\n"
      print old_self
      print "\nCHANGING ", reflip_node, "\n  FROM  :  ", old_val, "\n  TO   :  ", new_val, "\n"
      if old_val == new_val:
        print "SAME VAL"
  
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
      new_val = reflip_node.reflip(old_val, True)

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
    else:
      if self.mhstats_details:
        if reflip_node.hashval in self.mhstats:
          self.mhstats[reflip_node.hashval]['accepted-proposals'] += 1
        else:
          self.mhstats[reflip_node.hashval] = {}
          self.mhstats[reflip_node.hashval]['accepted-proposals'] = 1
          self.mhstats[reflip_node.hashval]['made-proposals'] = 0
      self.accepted_proposals += 1
    if self.mhstats_details:
      if reflip_node.hashval in self.mhstats:
        self.mhstats[reflip_node.hashval]['made-proposals'] += 1
      else:
        self.mhstats[reflip_node.hashval] = {}
        self.mhstats[reflip_node.hashval]['made-proposals'] = 1
        self.mhstats[reflip_node.hashval]['accepted-proposals'] = 0
    self.made_proposals += 1
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
      raise RException("Program has no randomness!")
    self.reflip(evalnode)

  def reset(self):
    self.__init__()
    
  def __str__(self):
    string = "EvalNodeTree:"
    for evalnode in self.assumes.values():
      string += evalnode.str_helper()
    for evalnode in self.observes.values():
      string += evalnode.str_helper()
    for evalnode in self.predicts.values():
      string += evalnode.str_helper()
    return string
