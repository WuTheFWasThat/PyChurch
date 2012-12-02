from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict
from utils.rexceptions import RException

# The traces datastructure. 
# DAG of two interlinked trees: 
#   1. eval (with subcases: IF, symbollookup, combination, lambda) + apply
#   2. environments
# crosslinked by symbol lookup nodes and by the env argument to eval

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

class EvalNode:
  def __init__(self, traces, env, expression):
    self.traces = traces

    self.active = False # Whether this node is currently activated

    self.parent = None 
    self.children = {} 
    # TODO: get rid of this?
    self.applychildren = {} 
    self.applychild = None

    self.mem = False # Whether this is the root of a mem'd procedure's application
    self.mem_calls = {} # just a set

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

    self.expression = expression
    self.type = expression.type

    self.val = None

    self.hashval = rrandom.random.randbelow()
    return

  def get_child(self, addition, env, subexpr, is_apply = False):
    children = (self.applychildren if is_apply else self.children)

    if addition not in children:
      self.spawnchild(addition, env, subexpr, is_apply)
    evalnode = children[addition]
    evalnode.env = env
    return evalnode
  
  def spawnchild(self, addition, env, subexpr, is_apply = False):
    child = EvalNode(self.traces, env, subexpr)
    child.parent = self
    if is_apply:
      self.applychildren[addition] = child
    else:
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

  def setargs(self, args):
    if not self.type == 'apply':
      raise RException("Setting args in a non-apply expression")
    self.args = args

  def remove_xrp(self):
    if not self.active:
      raise RException("Removing XRP from inactive node")
    xrp = self.xrp
    args = self.args
    if xrp.is_mem_proc():
      xrp.remove_mem(self.val, args, self.traces, self)
    else:
      xrp.remove(self.val, args)
    prob = xrp.prob(self.val, self.args)
    if not self.observed:
      self.traces.uneval_p += prob
    self.traces.p -= prob
    if not xrp.deterministic:
      self.traces.remove_xrp(self)

  def add_xrp(self, xrp, val, args):
    prob = xrp.prob(val, args)
    self.p = prob
    if not self.observed:
      self.traces.eval_p += prob
    self.traces.p += prob
    if xrp.is_mem_proc():
      xrp.incorporate_mem(val, args, self.traces, self)
    else:
      xrp.incorporate(val, args)

    if not xrp.deterministic:
      self.random_xrp_apply = True
      self.traces.add_xrp(args, self)

  # restore_inactive:  whether to restore or to reflip inactive nodes that get activated
  def propagate_up(self, restore_inactive, start = False):
    # NOTE: 
    # assert self.active <--- almost true
    # This only breaks when this node is unevaluated from another branch of propagate_up
    # but this means children may have changed, so if we activate this branch and don't re-evaluate,
    # the result may be wrong!  We can't always re-evaluate the branches, because of the way reflip restores.
    # TODO: optimize to not re-propagate. needs to calculate explicit trace structure

    if self.random_xrp_apply:
      if not start:
        oldval = self.val
        val = self.evaluate(reflip = 0.5, xrp_force_val = self.val, restore = restore_inactive)
        if not val is oldval:
          raise RException("Failed to forced val")
        return val
      else:
        val = self.val
    else:
      val = self.evaluate(reflip = 0.5, xrp_force_val = None, restore = restore_inactive)

    if self.assume:
      if not self.parent is None:
        raise RException("Assume node should not have parent")
      # lookups can be affected *while* propagating up. 
      lookup_nodes = []
      for evalnode in self.env.get_lookups(self.assume_name, self):
        lookup_nodes.append(evalnode)
      for evalnode in lookup_nodes:
        evalnode.propagate_up(restore_inactive)
    elif self.parent is not None:
      self.parent.propagate_up(restore_inactive)

    if self.mem:
      # self.mem_calls can be affected *while* propagating up.  However, if new links are created, they'll use the new value
      for evalnode in self.mem_calls.keys():
        evalnode.propagate_up(restore_inactive)

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
        addition = ','.join([x.str_hash for x in self.args])
        if not addition in self.applychildren:
          raise RException("Addition not in applychildren")
        self.applychildren[addition].unevaluate()
      else:
        if not self.xrp_apply:
          raise RException("Apply is neither procedure nor xrp apply")
        self.remove_xrp()
    else:
      for x in self.children:
        self.children[x].unevaluate()

    self.active = False
    return

  def evaluate_recurse(self, subexpr, env, addition, reflip, is_apply = False):
    child = self.get_child(addition, env, subexpr, is_apply)
    val = child.evaluate(reflip == True, None)
    return val
  
  def binary_op_evaluate(self, reflip):
    val1 = self.evaluate_recurse(self.expression.children[0], self.env, 'operand0', reflip)
    val2 = self.evaluate_recurse(self.expression.children[1], self.env, 'operand1', reflip)
    return (val1 , val2)

  def children_evaluate(self, reflip):
    return [self.evaluate_recurse(self.expression.children[i], self.env, 'child' + str(i), reflip) for i in range(len(self.expression.children))]
  
  # reflip = 1 # reflip all
  #          0.5 # reflip current, but don't recurse
  #          0 # reflip nothing
  # restore - whether we are restoring, in MH 
  def evaluate(self, reflip = False, xrp_force_val = None, restore = False):
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
    elif self.type == 'if':
      cond = self.evaluate_recurse(expr.cond, self.env, 'cond', reflip)
      if cond.bool:
        false_child = self.get_child('false', self.env, expr.false)
        if false_child.active:
          false_child.unevaluate()
          if reflip == 0.5:
            reflip = not restore
          val = self.evaluate_recurse(expr.true, self.env, 'true', reflip)
        else:
          val = self.evaluate_recurse(expr.true, self.env, 'true', reflip)
      else:
        true_child = self.get_child('true', self.env, expr.true)
        if true_child.active:
          true_child.unevaluate()
          if reflip == 0.5:
            reflip = not restore
          val = self.evaluate_recurse(expr.false, self.env, 'false', reflip)
        else:
          val = self.evaluate_recurse(expr.false, self.env, 'false', reflip)
    #elif self.type == 'switch':
    #  index = self.evaluate_recurse(expr.index, self.env, 'index', reflip)
    #  if not 0 <= index.num < expr.n:
    #    raise RException("Invalid index for switch")
    #  for i in range(expr.n):
    #    if i != index.num:
    #      self.get_child('child' + str(i), self.env, expr.children[i]).unevaluate()
    #  val = self.evaluate_recurse(self.children[index.num] , self.env, 'child' + str(index.num), reflip)
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
      new_body = expr.body.replace(new_env, {}, self)
      # TODO :  should probably be an applychild
      # this doesnt work properly.  needs to be analagous to apply
      self.get_child('letbody', new_env, new_body).unevaluate()
      val = self.evaluate_recurse(new_body, new_env, 'letbody', reflip)

    elif self.type == 'apply':
      n = len(expr.children)
      args = [self.evaluate_recurse(expr.children[i], self.env, 'arg' + str(i), reflip) for i in range(n)]
      op = self.evaluate_recurse(expr.op, self.env, 'operator', reflip)

      if xrp_force_val is not None:
        if op.type != 'xrp':
          raise RException("Require outermost XRP application")

      if op.type == 'procedure':
        self.procedure_apply = True
        
        if n != len(op.vars):
          raise RException('Procedure should have %d arguments.  \nVars were \n%s\n, but had %d children.' % (n, op.vars, len(expr.children)))
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        addition = ','.join([x.str_hash for x in args])

        applychild = self.get_child(addition, new_env, op.body, True)

        if self.applychild is applychild:
          val = self.evaluate_recurse(op.body, new_env, addition, reflip, True)
        else:
          if self.applychild is not None:
            self.applychild.unevaluate()
          if reflip == 0.5:
            reflip = not restore
          val = self.evaluate_recurse(op.body, new_env, addition, reflip, True)
        self.applychild = applychild
      elif op.type == 'xrp':
        self.xrp_apply = True
        xrp = op.xrp

        if reflip == False and self.val is not None: # also inactive
          val = self.val
          self.add_xrp(self.xrp, self.val, self.args)
        elif xrp_force_val is not None:
          if reflip == True and not self.observed:
            raise RException("Forcing value that is not observe, and wants reflip")
          if xrp.deterministic:
            raise RException("Forced XRP application should not be deterministic")
            
          val = xrp_force_val
          if self.active:
            self.remove_xrp()
          self.add_xrp(xrp, val, args)

        elif xrp.deterministic or (not reflip):
          if self.active:
            if xrp.is_mem_proc():
              val = xrp.apply_mem(args, self.traces)
            elif self.args == args and self.xrp == xrp:
              val = self.val
              # TODO: deal with mem'd function changing..>
            else:
              self.remove_xrp()
              val = xrp.apply(args)
              self.add_xrp(xrp, val, args)
          else:
            if xrp.is_mem_proc():
              val = xrp.apply_mem(args, self.traces)
            else:
              val = xrp.apply(args)
            self.add_xrp(xrp, val, args)
        else: # not deterministic, needs reflipping
          if self.active:
            self.remove_xrp()
          val = xrp.apply(args)
          self.add_xrp(xrp, val, args)

        self.xrp = xrp
        if val is None:
          raise RException("Value is not set")
      else:
        raise RException('Must apply either a procedure or xrp.  Instead got expression %s' % str(op))

      self.args = args
    elif self.type == 'function':
      n = len(expr.vars)
      new_env = self.env.spawn_child()
      bound = {}
      for i in range(n): # Bind variables
        bound[expr.vars[i]] = True
      procedure_body = expr.body.replace(new_env, bound, self)
      val = Procedure(expr.vars, procedure_body, self.env)
    elif self.type == '=':
      (val1, val2) = self.binary_op_evaluate(reflip)
      val = val1.__eq__(val2)
    elif self.type == '<':
      (val1, val2) = self.binary_op_evaluate(reflip)
      val = val1.__lt__(val2)
    elif self.type == '>':
      (val1, val2) = self.binary_op_evaluate(reflip)
      val = val1.__gt__(val2)
    elif self.type == '<=':
      (val1, val2) = self.binary_op_evaluate(reflip)
      val = val1.__le__(val2)
    elif self.type == '>=':
      (val1, val2) = self.binary_op_evaluate(reflip)
      val = val1.__ge__(val2)
    elif self.type == '&':
      vals = self.children_evaluate(reflip)
      andval = BoolValue(True)
      for x in vals:
        andval = andval.__and__(x)
      val = andval
    elif self.type == '^':
      vals = self.children_evaluate(reflip)
      xorval = BoolValue(True)
      for x in vals:
        xorval = xorval.__xor__(x)
      val = xorval
    elif self.type == '|':
      vals = self.children_evaluate(reflip)
      orval = BoolValue(False)
      for x in vals:
        orval = orval.__or__(x)
      val = orval
    elif self.type == '~':
      negval = self.evaluate_recurse(expr.children[0] , self.env, 'neg', reflip)
      val = negval.__inv__()
    elif self.type == '+':
      vals = self.children_evaluate(reflip)
      sum_val = NatValue(0)
      for x in vals:
        sum_val = sum_val.__add__(x)
      val = sum_val
    elif self.type == '-':
      val1 = self.evaluate_recurse(expr.children[0] , self.env, 'sub0', reflip)
      val2 = self.evaluate_recurse(expr.children[1] , self.env, 'sub1', reflip)
      val = val1.__sub__(val2)
    elif self.type == '*':
      vals = self.children_evaluate(reflip)
      prod_val = NatValue(1)
      for x in vals:
        prod_val = prod_val.__mul__(x)
      val = prod_val
    elif self.type == '/':
      val1 = self.evaluate_recurse(expr.children[0] , self.env, 'div0', reflip)
      val2 = self.evaluate_recurse(expr.children[1] , self.env, 'div1', reflip)
      val = val1.__div__(val2)
    elif self.type == '%':
      val1 = self.evaluate_recurse(expr.children[0] , self.env, 'val', reflip)
      val2 = self.evaluate_recurse(expr.children[1] , self.env, 'modulus', reflip)
      val = val1.__mod__(val2)
    else:
      raise RException('Invalid expression type %s' % self.type)

    self.val = val
    self.active = True

    if self.assume:
      if self.parent is not None:
        raise RException("Assume should not have a parent")
      self.env.set(self.assume_name, val) # Environment in which this was evaluated

    return val

  def reflip(self, force_val = None, restore_inactive = False):
    #if use_jit:
    #  jitdriver.jit_merge_point(node=self.val)
    self.evaluate(reflip = 0.5, xrp_force_val = force_val, restore = restore_inactive)
    if not self.random_xrp_apply:
      raise RException("Reflipping something that isn't a random xrp apply")
    self.propagate_up(restore_inactive, True)
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
        string += self.children[key].str_helper(n + 2)
      for key in self.applychildren:
        string += self.applychildren[key].str_helper(n + 2)
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

    self.env = EnvironmentNode()

    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0

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

  def random_choices(self):
    return self.db.__len__()

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

  def reflip(self, reflip_node):
    debug = False

    if debug:
      old_self = self.__str__()

    if not reflip_node.random_xrp_apply:
      raise RException("Reflipping something which isn't a random xrp application")
    if reflip_node.val is None:
      raise RException("Reflipping something which previously had value None")
    
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
    if self.db.__contains__(evalnodecheck):
      raise RException("DB already had this evalnode")
    self.db.__setitem__(evalnodecheck, True)

  def remove_xrp(self, evalnode):
    if not self.db.__contains__(evalnode):
      raise RException("DB did not already have this evalnode")
    self.db.__delitem__(evalnode)

  def infer(self):
    try:
      evalnode = self.db.randomKey()
    except:
      # No coin flips!
      return
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
