from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict, WeightedRandomChoiceDict
from utils.rexceptions import RException

# The traces datastructure. 
# DAG of two interlinked trees: 
#   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
#   2. environments
# crosslinked by symbol lookup nodes and by the env argument to eval

try:
  from rpython.rlib.jit import JitDriver
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
    self.lookups = {} # for each name, a set
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
      new_evalnode.propagate_up(restore_inactive)

  def spawn_child(self): 
    return EnvironmentNode(self)

def list_nodes(nodes):
  nodes_list = []
  for node in nodes:
    nodes_list.append(node)
  return nodes_list

class EvalNode(Node):
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.active = False # Whether this node is currently activated

    self.out_link = None # An XRP which is a "link" to the outside

    self.parent = None 
    self.children = {} 
    self.applychild = None

    self.env = env # Environment in which this was evaluated
    self.lookup = None 
    self.assume = False
    self.assume_name = None

    self.observed = False
    self.observe_val = None 

    self.xrp = XRP()
    self.xrp_apply = False
    self.random_xrp_apply = False
    self.procedure_apply = False
    self.args = None
    self.p = 0
    self.forcing = False

    self.expression = expression
    self.type = expression.type

    self.val = None

    self.hashval = rrandom.random.randbelow()
    return

  def get_child(self, addition, env, subexpr):
    if addition not in self.children:
      self.spawnchild(addition, env, subexpr)
    evalnode = self.children[addition]
    evalnode.env = env
    return evalnode
  
  def spawnchild(self, addition, env, subexpr):
    child = EvalNode(self.traces, env, subexpr)
    child.parent = self
    self.children[addition] = child

  def add_assume(self, name, env):
    if not env is self.env:
      raise RException("Adding to wrong environment")
    self.assume_name = name
    self.assume = True

  def setlookup(self, env):
    if not self.expression.type == 'variable':
      raise RException("Setting lookup in a non-variable expression")
    self.lookup = env 
    env.add_lookup(self.expression.name, self)

  def remlookup(self, name, env):
    self.lookup = None
    env.rem_lookup(name, self)

  def setargs(self, xrp, args, p):
    if not self.type == 'apply':
      raise RException("Setting args in a non-apply expression")
    self.xrp = xrp
    self.args = args
    self.p = p

  def remove_xrp(self):
    if not self.active:
      raise RException("Removing XRP from inactive node")
    self.traces.remove_xrp(self.xrp, self.args, self.val, self)

  def add_xrp(self, xrp, val, args, forcing = False):
    self.traces.add_xrp(xrp, args, val, self, forcing)

  def delete_children(self):
    # TODO: NOT ACTUALLY SAFE, because of multiple propagation
    for addition in self.children.keys():
      if not self.children[addition].active:
        del self.children[addition]

  # restore_inactive:  whether to restore or to reflip inactive nodes that get activated
  def propagate_up(self, restore_inactive, start = False):
    # NOTE: 
    # assert self.active <--- almost true
    # This only breaks when this node is unevaluated from another branch of propagate_up
    # but this means children may have changed, so if we activate this branch and don't re-evaluate,
    # the result may be wrong!  We can't always re-evaluate the branches, because of the way reflip restores.
    # TODO: optimize to not re-propagate. needs to calculate explicit trace structure, or use some heap structure?

    if self.random_xrp_apply:
      if not start:
        oldval = self.val
        val = self.evaluate(reflip = 0.5, xrp_force_val = self.val)
        if not val is oldval:
          raise RException("Failed to forced val")
        return val
      else:
        val = self.val
    else:
      val = self.evaluate(reflip = 0.5, xrp_force_val = None)
      if restore_inactive:
        self.delete_children()

    if self.assume:
      if not self.parent is None:
        raise RException("Assume node should not have parent")
      # lookups can be affected *while* propagating up. 
      self.env.propagate_link(self, val, restore_inactive)
    elif self.parent is not None:
      self.parent.propagate_up(restore_inactive)

    if self.out_link is not None:
      self.out_link.propagate_link(self, val, restore_inactive)

    self.val = val
    return self.val

  def unevaluate(self):
    # NOTE:  We may want to remove references to nodes when we unevaluate, such as when we have arguments
    # drawn from some continuous domain
    if not self.active:
      return
    expr = self.expression
    if self.type == 'variable':
      # Don't remove reference value.
      if not self.lookup:
        raise RException("Variable wasn't looked up")
      self.remlookup(expr.name, self.lookup)
    elif self.type == 'apply':
      n = len(expr.children)
      for i in range(n):
        self.get_child('arg' + str(i), self.env, expr.children[i]).unevaluate()
      self.get_child('operator', self.env, expr.op).unevaluate()
      if self.procedure_apply: 
        addition = ','.join(['apply'] + [x.str_hash for x in self.args])
        if not addition in self.children:
          raise RException("Addition not in children")
        self.children[addition].unevaluate()
      else:
        if not self.xrp_apply:
          raise RException("Apply is neither procedure nor xrp apply")
        self.remove_xrp()
    else:
      for x in self.children:
        self.children[x].unevaluate()

    self.active = False
    return

  def evaluate_recurse(self, subexpr, env, addition, reflip, force_val = None):
    child = self.get_child(addition, env, subexpr)
    val = child.evaluate(reflip == True, force_val)
    return val
  
  # reflip = 1 # reflip all
  #          0.5 # reflip current, but don't recurse
  #          0 # reflip nothing (unless inactive)
  # restore - whether we are restoring, in MH 
  def evaluate(self, reflip = False, xrp_force_val = None):
    if reflip == False and self.active:
      if self.val is None:
        raise RException("Active node has no value")
      return self.val

    expr = self.expression

    if self.observed:
      xrp_force_val = self.observe_val

    if xrp_force_val is not None:
      if self.type != 'apply':
        raise RException("Require outermost XRP application")

    if self.type == 'value':
      val = expr.val
    elif self.type == 'variable':
      (val, lookup_env) = self.env.lookup(expr.name)
      self.setlookup(lookup_env)
    # TODO: get rid of this and do properly
    elif self.type == 'if':
      cond = self.evaluate_recurse(expr.cond, self.env, 'cond', reflip)
      if cond.bool:
        false_child = self.get_child('false', self.env, expr.false)
        if false_child.active:
          false_child.unevaluate()
          val = self.evaluate_recurse(expr.true, self.env, 'true', reflip)
        else:
          val = self.evaluate_recurse(expr.true, self.env, 'true', reflip)
      else:
        true_child = self.get_child('true', self.env, expr.true)
        if true_child.active:
          true_child.unevaluate()
          val = self.evaluate_recurse(expr.false, self.env, 'false', reflip)
        else:
          val = self.evaluate_recurse(expr.false, self.env, 'false', reflip)
    elif self.type == 'let':
      # TODO: this really is a let*
      # Does environment stuff work properly?
      n = len(expr.vars)
      if not len(expr.expressions) == n:
        raise RException("Let has non-matching number of variables and expressions")
      values = []
      new_env = self.env
      for i in range(n): # Bind variables
        new_env = new_env.spawn_child()
        val = self.evaluate_recurse(expr.expressions[i], new_env, 'let' + str(i), reflip)
        values.append(val)
        new_env.set(expr.vars[i], values[i])
        if val.type == 'procedure':
          val.env = new_env
      new_body = expr.body
      self.get_child('letbody', new_env, new_body).unevaluate()
      val = self.evaluate_recurse(new_body, new_env, 'letbody', reflip)

    elif self.type == 'apply':
      n = len(expr.children)
      args = [self.evaluate_recurse(expr.children[i], self.env, 'arg' + str(i), reflip) for i in range(n)]
      op = self.evaluate_recurse(expr.op, self.env, 'operator', reflip)

      if op.type == 'procedure':
        self.procedure_apply = True
        
        if n != len(op.vars):
          raise RException('Procedure should have %d arguments.  \nVars were \n%s\n, but had %d children.' % (n, op.vars, len(expr.children)))
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        addition = ','.join(['apply'] + [x.str_hash for x in args])

        applychild = self.get_child(addition, new_env, op.body)

        if self.applychild is applychild:
          val = self.evaluate_recurse(op.body, new_env, addition, reflip, xrp_force_val)
        else:
          if self.applychild is not None:
            self.applychild.unevaluate()
          val = self.evaluate_recurse(op.body, new_env, addition, reflip, xrp_force_val)
        self.applychild = applychild
        self.applyaddition = addition
      elif op.type == 'xrp':
        self.xrp_apply = True
        xrp = op.xrp

        if reflip == False and self.val is not None: # also inactive.  (reactivated branch?)
          val = self.val
          self.add_xrp(self.xrp, self.val, self.args)
        elif xrp_force_val is not None:
          if reflip == True and not self.observed:
            raise RException("Forcing value that is not observe, and wants reflip")
          if xrp.resample:
            raise RException("Forced XRP application should be re-scorable")
            
          val = xrp_force_val
          if self.active:
            self.remove_xrp()
          self.add_xrp(xrp, val, args, True)

        elif xrp.resample or (not reflip):
          if self.active:
            if self.args == args and self.xrp == xrp:
              val = self.val
            else:
              self.remove_xrp()
              val = xrp.sample(args)
              self.add_xrp(xrp, val, args)
          else:
            val = xrp.sample(args)
            self.add_xrp(xrp, val, args)
        else: # not resampling, but needs reflipping
          if self.active:
            self.remove_xrp()
          val = xrp.sample(args)
          self.add_xrp(xrp, val, args)

        if val is None:
          raise RException("Value is not set")
      else:
        raise RException('Must apply either a procedure or xrp.  Instead got expression %s' % str(op))

      self.args = args
    elif self.type == 'function':
      n = len(expr.vars)
      val = Procedure(expr.vars, expr.body, self.env)
    else:
      raise RException('Invalid expression type %s' % self.type)

    self.active = True
    self.set_val(val)

    return val

  def restore(self, force_val):
    #if use_jit:
    #  jitdriver.jit_merge_point(node=self.val)

    if not self.active:
      raise RException("Reflipping something that isn't active")

    if self.traces.application_reflip:
      if not (self.type == 'apply' and self.xrp_apply and self.random_xrp_apply):
        raise RException("Reflipping something that isn't a random xrp apply")
      self.remove_xrp()
      self.add_xrp(self.xrp, force_val, self.args)
    self.set_val(force_val)
    self.propagate_up(True, True)
    return self.val

  def reflip(self):
    #if use_jit:
    #  jitdriver.jit_merge_point(node=self.val)

    if not (self.type == 'apply' and self.xrp_apply and self.random_xrp_apply):
      raise RException("Reflipping something that isn't a random xrp apply")
    if not self.active:
      raise RException("Reflipping something that isn't active")

    if self.observed:
      return self.val

    self.traces.remove_xrp(self.xrp, self.args, self.val, self)

    # TODO re-add something like this
    # (val, p_uneval, p_eval) = self.xrp.mh_prop(self.val, self.args)

    val = self.xrp.sample(self.args)

    self.traces.add_xrp(self.xrp, self.args, val, self)

    self.set_val(val)

    self.propagate_up(False, True)
    return self.val

  def set_val(self, val):
    self.val = val 

    if self.assume:
      if self.parent is not None:
        raise RException("Assume should not have a parent")
      self.env.set(self.assume_name, val) # Environment in which this was evaluated

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
        string += self.children[key].str_helper(n + 2)
    return string

  def __str__(self):
    if self.assume_name is None:
      return ("EvalNode of type %s, with expression %s and value %s" % (self.type, str(self.expression), str(self.val)))
    else:
      return ("EvalNode %s" % (self.assume_name))

class Traces(Engine):
  def __init__(self):
    self.engine_type = 'traces'

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
    self.old_to_new_q = 0
    self.new_to_old_q = 0

    self.eval_xrps = [] # (xrp, args, val)
    self.uneval_xrps = [] # (xrp, args, val)

    self.debug = False

    # Stuff for restoring
    self.application_reflip = False
    self.reflip_node = EvalNode(self, self.env, VarExpression(''))
    self.nodes = []
    self.old_vals = []
    self.new_vals = []
    self.old_val = Value() 
    self.new_val = Value() 
    self.reflip_xrp = XRP()

    self.made_proposals = 0
    self.accepted_proposals = 0

    self.mhstats_details = False
    self.mhstats = {}
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

  def assume(self, name, expr, id):
    evalnode = EvalNode(self, self.env, expr)

    if id != -1:
      self.assumes[id] = evalnode
      if id != len(self.directives):
        raise RException("Id %d does not agree with directives length of %d" % (id, len(self.directives)))
      self.directives.append('assume')

    val = evalnode.evaluate()
    self.env.add_assume(name, evalnode)
    evalnode.add_assume(name, self.env)
    self.env.set(name, val)
    return val

  def predict(self, expr, id):
    evalnode = EvalNode(self, self.env, expr)

    if id != len(self.directives):
      raise RException("Id %d does not agree with directives length of %d" % (id, len(self.directives)))
    self.directives.append('predict')
    self.predicts[id] = evalnode
    val = evalnode.evaluate(False)
    return val

  def observe(self, expr, obs_val, id):
    evalnode = EvalNode(self, self.env, expr)

    if id != len(self.directives):
      raise RException("Id %d does not agree with directives length of %d" % (id, len(self.directives)))
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
    elif self.directives[id] == 'predict':
      node = self.predicts[id]
    else:
      raise RException("Invalid directive")
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
    
    self.old_to_new_q = 0
    self.new_to_old_q = 0

    old_p = self.p

    self.old_to_new_q = - math.log(self.weight())

    if self.application_reflip:
      self.old_val = self.reflip_node.val
      self.new_val = self.reflip_node.reflip()
    else:
      args_list = []
      self.old_vals = []
      for node in self.nodes:
        if not node.xrp_apply:
          raise RException("non-XRP application node being used in transition")
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
        node.propagate_up(False, True)

    new_p = self.p
    self.new_to_old_q -= math.log(self.weight())

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

    return old_p, self.old_to_new_q, new_p, self.new_to_old_q

  def restore(self):
    if self.application_reflip:
      self.reflip_node.restore(self.old_val)
    else:
      for i in range(len(self.nodes)):
        node = self.nodes[i]
        node.set_val(self.old_vals[i])
        node.propagate_up(True, True)
      self.reflip_xrp.theta_mh_restore()
    if self.debug: 
      print 'restore'
      print "\n-----------------------------------------\n"

  def keep(self):
    if self.application_reflip:
      self.reflip_node.restore(self.new_val) # NOTE: Is necessary for correctness, as we must forget old branch
    else:
      for i in range(len(self.nodes)):
        node = self.nodes[i]
        node.restore(self.new_vals[i]) 
      self.reflip_xrp.theta_mh_keep()
    if self.debug: 
      print 'keep'
      print "\n-----------------------------------------\n"

  def add_for_transition(self, xrp, evalnode):
    hashval = xrp.__hash__()
    if hashval not in self.xrps:
      self.xrps[hashval] = (xrp, {})
    (xrp, evalnodes) = self.xrps[hashval]
    evalnodes[evalnode] = True

    weight = xrp.state_weight()
    self.delete_from_db(hashval)
    self.add_to_db(hashval, weight)

  # Add an XRP application node to the db
  def add_xrp(self, xrp, args, val, evalnode, forcing = False):
    self.eval_xrps.append((xrp, args, val))

    evalnode.forcing = forcing
    if not xrp.resample:
      evalnode.random_xrp_apply = True
    prob = xrp.prob(val, args)
    evalnode.setargs(xrp, args, prob)
    xrp.incorporate(val, args)
    xrp.make_link(evalnode, args)
    if not forcing:
      self.old_to_new_q += prob
    self.p += prob
    self.add_for_transition(xrp, evalnode)
    if xrp.resample:
      return

    weight = xrp.weight(args)
    try:
      self.new_to_old_q += math.log(weight)
    except:
      pass # This is only necessary if we're reflipping

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
      self.delete_from_db(hashval)

  def remove_xrp(self, xrp, args, val, evalnode):
    self.uneval_xrps.append((xrp, args, val))

    xrp.break_link(evalnode, args)
    xrp.remove(val, args)
    prob = xrp.prob(val, args)
    if not evalnode.forcing:
      self.new_to_old_q += prob
    self.p -= prob 
    self.remove_for_transition(xrp, evalnode)
    if xrp.resample:
      return

    xrp = evalnode.xrp
    try: # TODO: dont do this here.. dont do cancellign
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
    if new_p + self.new_to_old_q - old_p - self.old_to_new_q < math.log(p):
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
