from expressions import *
from mem import *

import utils.rrandom as rrandom

from utils.format import table_to_string
from utils.rexceptions import RException
from utils.expr_parser import *
import utils.infertools as infertools 

import time

try:
  from pypy.rlib.jit import JitDriver
  jitdriver = JitDriver(greens = [ \
                                 ### INTs 
                                 ### REFs 
                                 ### FLOATs 
                                 ],  \
                        reds   = [  \
                                 ### INTs 
                                 #'assume', \
                                 #'observed', \
                                 #'predict', \
                                 #'active', \
                                 #'mem', \
                                 #'random_xrp_apply', \

                                 ### REFs 
                                 #'traces', \
                                 #'parent', \
                                 #'mem_calls', \
                                 #'env', \
                                 #'assume_name', \
                                 #'observe_val', \
                                 #'expression', \
                                 #'type', \
                                 #'children', \
                                 #'active_children', \
                                 #'lookups', \
                                 #'xrp_applies', \
                                 #'xrp', \
                                 #'args', \
                                 #'val', \
                                 #'xrp_force_val', \
                                 'engine' \

                                 ### FLOATs 
                                 #'p' \
                                 ])
  def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()
  use_jit = True
except:
  use_jit = False


# TODO: jitting
#    if use_jit:
#      jitdriver.jit_merge_point( \
#                                 # INTs
#                                 #observed = evalnode.observed, \
#                                 #assume = evalnode.assume, \
#                                 #predict = evalnode.predict, \
#                                 #active = evalnode.active, \
#                                 #random_xrp_apply = evalnode.random_xrp_apply, \
#                                 #mem = evalnode.mem, \
#                                 ## REFs
#                                 #traces = evalnode.traces, \
#                                 #parent = evalnode.parent, \
#                                 #mem_calls = evalnode.mem_calls, \
#                                 #env = evalnode.env, \
#                                 #assume_name = evalnode.assume_name, \
#                                 #observe_val = evalnode.observe_val, \
#                                 #expression = evalnode.expression, \
#                                 #type = evalnode.type, \
#                                 #children = evalnode.children, \
#                                 #active_children = evalnode.active_children, \
#                                 #lookups = evalnode.lookups, \
#                                 #xrp_applies = evalnode.xrp_applies, \
#                                 #xrp = evalnode.xrp, \
#                                 #args = evalnode.args, \
#                                 #val = evalnode.val, \
#                                 engine = engine \
#                                 # FLOATs
#                                 #p = evalnode.p
#                                 )   
#    #node = engine.random_node()
#    ## evalnode if traces/reduced traces
#    ## stack if randomdb

class Directives:
  def __init__(self, engine):
    self.engine = engine

    # id -> (name, expr)
    self.assumes = {}
    # id -> (expr, val, active)
    self.observes = {}
    # id -> (expr, active)
    self.predicts = {}

    self.directives = []
    self.next_id = -1

    self.reset_engine()

  def reset(self):
    self.__init__(self.engine)
  
  def reset_engine(self):
    self.engine.reset()
  
    # BASIC DISTRIBUTIONS

    self.assume('bernoulli', xrp(bernoulli_XRP()), True)
    self.assume('flip', var('bernoulli'), True)
    self.assume('beta', xrp(beta_XRP()), True)
    self.assume('gamma', xrp(gamma_XRP()), True)
    self.assume('gaussian', xrp(gaussian_XRP()), True)
    self.assume('normal', var('gaussian'), True)
    self.assume('randbelow', xrp(uniform_discrete_XRP()), True)
    self.assume('rand', function([], apply(var('beta'), [num_expr(1), num_expr(1)])), True)

    self.assume('uniform-discrete', function(['min-inclusive', 'max-inclusive'],
                                    op('+', [apply(var('randbelow'), [op('+', [op('-', [var('max-inclusive'), var('min-inclusive')]), nat_expr(1)])]), var('min-inclusive')])),
                True)
    self.assume('uniform-continuous', function(['min-inclusive', 'max-inclusive'],
                                      op('+', [op('*', [apply(var('rand'), []), op('-', [var('max-inclusive'), var('min-inclusive')])]), var('min-inclusive')])),
                True)
   
    # FOR OBSERVES

    self.assume('noisy', function(['expr', 'noise'],  \
                         ifelse(apply(var('bernoulli'), [var('noise')]), negation(var('expr')), var('expr'))),  \
                 True) 

    self.assume('noise-negate', function(['expr', 'noise'],  \
                         apply(var('bernoulli'), [ifelse(var('expr'), num_expr(1), var('noise'))])),  \
                 True) 

    # MORE COMPLICATED PROCESSES

    #self.assume('dirichlet-multinomial/make', xrp(make_symmetric_dirichlet_XRP()), True)
    #self.assume('dirichlet', xrp(symmetric_dirichlet_args_XRP()), True)
    self.assume('symmetric-dirichlet-multinomial/make', xrp(make_symmetric_dirichlet_multinomial_XRP()), True)
    self.assume('symmetric-dirichlet', xrp(symmetric_dirichlet_XRP()), True)
  
    self.assume('CRP/make', xrp(gen_CRP_XRP()), True)
    self.assume('beta-binomial/make', xrp(make_beta_bernoulli_XRP()), True)
  
    self.assume('mem', xrp(mem_XRP()), True)

    """DEFINITION OF DP"""
    self.assume('DP_uncollapsed', \
           function(['concentration', 'basemeasure'], \
                    let([('sticks', apply(var('mem'), [function(['j'], apply(var('beta'), [num_expr(1), var('concentration')]))])),
                         ('atoms',  apply(var('mem'), [function(['j'], apply(var('basemeasure'), []))])),
                         ('loop', \
                          function(['j'], 
                                   ifelse(apply(var('bernoulli'), [apply(var('sticks'), [var('j')])]), \
                                          apply(var('atoms'), [var('j')]), \
                                          apply(var('loop'), [op('+', [var('j'), num_expr(1)])])))) \
                        ], \
                        function([], apply(var('loop'), [num_expr(1)])))),
           True) 
  
    """DEFINITION OF ONE ARGUMENT DPMEM"""
    self.assume('DPmem_uncollapsed', \
           function(['concentration', 'proc'], \
                    let([('restaurants', \
                          apply(var('mem'), [function(['args'], apply(var('DP'), [var('concentration'), function([], apply(var('proc'), [var('args')]))]))]))], \
                        function(['args'], apply(var('restaurants'), [var('args')])))), 
           True) 

  def get_next_id(self):
    self.next_id += 1
    return self.next_id

  def assume(self, name, expr, default = False):
    id = -1
    if not default:
      self.directives.append('assume')
      id = self.get_next_id()
      self.assumes[id] = (name, expr)
    val = self.engine.assume(name, expr, id)
    return (val, id)
  
  def observe(self, expr, val):
    self.directives.append('observe')
    id = self.get_next_id()
    self.observes[id] = (expr, val, True)
    val = self.engine.observe(expr, val, id)
    return id
  
  def forget(self, id):
    if self.directives[id] == 'observe':
      if id not in self.observes:
        raise RException("id %d was never observed" % id) 
      (expr, val, active) = self.observes[id]
      if not active:
        raise RException("observe %d was already forgotten" % id) 
      self.observes[id] = (expr, val, False)
    elif self.directives[id] == 'predict':
      if id not in self.predicts:
        raise RException("id %d was never predicted" % id) 
      (expr, active) = self.predicts[id]
      if not active:
        raise RException("predict %d was already forgotten" % id) 
      self.predicts[id] = (expr, False)
    else:
      raise RException("Cannot forget assumes")
    self.engine.forget(id)
    return
    
  def predict(self, expr):
    self.directives.append('predict')
    id = self.get_next_id()
    self.predicts[id] = (expr, True)
    val = self.engine.predict(expr, id)
    return (val, id)
  
  def rerun(self):
  # Class representing environments
    self.reset_engine()
    for id in range(len(self.directives)):
      if self.directives[id] == 'assume':
        (varname, expr) = self.assumes[id]
        self.engine.assume(varname, expr, id)
      elif self.directives[id] == 'observe':
        (expr, val, active) = self.observes[id]
        if active:
          self.engine.observe(expr, val, id)
      elif self.directives[id] == 'predict':
        (expr, active) = self.predicts[id]
        if active:
          self.engine.predict(expr, id)
      else:
        raise RException("Invalid directive")
    
  def report_value(self, id):
    value = self.engine.report_value(id)
    return value
  
  #def report_directives(self, desired_directive_type = ""):
  #  directive_report = []
  #  for id in range(len(self.directives)):
  #    directive_type = self.directives[id]
  #    if desired_directive_type in ["", directive_type]:
  #      d = {}
  #      d["directive-id"] = str(id)
  #      if directive_type == 'assume':
  #        (varname, expr) = self.assumes[id]
  #        d["directive-type"] = "DIRECTIVE-ASSUME"
  #        d["directive-expression"] = expr.__str__()
  #        d["name"] = varname
  #        d["value"] = self.report_value(id).__str__()
  #        directive_report.append(d)
  #      elif directive_type == 'observe':
  #        (expr, val, active) = self.observes[id]
  #        d["directive-type"] = "DIRECTIVE-OBSERVE"
  #        d["directive-expression"] = expr.__str__()
  #        #d["value"] = self.report_value(id).__str__()
  #        directive_report.append(d)
  #      elif directive_type == 'predict':
  #        (expr, active) = self.predicts[id]
  #        d["directive-type"] = "DIRECTIVE-PREDICT"
  #        d["directive-expression"] = expr.__str__()
  #        d["value"] = self.report_value(id).__str__()
  #        directive_report.append(d)
  #      else:
  #        raise RException("Invalid directive %s" % directive_type)
  #  return directive_report
  
  def infer(self, iters = 1):
    t = time.time()
    for i in range(iters):
      self.engine.infer()
    t = time.time() - t
    return t

  def infer_many(self, expression, niter = 1000, burnin = 100, printiters = 0): 
    self.rerun()
    dict = {}
    (val, id) = self.predict(expression)
  
    for n in range(niter):
      if printiters > 0 and n % printiters == 0:  
        print n, "iters"
  
      self.infer(burnin)
  
      val = self.report_value(id).__hash__()
      if val in dict:
        dict[val] += 1
      else:
        dict[val] = 1 
  
    return dict 

  def parse_and_run_command(self, s):
    ret_str = 'done'
    (token, i) = parse_token(s, 0)
    if token == 'assume':
      (var, i) = parse_token(s, i)
      (expr, i) = parse_expression(s, i)
      (val, id) = self.assume(var, expr)
      ret_str = 'value: ' + val.__str__() + '\nid: ' + str(id)
    elif token == 'observe':
      (expr, i) = parse_expression(s, i)
      (val, i) = parse_value(s, i)
      id = self.observe(expr, val)
      ret_str = 'id: ' + str(id)
    elif token == 'predict':
      (expr, i) = parse_expression(s, i)
      (val, id) = self.predict(expr)
      ret_str = 'value: ' + val.__str__() + '\nid: ' + str(id)
    elif token == 'forget':
      (id, i) = parse_integer(s, i)
      self.forget(id)
      ret_str = 'forgotten'
    elif token == 'infer':
      try:
        (iters, i) = parse_integer(s, i)
      except:
        iters = 1
      t = self.infer(iters)
      ret_str = 'time: ' + str(t)
    elif token == 'seed':
      (seed, i) = parse_integer(s, i)
      rrandom.random.seed(seed)
    # TODO: fix
    elif token == 'infer_many':
      (expression, i) = parse_expression(s, i)
      (niters, i) = parse_integer(s, i)
      (burnin, i) = parse_integer(s, i)
      t = time.time()
      d = self.infer_many(expression, niters, burnin)
      t = time.time() - t
      ret_str = '\n'
      table = []
      for val in d:
        p = d[val]
        table.append([str(val), str(p)])
      ret_str = table_to_string(table, ['Value', 'Count'])
      ret_str += '\nTime taken (seconds): ' + str(t)
    elif token == 'clear':
      self.reset()
      ret_str = 'cleared'
    elif token == 'report_value':
      (id, i) = parse_integer(s, i)
      ret_str = 'value: ' + self.report_value(id).__str__()
    #elif token == 'report_directives':
    #  (directive_type, i) = parse_token(s, i)
    #  directives_report = self.report_directives(directive_type)
    #  ret_str = table_to_string(directives_report, ['id', 'directive', 'value'])
    else:
      raise RException("Invalid directive")
    return ret_str
