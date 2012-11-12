from engine import *
from expressions import *
from environment import *
from utils.random_choice_dict import RandomChoiceDict

# TODO:  Use rolling hash for stack

# Class representing random db
class RandomDB(Engine):
  def __init__(self, env):
    #self.db = {} 
    self.db = RandomChoiceDict() 
    self.db_noise = {}
    self.log = []
    # ALWAYS WORKING WITH LOG PROBABILITIES
    self.uneval_p = 0
    self.eval_p = 0
    self.p = 0 

    env.reset()
    self.env = env

    self.assumes = []
    self.observes = {}
    self.vars = {}

  def reset(self):
    self.__init__()

  def assume(self, varname, expr): 
    self.assumes.append((varname, expr))
    self.vars[varname] = expr
    value = self.evaluate(expr, self.env, reflip = True, stack = [varname])
    self.env.set(varname, value)
    return value

  def observe(self, expr, obs_val, id):
    if expr.hashval in self.observes:
      raise Exception('Already observed %s' % str(expr))
    self.observes[id] = (expr, obs_val) 
    # bit of a hack, here, to make it recognize same things as with noisy_expr
    self.evaluate(expr, self.env, reflip = False, stack = ['obs', id], xrp_force_val = obs_val)
    return expr.hashval

  def rerun(self):
    for (varname, expr) in self.assumes:
      value = self.evaluate(expr, self.env, reflip = True, stack = [varname])
      self.env.set(varname, value)
    for id in self.observes:
      (expr, obs_val) = self.observes[id]
      self.evaluate(expr, self.env, reflip = True, stack = ['obs', id], xrp_force_val = obs_val)

  def forget(self, id):
    self.remove(['obs', id])
    assert id in self.observes
    del self.observes[id]
    return

  def insert(self, stack, xrp, value, args, is_obs_noise = False, memorize = True):
    stack = tuple(stack)
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
      self.eval_p += prob # hmmm.. 
    if memorize:
      self.log.append(('insert', stack, xrp, value, args, is_obs_noise))

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
      self.uneval_p += prob # previously unindented...
    if memorize:
      self.log.append(('remove', stack, xrp, value, args, is_obs_noise))

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
      raise Exception('Failed to get stack %s' % str(stack))

  def infer(self):
    try:
      stack = self.random_stack()
    except:
      return
    self.reflip(stack)

  def random_stack(self):
    key = self.db.randomKey()
    return key

  def evaluate_recurse(self, subexpr, env, reflip, stack, addition):
    if type(addition) != list:
      val = self.evaluate(subexpr, env, reflip, stack + [addition])
    else:
      val = self.evaluate(subexpr, env, reflip, stack + addition)
    return val
      
  def binary_op_evaluate(self, expr, env, reflip, stack):
    val1 = self.evaluate_recurse(expr.children[0], env, reflip, stack, 'operand0')
    val2 = self.evaluate_recurse(expr.children[1], env, reflip, stack, 'operand1')
    return (val1 , val2)
  
  def children_evaluate(self, expr, env, reflip, stack):
    return [self.evaluate_recurse(expr.children[i], env, reflip, stack, 'child' + str(i)) for i in range(len(expr.children))]

  # Draws a sample value (without re-sampling other values) given its parents, and sets it
  def evaluate(self, expr, env = None, reflip = False, stack = [], xrp_force_val = None):
    if env is None:
      env = self.env
      
    if xrp_force_val is not None: 
      assert expr.type == 'apply'
      
    if expr.type == 'value':
      val = expr.val
    elif expr.type == 'variable':
      var = expr.name
      (val, lookup_env) = env.lookup(var)
    elif expr.type == 'if':
      cond = self.evaluate_recurse(expr.cond, env, reflip, stack , 'cond')
      if cond.bool: 
        self.unevaluate(stack + ['false'])
        val = self.evaluate_recurse(expr.true, env, reflip, stack , 'true')
      else:
        self.unevaluate(stack + ['true'])
        val = self.evaluate_recurse(expr.false, env, reflip, stack , 'false')
    #elif expr.type == 'switch':
    #  index = self.evaluate_recurse(expr.index, env, reflip, stack , 'index')
    #  assert 0 <= index.num < expr.n
    #  for i in range(expr.n):
    #    if i != index.num:
    #      self.unevaluate(stack + ['child' + str(i)])
    #  val = self.evaluate_recurse(expr.children[index.num], env, reflip, stack, 'child' + str(index.num))
    elif expr.type == 'let':
      # NOTE: this really is a let*

      n = len(expr.vars)
      assert len(expr.expressions) == n
      values = []
      new_env = env
      for i in range(n): # Bind variables
        new_env = new_env.spawn_child()
        val = self.evaluate_recurse(expr.expressions[i], new_env, reflip, stack, 'let' + str(i))
        values.append(val)
        new_env.set(expr.vars[i], values[i])
        if val.type == 'procedure':
          val.env = new_env
      new_body = expr.body.replace(new_env)
      val = self.evaluate_recurse(new_body, new_env, reflip, stack, 'body')
    elif expr.type == 'apply':
      n = len(expr.children)
      args = [self.evaluate_recurse(expr.children[i], env, reflip, stack, 'arg' + str(i)) for i in range(n)]
      op = self.evaluate_recurse(expr.op, env, reflip, stack , 'operator')

      addition = ','.join([x.str_hash for x in args])
      if op.type == 'procedure':
        self.unevaluate(stack + ['apply'], addition)
        if n != len(op.vars):
          raise Exception('Procedure should have %d arguments.  \nVars were \n%s\n, but children were \n%s.' % (n, op.vars, expr.children))
        new_env = op.env.spawn_child()
        for i in range(n):
          new_env.set(op.vars[i], args[i])
        val = self.evaluate_recurse(op.body, new_env, reflip, stack, ('apply', addition))
      elif op.type == 'xrp':
        self.unevaluate(stack + ['apply'], addition)
  
        if xrp_force_val is not None:
          assert not reflip
          if self.has(stack):
            self.remove(stack)
          self.insert(stack, op.xrp, xrp_force_val, args, True)
          val = xrp_force_val
        else:
          substack = stack + ['apply', addition]
          if not self.has(substack):
            if op.xrp.is_mem():
              val = op.xrp.apply_mem(args, stack)
            else:
              val = op.xrp.apply(args)
            self.insert(substack, op.xrp, val, args)
          else:
            if reflip:
              self.remove(substack)
              if op.xrp.is_mem():
                val = op.xrp.apply_mem(args, stack)
              else:
                val = op.xrp.apply(args)
              self.insert(substack, op.xrp, val, args)
            else:
              (xrp, val, dbargs, is_obs_noise) = self.get(substack)
              assert not is_obs_noise
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
      (val1, val2) = self.binary_op_evaluate(expr, env, reflip, stack)
      val = val1.__eq__(val2)
    elif expr.type == '<':
      (val1, val2) = self.binary_op_evaluate(expr, env, reflip, stack)
      val = val1.__lt__(val2)
    elif expr.type == '>':
      (val1, val2) = self.binary_op_evaluate(expr, env, reflip, stack)
      val = val1.__gt__(val2)
    elif expr.type == '<=':
      (val1, val2) = self.binary_op_evaluate(expr, env, reflip, stack)
      val = val1.__le__(val2)
    elif expr.type == '>=':
      (val1, val2) = self.binary_op_evaluate(expr, env, reflip, stack)
      val = val1.__ge__(val2)
    elif expr.type == '&':
      vals = self.children_evaluate(expr, env, reflip, stack)
      andval = BoolValue(True)
      for x in vals:
        andval = andval.__and__(x.bool)
      val = andval
    elif expr.type == '^':
      vals = self.children_evaluate(expr, env, reflip, stack)
      xorval = BoolValue(True)
      for x in vals:
        xorval = xorval.__xor__(x.bool)
      val = xorval
    elif expr.type == '|':
      vals = self.children_evaluate(expr, env, reflip, stack)
      orval = BoolValue(False)
      for x in vals:
        orval = orval.__or__(x.bool)
      val = orval
    elif expr.type == '~':
      negval = self.evaluate_recurse(expr.children[0], env, reflip, stack, 'neg').bool
      val = negval.__inv__()
    elif expr.type == '+':
      vals = self.children_evaluate(expr, env, reflip, stack)
      sum_val = NatValue(0)
      for x in vals:
        sum_val = sum_val.__add__(x)
      val = sum_val
    elif expr.type == '-':
      val1 = self.evaluate_recurse(expr.children[0], env, reflip, stack , 'sub0')
      val2 = self.evaluate_recurse(expr.children[1], env, reflip, stack , 'sub1')
      val = val1.__sub__(val2)
    elif expr.type == '*':
      vals = self.children_evaluate(expr, env, reflip, stack)
      prod_val = NatValue(1)
      for x in vals:
        prod_val = prod_val.__mul__(x)
      val = prod_val
    elif expr.type == '/':
      val1 = self.evaluate_recurse(expr.children[0], env, reflip, stack , 'div0')
      val2 = self.evaluate_recurse(expr.children[1], env, reflip, stack , 'div1')
      val = val1.__div__(val2)
    else:
      raise Exception('Invalid expression type %s' % expr.type)
    return val


  def unevaluate(self, uneval_stack, args = None):
    if args is not None:
      args = tuple(args)

    to_unevaluate = []

    for tuple_stack in self.db:
      to_unevaluate.append(tuple_stack)
    for tuple_stack in self.db_noise:
      to_unevaluate.append(tuple_stack)

    to_delete = []

    for tuple_stack in to_unevaluate:
      stack = list(tuple_stack) 
      if len(stack) >= len(uneval_stack) and stack[:len(uneval_stack)] == uneval_stack:
        if args is None:
          to_delete.append(tuple_stack)
        else:
          assert len(stack) > len(uneval_stack)
          if stack[len(uneval_stack)] != args:
            to_delete.append(tuple_stack)

    for tuple_stack in to_delete:
      self.remove(tuple_stack)

  def predict(self, expr):
    return self.evaluate(expr, env, reflip, ['expr', expr.hashval])

  def save(self):
    self.log = []
    self.uneval_p = 0
    self.eval_p = 0

  def restore(self):
    self.log.reverse()
    for (type, stack, xrp, value, args, is_obs_noise) in self.log:
      if type == 'insert':
        self.remove(stack, False)
      else:
        assert type == 'remove'
        self.insert(stack, xrp, value, args, is_obs_noise, False)

  def reflip(self, stack):
    (xrp, val, args, is_obs_noise) = self.get(stack)
  
    #debug = True 
    debug = False
  
    old_p = self.p
    old_to_new_q = - math.log(len(self.db))
    if debug:
      print  "old_db", self 
  
    self.save()
  
    self.remove(stack)
    if xrp.is_mem():
      new_val = xrp.apply(args, list(stack))
    else:
      new_val = xrp.apply(args)
    self.insert(stack, xrp, new_val, args)
  
    if debug:
      print "\nCHANGING ", stack, "\n  TO   :  ", new_val, "\n"
  
    if val == new_val:
      return
  
    self.rerun(False)
    new_p = self.p
    new_to_old_q = self.uneval_p - math.log(len(self.db))
    old_to_new_q += self.eval_p
    if debug:
      print "new db", self, \
            "\nq(old -> new) : ", old_to_new_q, \
            "q(new -> old) : ", new_to_old_q, \
            "p(old) : ", old_p, \
            "p(new) : ", new_p, \
            'log transition prob : ',  new_p + new_to_old_q - old_p - old_to_new_q , "\n"
  
    if old_p * old_to_new_q > 0:
      p = rrandom.random.random()
      if new_p + new_to_old_q - old_p - old_to_new_q < math.log(p):
        self.restore()
        if debug:
          print 'restore'
        self.rerun(False)
  
    if debug:
      print "new db", self
      print "\n-----------------------------------------\n"

  def reset(self):
    self.__init__(self.env)

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

