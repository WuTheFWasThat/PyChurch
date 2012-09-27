from directives import *
import matplotlib.pyplot as plt 

""" Inference routines """
# some re-naming needed perhaps

def infer_many(name, niter = 1000, burnin = 100):

  if name in globals.mem.vars:
    expr = globals.mem.vars[name]
  else:
    warnings.warn('%s is not defined' % str(name))

  dict = {}
  for n in xrange(niter):
    if n > 0 and n % 100 == 0: print n, "iters"

    # re-draw from prior
    rerun(True)
    for t in xrange(burnin):
      infer()

    val = evaluate(name, globals.env, reflip = False, stack = [name])
    if val in dict:
      dict[val] += 1
    else:
      dict[val] = 1 

  return dict 

def follow_prior(names, niter = 1000, burnin = 100):
  rerun(True)
  dict = {}

  for t in xrange(burnin):
    infer()

  for name in names:
    if name in globals.mem.vars:
      expr = globals.mem.vars[name]
    else:
      warnings.warn('%s is not defined' % str(name))
    dict[name] = []

  for n in xrange(niter):
    if n > 0 and n % 100 == 0: print n, "iters"
    infer()

    for name in names:
      val = evaluate(name, globals.env, reflip = False, stack = [name]).val
      dict[name].append(val)

  return dict 

# TODO : just automatically get all the assume/observe variables
def sample_prior(names, niter = 1000):
  dict = {}

  for name in names:
    if name in globals.mem.vars:
      expr = globals.mem.vars[name]
    else:
      warnings.warn('%s is not defined' % str(name))
    dict[name] = {}

  for n in xrange(niter):
    rerun(True)
    for name in names:
      val = evaluate(name, globals.env, reflip = False, stack = [name]).val
      if val in dict[name]:
        dict[name][val] += 1
      else:
        dict[name][val] = 1

  return dict 

def noisy(expression, error):
  return bernoulli(ifelse(expression, 1, error))

""" OUTPUT MANIPULATION """

def count_up(list):
  d = {}
  for x in list:
    if x in d:
      d[x] += 1
    else:
      d[x] = 1
  return d

def normalize(dict):
  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0)
  return dict

def get_pdf(valuedict, start, end, bucketsize, normalizebool = True):
  if normalizebool:
    valuedict = normalize(valuedict)
  numbuckets = int(math.floor((end - start) / bucketsize))
  density = [0] * numbuckets
  for value in valuedict:
    if not start <= value.val <= end:
      warnings.warn('value %s is not in the interval [%s, %s]' % (str(value), str(start), str(end)))
      continue
    index = int(math.floor((value.val - start) / bucketsize))
    density[index] += valuedict[value.val]
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

""" PLOTTING TOOLS """

def plot(xs, ys, name = 'graphs/plot.png', minx = None, maxx = None, miny = None, maxy = None):
  if minx is None: minx = xs[0]
  if maxx is None: maxx = xs[-1]
  if miny is None: miny = min(ys)
  if maxy is None: maxy = max(ys)
  plt.axis([minx, maxx, miny, maxy])
  plt.plot(xs, ys)
  plt.savefig(name)
#  plt.close()

def plot_dist(ys, start, end, bucketsize, name = 'graphs/plot.png', ymax = None):
  numbuckets = int(math.floor((end - start) / bucketsize))
  xs = [start + i * bucketsize for i in range(numbuckets+1)]
  plot(xs, ys, name, start, end, 0, ymax)

def plot_pdf(valuedict, start, end, bucketsize, name = 'graphs/plot.png', ymax = None):
  plot_dist(get_pdf(valuedict, start, end, bucketsize), start + (bucketsize / 2.0), end - (bucketsize / 2.0), bucketsize, name, ymax)

def plot_cdf(valuedict, start, end, bucketsize, name = 'graphs/plot.png'):
  plot_dist(get_cdf(valuedict, start, end, bucketsize), start, end, bucketsize, name, 1)

def plot_beta_cdf(a, b, bucketsize, name = 'graphs/betaplot.png'):
  plot_dist(get_beta_cdf(a, b, bucketsize), 0, 1, bucketsize, name, 1)

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

def plotnames(names, plotname = 'plotnames'):
  for name in names:
    plot(range(niter), dict[name], 'graphs/' + plotname + '-' + name + '.png')

""" DISTANCE MEASURES """

def L0distance(cdf1, cdf2):  # Kolmogorov-Smirnov test 
  return max(abs(cdf1[i] - cdf2[i]) for i in xrange(len(cdf1)))

def L1distance(cdf2, cdf1):
  return sum(abs(cdf1[i] - cdf2[i]) for i in xrange(len(cdf1)))

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
