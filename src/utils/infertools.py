from engine.directives import *
import time

""" Dictionary -> distribution """

def count_up(list):
  d = {}
  for x in list:
    if x in d:
      d[x] += 1
    else:
      d[x] = 1
  return d

def sum(list):
  ans = 0
  for x in list:
    ans += x
  return ans

def average(list):
  return sum(list) / (0.0 + len(list))

def standard_deviation(list):
  avg = average(list)
  variance = (sum((x-avg)**2 for x in list)) / (0.0 + len(list))
  return variance**0.5

def normalize(dict):
  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0)
  return dict

def merge_counts(d1, d2):
  d = {} 
  for x in d1:
    d[x] = d1[x]
  for x in d2:
    if x in d:
      d[x] += d2[x]
    else:
      d[x] = d2[x]
  return d

""" Inference routines """

# TODO: OUTDATED
def reject_infer():
  assert not directives.engine_type == 'traces'
  flag = False
  while not flag:
    rerun()

    # Reject if observations untrue
    flag = True
    for obs_hash in directives.engine.observes:
      (obs_expr, obs_val) = directives.engine.observes[obs_hash] 
      (val, id) = predict(obs_expr)
      if val != obs_val:
        flag = False
        break

# Rejection based inference
def reject_infer_many(name, niter = 1000):
  assert not directives.engine_type == 'traces'
  if name in directives.engine.vars:
    expr = directives.engine.vars[name]
  else:
    warnings.warn('%s is not defined' % str(name))

  dict = {}
  for n in range(niter):
    # Re-draw from prior
    reject_infer()
    ans = directives.engine.evaluate(expr, None, False, [name]) 

    if ans in dict:
      dict[ans] += 1
    else:
      dict[ans] = 1 

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 

def infer_many(expression, niter = 1000, burnin = 100, printiters = 0):

  if directives.engine_type == 'traces':
    rerun()
  dict = {}

  (val, id) = predict(expression)
  evalnode = directives.engine.predicts[id]

  for n in range(niter):
    if printiters > 0 and n % printiters == 0: 
      print n, "iters"

    # re-draw from prior
    infer(burnin)

    val = evalnode.val
    if val in dict:
      dict[val] += 1
    else:
      dict[val] = 1 

  return dict 

def follow_prior(names, niter = 1000, burnin = 100, timer = True, printiters = 0):
  rerun()
  dict = {}
  evalnodes = {}

  infer(burnin)

  for name in names:
    assert name not in ['TIME']
    dict[name] = []
    (val, id) = predict(var(name))
    evalnodes[name] = directives.engine.predicts[id]
  if timer:
    dict['TIME'] = []
  
  for n in range(niter):
    if printiters > 0 and n % printiters == 0: 
      print n, "iters"
    t = time.time()
    infer()

    for name in names:
      val = evalnodes[name].val
      if val.type != 'procedure' and val.type != 'xrp': 
        dict[name].append(val)
    t = time.time() - t
    if timer:
      dict['TIME'].append(t)

  for name in names:
    if len(dict[name]) == 0:
      del dict[name]
  return dict 

def sample_prior(names, niter = 1000, timer = True, printiters = 0):
  dict = {}

  for name in names:
    assert name not in ['TIME']
    dict[name] = []

  if timer:
    dict['TIME'] = []

  for n in range(niter):
    if printiters > 0 and n % printiters == 0: 
      print n, "iters"
    t = time.time()
    rerun()
    for name in names:
      (val, id) = predict(var(name))
      if val.type != 'procedure' and val.type != 'xrp': 
        dict[name].append(val)
    t = time.time() - t
    if timer:
      dict['TIME'].append(t)

  for name in names:
    if len(dict[name]) == 0:
      del dict[name]
  return dict 

def test_prior(niter = 1000, burnin = 100, countup = True, timer = True):
  expressions = []
  varnames = []

  # TODO : get all the observed variables
  if directives.engine_type == 'reduced traces':
    for id in directives.engine.assumes:
      evalnode = directives.engine.assumes[id]
      expressions.append(evalnode.expression)
      varnames.append(evalnode.assume_name)
  elif directives.engine_type == 'traces':
    for id in directives.engine.assumes:
      evalnode = directives.engine.assumes[id]
      assert evalnode.assume_name not in ['TIME']
      expressions.append(evalnode.expression)
      varnames.append(evalnode.assume_name)
  else:
    for (varname, expr) in directives.engine.assumes:
      assert varname not in ['TIME']
      expressions.append(expr)
      varnames.append(varname)

  d2 = follow_prior(varnames, niter, burnin, timer)
  d1 = sample_prior(varnames, niter, timer)

  for i in range(len(varnames)):
    name = varnames[i]
    if name in d1:
      assert name in d2
      if countup:
        d1[name] = count_up(d1[name])
        d2[name] = count_up(d2[name])
    else:
      assert name not in d2
  if countup and timer:
    d1['TIME'] = count_up(d1['TIME'])
    d2['TIME'] = count_up(d2['TIME'])
  return (d1, d2)

def test_prior_bool(d, varname):
  return abs(d[0][varname][False] - d[1][varname][False]) / (d[0][varname][False] + d[0][varname][True] + 0.0)

def test_prior_L0(d, varname, start, end, bucketsize):
  (d1, d2) = (d[0][varname], d[1][varname])
  c1 = get_cdf(d1, start, end, bucketsize, True)
  c2 = get_cdf(d2, start, end, bucketsize, True)
  a = L0distance(c1, c2)
  return a

""" NOISE """

def noisy(expression, error):
  return bernoulli(ifelse(expression, num_expr(1), num_expr(error)))

""" OUTPUT MANIPULATION """

def get_pdf(valuedict, start, end, bucketsize, normalizebool = True):
  if normalizebool:
    valuedict = normalize(valuedict)
  numbuckets = int(math.floor((end - start) / bucketsize))
  density = [0] * numbuckets
  for value in valuedict:
    if not start <= value <= end:
      warnings.warn('value %s is not in the interval [%s, %s]' % (str(value), str(start), str(end)))
      continue
    index = int(math.floor((value - start) / bucketsize))
    density[index] += valuedict[value]
  return density

def get_cdf(valuedict, start, end, bucketsize, normalizebool = True):
  numbuckets = int(math.floor((end - start) / bucketsize))
  density = get_pdf(valuedict, start, end, bucketsize, normalizebool)
  cumulative = [0]
  for i in range(numbuckets):
    cumulative.append(cumulative[-1] + density[i])
  if normalizebool:
    assert 0.999 < cumulative[-1] < 1.001
  return cumulative

def get_beta_cdf(a, b, bucketsize):
  assert type(a) == type(b) == int

  coeffs = [math.gamma(a+b) / (math.gamma(i + 1) * math.gamma(a+b-i)) for i in range(a, a+b)]

  numbuckets = int(math.floor(1.0 / bucketsize))
  xs = [i * bucketsize for i in range(numbuckets)]

  cumulative = [0]
  for x in xs:
    ppows = [1]
    npows = [1]
    for i in range(a + b):
      ppows.append(ppows[-1] * x)
      npows.append(npows[-1] * (1-x))
    sum = 0
    for i in range(a, a+b):
      sum += coeffs[i-a] * ppows[i] * npows[a + b - 1 - i]
    cumulative.append(sum)
  return cumulative

def format(list, format):
  return [ format % x for x in list]

""" DISTANCE MEASURES """

def L0distance(cdf1, cdf2):  # Kolmogorov-Smirnov test 
  return max(abs(cdf1[i] - cdf2[i]) for i in range(len(cdf1)))

def L1distance(cdf2, cdf1):
  return sum(abs(cdf1[i] - cdf2[i]) for i in range(len(cdf1)))

def KLdivergence(d, pdf):
  d = normalize(d)
  kl = 0
  for x in d:
    kl += d[x] * (log(d[x]) - log(pdf(x)))
  return kl

def perplexity(d, pdf):
  d = normalize(d)
  ans = 0
  for x in d:
    ans += d[x] * log(pdf(x))
  return ans
