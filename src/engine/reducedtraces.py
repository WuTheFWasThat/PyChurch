from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict, WeightedRandomChoiceDict
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


  def propagate_link(self, evalnode, val, restore_inactive):
    if self.assumes[evalnode.assume_name] is not evalnode:
      raise RException("Wrong evalnode getting lookups for %s" % evalnode.assume_name)
    evalnode.val = val 
    lookup_nodes = list_nodes(self.get_lookups(evalnode.assume_name, evalnode))
    for new_evalnode in lookup_nodes:
      evalnode.propagate_to(new_evalnode, restore_inactive)

  def spawn_child(self): 
    return EnvironmentNode(self)

def list_nodes(nodes):
  nodes_list = []
  for node in nodes:
    nodes_list.append(node)
  return nodes_list

class ReducedEvalNode(Node):
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.parent = None 

    self.env = env # Environment in which this was evaluated

    self.assume = False
    self.assume_name = None
    self.predict = False

    self.observed = False
    self.observe_val = None 

    self.out_link = None

    self.expression = expression
    self.type = expression.type

    self.hashval = rrandom.random.randbelow()
    self.reset()
    return

  # Reset things that have to do with current run, but not with program
  def reset(self):
    self.active = False # Whether this node is currently activated

    # Relative path (hash) -> evalnode
    self.children = {}  
    self.active_children = {}  

    # Bookkeeping for all references made.  Necessary since they are deleted sometimes, so we should stop propagating to this node from that variable.
    self.lookups = {}  

    # List of (xrp, args).  Bookkeeping for all un-forcing XRPs.  Necessary to keep track, so we can remove their old applications
    self.xrp_applies = []  

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
      self.env.propagate_link(self, self.val, restore_inactive)
    elif self.parent is not None:
      self.propagate_to(self.parent, restore_inactive)

    if self.out_link is not None:
      self.out_link.propagate_link(self, self.val, restore_inactive)


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
      assert self.assume or self.predict

    self.active = False
    return

  def remove_xrp(self, xrp, val, args, forcing = False):
    xrp.break_link(self)
    xrp.remove(val, args)
    prob = xrp.prob(val, args)
    if not forcing:
      self.traces.uneval_p += prob
    self.traces.p -= prob

  def add_xrp(self, xrp, val, args, forcing = False):
    prob = xrp.prob(val, args)
    if not forcing:
      self.traces.eval_p += prob
    self.traces.p += prob
    self.p = prob
    xrp.incorporate(val, args)
    xrp.make_link(self)

  # reflips own XRP, possibly with a forced value
  def apply_random_xrp(self, xrp, args, xrp_force_val = None):
    assert self.random_xrp_apply
    if self.active:
      self.remove_xrp(self.xrp, self.val, self.args, xrp_force_val is not None)
      self.traces.remove_xrp(self)

    self.xrp = xrp
    self.args = args

    if xrp_force_val is None:
      val = self.xrp.sample(self.args)
    else:
      val = xrp_force_val
    self.add_xrp(self.xrp, val, self.args, xrp_force_val is not None)
    self.traces.add_xrp(self.xrp, self.args, self)
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

    # TODO: use directive ids... 
    val = self.evaluate_recurse(expr, env, 0, 0, xrp_force_val, restore)

    if not self.random_xrp_apply:
      if xrp_force_val is not None:
        raise RException("Can only force re-scoring XRP applications")
      assert self.assume  or self.predict

    self.set_val(val)
    self.active = True

    for addition in old_active_children:
      if addition not in self.active_children:
        evalnode = self.children[addition]
        evalnode.unevaluate()

    return val

  def evaluate_recurse(self, expr, env, hashval, addition, xrp_force_val = None, restore = False):
    hashval = rhash.hash_pair(hashval, addition)

    if expr.type == 'value':
      val = expr.val
    elif expr.type == 'variable':
      (val, lookup_env) = env.lookup(expr.name)
      self.addlookup(expr.name, lookup_env)
    # TODO: get rid of.  Works with proper if, but not in traces
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
      val = self.evaluate_recurse(expr.body, new_env, hashval, 1, None, restore)

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
        if not xrp.resample:
          if hashval == 0:
            self.random_xrp_apply = True
            val = self.apply_random_xrp(xrp, args, xrp_force_val)
          else:
            child = self.get_child(hashval, env, expr, restore)
            val = child.val
        else:
          val = xrp.sample(args)
          self.add_xrp(xrp, val, args)
          self.xrp_applies.append((xrp, val, args))
        assert val is not None
      else:
        raise RException('Must apply either a procedure or xrp.  Instead got expression %s' % str(op))

    elif expr.type == 'function':
      n = len(expr.vars)
      new_env = env.spawn_child()
      val = Procedure(expr.vars, expr.body, env)
    else:
      raise RException('Invalid expression type %s' % expr.type)

    return val

  def set_val(self, val):
    self.val = val
    if self.assume:
      assert self.parent is None
      self.env.set(self.assume_name, self.val) # Environment in which this was evaluated

  def restore(self, val):
    assert self.active
    assert self.random_xrp_apply
    self.remove_xrp(self.xrp, self.val, self.args, True)
    self.traces.remove_xrp(self)
    self.add_xrp(self.xrp, val, self.args, True)
    self.traces.add_xrp(self.xrp, self.args, self)
    self.set_val(val)
    self.propagate_up(True)
    return self.val

  def reflip(self):
    assert self.active
    assert self.random_xrp_apply

    self.traces.remove_xrp(self)

    (val, p_uneval, p_eval) = self.xrp.mh_prop(self.val, self.args)

    self.traces.add_xrp(self.xrp, self.args, self)
    
    self.traces.uneval_p += p_uneval
    self.traces.p -= p_uneval
    self.traces.eval_p += p_eval
    self.traces.p += p_eval
    self.p = p_eval

    self.set_val(val)

    self.propagate_up(False)
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
    self.weighted_db = WeightedRandomChoiceDict() 
    self.choices = {} # hash -> evalnode
    self.xrps = {} # hash -> (xrp, set of application nodes)

    self.env = EnvironmentNode()

    self.p = 0
    self.uneval_p = 0
    self.eval_p = 0
    self.new_to_old_q = 0
    self.old_to_new_q = 0

    self.debug = False

    # necessary because of the new XRP interface requiring some state kept while doing inference
    self.application_reflip = False
    self.reflip_node = ReducedEvalNode(self, self.env, VarExpression(''))
    self.nodes = []
    self.old_vals = [Value()]
    self.new_vals = [Value()]
    self.old_val = Value() 
    self.new_val = Value() 
    self.reflip_xrp = XRP()

    self.mhstats_details = False
    self.mhstats = {}
    self.made_proposals = 0
    self.accepted_proposals = 0

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

  def weight(self):
    return self.db.weight() + self.weighted_db.weight()

  def random_choices(self):
    return self.db.__len__() + self.weighted_db.__len__()

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

  def add_accepted_proposal(self, hashval):
    if self.mhstats_details:
      if hashval in self.mhstats:
        self.mhstats[hashval]['accepted-proposals'] += 1
      else:
        self.mhstats[hashval] = {}
        self.mhstats[hashval]['accepted-proposals'] = 1
        self.mhstats[hashval]['made-proposals'] = 0
    self.accepted_proposals += 1

  def add_made_proposal(self, hashval):
    if self.mhstats_details:
      if hashval in self.mhstats:
        self.mhstats[hashval]['made-proposals'] += 1
      else:
        self.mhstats[hashval] = {}
        self.mhstats[hashval]['made-proposals'] = 1
        self.mhstats[hashval]['accepted-proposals'] = 0
    self.made_proposals += 1

  def reflip(self, hashval):
    if self.debug:
      print self

    if hashval in self.choices:
      self.application_reflip = True
      self.reflip_node = self.choices[hashval]
      if not self.reflip_node.random_xrp_apply:
        raise RException("Reflipping something which isn't a random xrp application")
      if self.reflip_node.val is None:
        raise RException("Reflipping something which previously had value None")
    else:
      self.application_reflip = False # internal reflip
      (self.reflip_xrp, nodes) = self.xrps[hashval]
      self.nodes = list_nodes(nodes)

    self.eval_p = 0
    self.uneval_p = 0

    old_p = self.p
    self.old_to_new_q = - math.log(self.weight())

    if self.application_reflip:
      self.old_val = self.reflip_node.val
      self.new_val = self.reflip_node.reflip()
    else:
      # TODO: this is copied from traces.  is it correct?
      args_list = []
      self.old_vals = []
      for node in self.nodes:
        args_list.append(node.args)
        self.old_vals.append(node.val)
      self.old_to_new_q += math.log(self.reflip_xrp.state_weight())
      old_p += self.reflip_xrp.theta_prob()
  
      self.new_vals, q_forwards, q_back = self.reflip_xrp.theta_mh_prop(args_list, self.old_vals)
      self.old_to_new_q += q_forwards
      self.new_to_old_q += q_back
  
      for i in range(len(self.nodes)):
        node = self.nodes[i]
        val = self.new_vals[i]
        node.set_val(val)
        node.propagate_up(False)

    new_p = self.p
    self.new_to_old_q = - math.log(self.weight())
    self.old_to_new_q += self.eval_p
    self.new_to_old_q += self.uneval_p

    if not self.application_reflip:
      new_p += self.reflip_xrp.theta_prob()
      self.new_to_old_q += math.log(self.reflip_xrp.state_weight())

    if self.debug:
      if self.application_reflip:
        print "\nCHANGING VAL OF ", self.reflip_node, "\n  FROM  :  ", self.old_val, "\n  TO   :  ", self.new_val, "\n"
        if (self.old_val.__eq__(self.new_val)).bool:
          print "SAME VAL"
      else:
        print "TRANSITIONING STATE OF ", self.reflip_xrp
  
      print "new db", self
      print "\nq(old -> new) : ", math.exp(self.old_to_new_q)
      print "q(new -> old) : ", math.exp(self.new_to_old_q )
      print "p(old) : ", math.exp(old_p)
      print "p(new) : ", math.exp(new_p)
      print 'transition prob : ',  math.exp(new_p + self.new_to_old_q - old_p - self.old_to_new_q) , "\n"
      print "\n-----------------------------------------\n"

    return old_p, self.old_to_new_q, new_p, self.new_to_old_q

  def restore(self):
    if self.application_reflip:
      self.reflip_node.restore(self.old_val)
    else:
      for i in range(len(self.nodes)):
        node = self.nodes[i]
        node.set_val(self.old_vals[i])
        node.propagate_up(True)
      self.reflip_xrp.theta_mh_restore()
    if self.debug:
      print 'restore'

  def keep(self):
    if self.application_reflip:
      self.reflip_node.restore(self.new_val) # NOTE: Is necessary for correctness, as we must forget old branch
    else:
      for i in range(len(self.nodes)):
        node = self.nodes[i]
        node.restore(self.new_vals[i])
      self.reflip_xrp.theta_mh_keep()

  def add_for_transition(self, xrp, evalnode):
    hashval = xrp.__hash__()
    if hashval not in self.xrps:
      self.xrps[hashval] = (xrp, {})
    (xrp, evalnodes) = self.xrps[hashval]
    evalnodes[evalnode] = True

    weight = xrp.state_weight()
    self.delete_from_db(xrp.__hash__())
    self.add_to_db(xrp.__hash__(), weight)

  # Add an XRP application node to the db
  def add_xrp(self, xrp, args, evalnode):
    weight = xrp.weight(args)
    evalnode.setargs(args)
    try:
      self.new_to_old_q += math.log(weight)
    except:
      pass # This is only necessary if we're reflipping
    self.add_for_transition(xrp, evalnode)

    if self.weighted_db.__contains__(evalnode.hashval) or self.db.__contains__(evalnode.hashval) or (evalnode.hashval in self.choices):
      raise RException("DB already had this evalnode")
    self.choices[evalnode.hashval] = evalnode
    self.add_to_db(evalnode.hashval, weight)

  def add_to_db(self, hashval, weight):
    if weight == 0:
      return
    elif weight == 1:
      self.db.__setitem__(hashval, True)
    else:
      self.weighted_db.__setitem__(hashval, True, weight)


  def remove_for_transition(self, xrp, evalnode):
    hashval = xrp.__hash__()
    (xrp, evalnodes) = self.xrps[hashval]
    del evalnodes[evalnode]
    if len(evalnodes) == 0:
      del self.xrps[hashval]
      self.delete_from_db(xrp.__hash__())

  def remove_xrp(self, evalnode):
    xrp = evalnode.xrp
    self.remove_for_transition(xrp, evalnode)
    try:
      self.old_to_new_q += math.log(xrp.weight(evalnode.args))
    except:
      pass # This fails when restoring/keeping, for example

    if evalnode.hashval not in self.choices:
      raise RException("Choices did not already have this evalnode")
    else:
      del self.choices[evalnode.hashval]
      self.delete_from_db(evalnode.hashval)

  def delete_from_db(self, hashval):
    if self.db.__contains__(hashval):
      self.db.__delitem__(hashval)
    elif self.weighted_db.__contains__(hashval):
      self.weighted_db.__delitem__(hashval)

  def randomKey(self):
    if rrandom.random.random() * self.weight() > self.db.weight():
      return self.weighted_db.randomKey()
    else:
      return self.db.randomKey()

  def infer(self):
    try:
      hashval = self.randomKey()
    except:
      raise RException("Program has no randomness!")

    old_p, old_to_new_q, new_p, new_to_old_q = self.reflip(hashval)
    p = rrandom.random.random()
    if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
      self.restore()
    else:
      self.keep()
      self.add_accepted_proposal(hashval)
    self.add_made_proposal(hashval)

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

