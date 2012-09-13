from directives import * 
from mem import *
from time import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages 

simpletests = True

def noisy(expression, error):
  return bernoulli(ifelse(expression, 1, error))

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

def L0distance(cdf1, cdf2):  # Kolmogorov-Smirnov test 
  return max(abs(cdf1[i] - cdf2[i]) for i in xrange(len(cdf1)))

def L1distance(cdf2, cdf1):   
  return sum(abs(cdf1[i] - cdf2[i]) for i in xrange(len(cdf1)))

""" TESTS """

def test_expressions():
  print " \n TESTING EXPRESSIONS, SAMPLING \n"
  
  f = function(('x','y','z'), ifelse(var('x'), var('y'), var('z')))
  print 'Sample of\n%s\n= %s\n' % (str(f), str(resample(f)))
  
  g = function( ('x', 'z'), apply(f, [var('x'), constant(0), var('z')] ))
  print 'Sample of\n%s\n= %s\n' % (str(g), str(resample(g)))
  
  a = bernoulli(0.5) 
  print 'Some samples of\n%s:' % (str(a))
  print [resample(a) for i in xrange(10)]
  print 
  
  x = apply(g, [a, uniform(22)])
  print 'Some samples of\n%s:' % (str(x))
  print [resample(x) for i in xrange(10)]
  print
  
  b = ifelse(bernoulli(0.2), beta(3,4), beta(4,3))
  print 'Some samples of\n%s:' % (str(b))
  print [resample(b) for i in xrange(10)]
  print 
  
  c = (~bernoulli(0.3) & bernoulli(0.4)) | bernoulli(b)
  print 'Some samples of\n%s:' % (str(c))
  print [resample(c) for i in xrange(10)]
  print 
  
  d = function('x', ('apply', f, [a,c,'x']))
  print 'Sample of\n%s\n= %s\n' % (str(d), str(resample(d)))
  
  e = apply( d, b)
  print 'Some samples of\n%s:' % (str(e))
  print [resample(e) for i in xrange(10)]
  print

  #testing closure
  f = function(('x', 'y'), apply('x', 'y'))
  g = function('x', var('x') + 1)
  print sample(apply(f, [g, 21]))
  print 'Should be 22'
  assume('f', f)
  assume('g', g)

  a = let([('b', 1)], var('b') + 3)
  print sample(a)
  print 'Should be 4'
  print
  b = let([('c', 21), ('d', 'f')], apply('d', ['g', 'c']))
  print sample(b)
  print 'Should be 22'
  print
  e = let([('a', function(['x', 'y', 'z'], ifelse(bernoulli('x'), 'y', 'z'))), ('b', beta(1, 1)), ('c', uniform(3)), ('d', gaussian(5, .1))], apply('a', ['b', 'c', 'd']))
  print 'Some samples of\n%s:' % (str(e))
  print [resample(e) for i in xrange(10)]
  print


def test_tricky():
  print " \n COIN TEST\n "
  reset()

  noise_level = .001

  #assume('make-coin', function([], apply(function('weight', function([], bernoulli('weight'))), beta(1, 1))))
  #print globals.env.lookup('make-coin')

  #assume('tricky-coin', apply('make-coin'))
  #print globals.env.lookup('tricky-coin')
  #print "flips: ", [sample(apply('tricky-coin')) for i in xrange(10)]
  #
  #assume('my-coin-2', apply('make-coin'))
  #print globals.env.lookup('my-coin-2')
  #print "flips: ", [sample(apply('my-coin-2')) for i in xrange(10)]

  assume('weight', beta(1, 1))
  assume('tricky-coin', function([], bernoulli('weight')))

  assume('fair-coin', function([], bernoulli(0.5)))
  print globals.env.lookup('fair-coin')
  print "fair coin flips: ", [sample(apply('fair-coin')) for i in xrange(10)]

  assume('is-fair', bernoulli(0.5))
  assume('coin', ifelse('is-fair', 'fair-coin', 'tricky-coin')) 
  #assume('coin', ifelse('is-fair', 'fair-coin', apply('make-coin'))) 

  nheads = 5
  niters, burnin = 1000, 100

  print 'running', niters, 'times,', burnin, 'burnin'

  print '\nsaw', 0, 'heads'
  print follow_prior('is-fair', niters, burnin)
  
  for i in xrange(nheads):
    print '\nsaw', i+1, 'heads'
    observe(noisy(apply('coin'), noise_level), True)
    print follow_prior('is-fair', niters, burnin)

def test_beta_bernoulli():
  print " \n TESTING BETA-BERNOULLI XRPs\n"
  
  print "beta_bernoulli_1"
  coin1 = beta_bernoulli_1()
  print [sample(apply(coin1)) for i in xrange(10)]
  print coin1.state
  
  print "beta_bernoulli_2"
  coin_2 = beta_bernoulli_2()
  print [sample(apply(coin_2)) for i in xrange(10)]
  print coin_2.state

def test_CRP():
  print " \n TESTING CHINESE RESTAURANT PROCESS XRP\n"
  
  print "CRP(1)"
  assume('crp1', CRP(1))
  print [sample(apply('crp1')) for i in xrange(10)]
  
  print "CRP(10)"
  assume('crp2', CRP(10))
  print [sample(apply('crp2')) for i in xrange(10)]

  assume('alpha', gamma(0.1, 10))
  assume('cluster-crp', CRP('alpha'))
  assume('get-cluster-mean', mem(function('cluster', gaussian(0, 10))))
  assume('get-cluster-variance', mem(function('cluster', gamma(0.1, 100))))
  assume('get-cluster', mem(function('id' ,'cluster-crp')))
  assume('get-cluster-model', mem(function('cluster', function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
  assume('get-datapoint', mem(function('id', apply('get-cluster-model', apply('get-cluster', 'id')))))

def test_bayes_nets():
  print "\n TESTING INFERENCE ON CLOUDY/SPRINKLER\n"
  
  niters, burnin = 100, 100

  reset()
  assume('cloudy', bernoulli(0.5))
  
  assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5)))
  
  noise_level = .001
  sprinkler_ob = observe(noisy('sprinkler', noise_level), True)
  print follow_prior('cloudy', niters, burnin)
  print 'Should be .833 False, .166 True'
  
  forget(sprinkler_ob)
  print follow_prior('cloudy', niters, burnin)
  print 'Should be .500 False, .500 True'

  print "\n TESTING BEACH NET\n"
  
  niters, burnin = 100, 100

  reset()
  assume('sunny', bernoulli(0.5))
  assume('weekend', bernoulli(0.285714))
  assume('beach', ifelse('weekend', ifelse('sunny', bernoulli(0.9), bernoulli(0.5)), \
                                    ifelse('sunny', bernoulli(0.3), bernoulli(0.1))))
  
  observe(noisy('weekend', noise_level), True)
  print follow_prior('sunny', niters, burnin)
  print 'Should be .5 False, .5 True'
  
  observe(noisy('beach', noise_level), True)
  print follow_prior('sunny', niters, burnin)
  print 'Should be .357142857 False, .642857143 True'

  print "\n TESTING MODIFIED BURGLARY NET\n" # An example from AIMA
  reset()

  niters, burnin = 100, 100

  pB = 0.1
  pE = 0.2
  pAgBE, pAgBnE, pAgnBE, pAgnBnE = 0.95, 0.94, 0.29, 0.10
  pJgA, pJgnA = 0.9, 0.5
  pMgA, pMgnA = 0.7, 0.1
  
  pA = pB * pE * pAgBE + (1-pB) * pE * pAgnBE + pB * (1 - pE) * pAgBnE + (1-pB) * (1-pE) * pAgnBnE
  
  pJ = pA * pJgA + (1 - pA) * pJgnA
  
  pAgnB = (pE * pAgnBE + (1 - pE) * pAgnBnE) / (1 - pB)
  pJgnB = pJgA * pAgnB + pJgnA * (1 - pAgnB) 
  
  pAgM = pMgA * pA / (pMgA * pA + pMgnA * (1 - pA))
  pJgM = pAgM * pJgA + (1 - pAgM) * pJgnA
  
  pJnB = pJgnB * (1 - pB)
  
  assume('burglary', bernoulli(pB))
  assume('earthquake', bernoulli(pE))
  assume('alarm', ifelse('burglary', ifelse('earthquake', bernoulli(pAgBE), bernoulli(pAgBnE)), \
                                    ifelse('earthquake', bernoulli(pAgnBE), bernoulli(pAgnBnE))))

  assume('johnCalls', ifelse('alarm',  bernoulli(pJgA), bernoulli(pJgnA)))
  assume('maryCalls', ifelse('alarm',  bernoulli(pMgA), bernoulli(pMgnA)))

  print follow_prior('alarm', niters, burnin)
  print 'Should be %f True' % pA

  mary_ob = observe(noisy('maryCalls', noise_level), True)
  print follow_prior('johnCalls', niters, burnin)
  print 'Should be %f True' % pJgM
  forget(mary_ob)

  burglary_ob = observe(noisy(~var('burglary'), noise_level), True)
  print follow_prior('johnCalls', niters, burnin)
  print 'Should be %f True' % pJgnB
  forget(burglary_ob)

  print "\n TESTING BURGLARY NET\n" # An example from AIMA

  pB = 0.001
  pE = 0.002
  pAgBE = 0.95
  pAgBnE = 0.94
  pAgnBE = 0.29
  pAgnBnE = 0.001
  pJgA = 0.9
  pJgnA = 0.05
  pMgA = 0.7
  pMgnA = 0.01
  
  pA = pB * pE * pAgBE + (1-pB) * pE * pAgnBE + pB * (1 - pE) * pAgBnE + (1-pB) * (1-pE) * pAgnBnE
  
  pJ = pA * pJgA + (1 - pA) * pJgnA
  
  pAgnB = (pE * pAgnBE + (1 - pE) * pAgnBnE) / (1 - pB)
  pJgnB = pJgA * pAgnB + pJgnA * (1 - pAgnB) 
  
  pAgM = pMgA * pA / (pMgA * pA + pMgnA * (1 - pA))
  pJgM = pAgM * pJgA + (1 - pAgM) * pJgnA
  
  pJnB = pJgnB * (1 - pB)
  
  reset()
  assume('burglary', bernoulli(pB))
  assume('earthquake', bernoulli(pE))
  assume('alarm', ifelse('burglary', ifelse('earthquake', bernoulli(pAgBE), bernoulli(pAgBnE)), \
                                    ifelse('earthquake', bernoulli(pAgnBE), bernoulli(pAgnBnE))))

  assume('johnCalls', ifelse('alarm',  bernoulli(pJgA), bernoulli(pJgnA)))
  assume('maryCalls', ifelse('alarm',  bernoulli(pMgA), bernoulli(pMgnA)))

  print follow_prior('alarm', niters, burnin)
  print 'Should be %f True' % pA

  mary_ob = observe(noisy('maryCalls', noise_level), True)
  print follow_prior('johnCalls', niters, burnin)
  print 'Should be %f True (BUT WONT BE)' % pJgM
  forget(mary_ob)

  burglary_ob = observe(noisy(~var('burglary'), noise_level), True)
  print follow_prior('johnCalls', niters, burnin)
  print 'Should be %f True' % pJgnB
  forget(burglary_ob)

def test_xor():
  print "\n XOR TEST\n"

  reset()
 
  p = 0.6
  q = 0.4
  noise_level = .01
  assume('a', bernoulli(p)) 
  assume('b', bernoulli(q)) 
  assume('c', var('a') ^ var('b'))

  #print follow_prior('a', 10000, 100) 
  #print 'should be 0.60 true'
  # should be True : p, False : 1 - p

  xor_ob = observe(noisy('c', noise_level), True) 
  print follow_prior('a', 1000, 50) 
  print 'should be 0.69 true'
  # should be True : p(1-q)/(p(1-q)+(1-p)q), False : q(1-p)/(p(1-q) + q(1-p)) 
  # I believe this gets skewed because it has to pass through illegal states, and the noise values get rounded badly 

def test_recursion():
  print "\n TESTING RECURSION, FACTORIAL\n" 
  reset() 
  
  factorial_expr = function('x', ifelse(var('x') == 0, 1, \
              var('x') * apply('factorial', var('x') - 1))) 
  assume('factorial', factorial_expr) 
  
  print "factorial" 
  print factorial_expr 
  print "factorial(5) =", sample(apply('factorial', 5)) 
  print "should be 120"
  print "factorial(10) =", sample(apply('factorial', 10)) 
  print "should be 3628800"

def test_mem():
  print "\n MEM TEST, FIBONACCI\n" 
  reset() 
  
  fibonacci_expr = function('x', ifelse(var('x') <= 1, 1, \
                apply('fibonacci', var('x') - 1) + apply('fibonacci', var('x') - 2) )) 
  assume('fibonacci', fibonacci_expr) 
  print "fib(20) should be 10946\n"
  
  print "fibonacci" 
  print fibonacci_expr 
  t = time()
  print "fibonacci(20) =", sample(apply('fibonacci', 20)) 
  print "      took", time() - t, "seconds"
  t = time()
  print "fibonacci(20) =", sample(apply('fibonacci', 20)) 
  print "      took", time() - t, "seconds"

  assume('bad_mem_fibonacci', mem('fibonacci')) 
  # Notice that this mem'ed fibonacci doesn't recurse using itself.  It still calls fibonacci

  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"
  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"

  mem_fibonacci_expr = function('x', ifelse(var('x') <= 1, 1, \
                apply('mem_fibonacci', var('x') - 1) + apply('mem_fibonacci', var('x') - 2) )) 
  assume('mem_fibonacci', mem(mem_fibonacci_expr)) 

  print "mem_fibonacci(20) =", sample(apply('mem_fibonacci', 20))
  print "      took", time() - t, "seconds"
  t = time()
  print "mem_fibonacci(20) =", sample(apply('mem_fibonacci', 20))
  print "      took", time() - t, "seconds"

def test_geometric():
  reset()
  print " \n TESTING GEOMETRIC\n"

  print "Sampling from a geometric distribution"

  a, b = 3, 2
  timetodecay = 1
  bucketsize = .01

  niters, burnin = 100, 100 

  assume('decay', beta(a, b))
  #assume('decay', 0.5)
  #assume('decay', uniform(5))

  assume('geometric', function('x', ifelse(bernoulli('decay'), 'x', apply('geometric', var('x') + 1))))
  print "decay", globals.env.lookup('decay')
  print [sample(apply('geometric', 0)) for i in xrange(10)]
  observe(noisy(apply('geometric', 0) == timetodecay, .001), True)
  dist = follow_prior('decay', niters, burnin)
  print dist 
  print 'pdf:', get_pdf(dist, 0, 1, .1)
  print 'cdf:', get_cdf(dist, 0, 1, .1)

  plot_beta_cdf(a, b, bucketsize, name = 'graphs/prior.png')
  plot_cdf(dist, 0, 1, bucketsize, name = 'graphs/geometric%d.png' % burnin)
  plot_beta_cdf(a + 1, b + timetodecay, bucketsize, name = 'graphs/posterior.png')

  prior_cdf = get_beta_cdf(a, b, bucketsize)
  posterior_cdf = get_beta_cdf(a + 1, b+timetodecay, bucketsize)
  dist_cdf = get_cdf(dist, 0, 1, bucketsize)

  print "L0 distance from prior     = %0.3f" % L0distance(prior_cdf, dist_cdf)

  print "L0 distance from posterior = %0.3f" % L0distance(posterior_cdf, dist_cdf)   

  print "L1 distance from prior     = %0.3f" % L1distance(prior_cdf, dist_cdf)

  print "L1 distance from posterior = %0.3f" % L1distance(posterior_cdf, dist_cdf)   

def test_DPmem():
  reset()
  print " \n TESTING DP\n"

  def count_distinct(ls):
    d = set()
    dd = set()
    count = 0
    duplicates = 0
    for x in ls:
      if x not in d:
        d.add(x)
        count += 1
      else:
        if x not in dd:
          dd.add(x)
          duplicates += 1
    return duplicates 

  concentration = 10
  measure = function([], gaussian(0, 1))

  """DEFINITION OF DP"""

  assume('DP', \
         function(['concentration', 'basemeasure'], \
                  let([('sticks', mem(function('j', beta(1, 'concentration')))),
                       ('atoms',  mem(function('j', apply('basemeasure')))),
                       ('loop', \
                        function('j', \
                                 ifelse(bernoulli(apply('sticks', 'j')), \
                                        apply('atoms', 'j'), \
                                        apply('loop', var('j')+1)))) \
                      ], \
                      function([], apply('loop', 1))))) 

  print "TEST VERSION"
  assume('DPgaussian', apply('DP', [concentration, measure]))
  print 'DPGaussian = ', sample('DPgaussian')
  ls = [sample(apply('DPgaussian')) for i in xrange(10)]
  print ls
  print count_distinct(ls)

  """TESTING DP"""
  if simpletests:
    concentration = .1 # when close to 0, lots of repeat.  when close to infinity, many new sample 
    assume('DPgaussian', apply('DP', [concentration, function([], gaussian(0, 1))]))
    print [sample(apply('DPgaussian')) for i in xrange(10)]

    concentration = 10 # when close to 0, lots of repeat.  when close to infinity, many new sample 
    assume('DPgaussian', apply('DP', [concentration, function([], gaussian(0, 1))]))
    print [sample(apply('DPgaussian')) for i in xrange(10)]

  print " \n TESTING DPMem\n"

  """DEFINITION OF DPMEM"""
  # Only supports function with exactly one argument
  assume('DPmem', \
         function(['concentration', 'proc'], \
                  let([('restaurants', \
                        mem( function('args', apply('DP', ['concentration', function([], apply('proc', 'args'))]))))], \
                      function('args', apply('restaurants', 'args'))))) 

  """TESTING DPMEM"""
  concentration = 1 # when close to 0, just mem.  when close to infinity, sample 
  assume('DPmemflip', apply('DPmem', [concentration, function(['x'], gaussian(0, 1))]))
  #print [sample(apply(apply('DPmemflip', 222))) for i in xrange(10)]
  #print [sample(apply(apply('DPmemflip', 22))) for i in xrange(10)]
  #print [sample(apply(apply('DPmemflip', 222))) for i in xrange(10)]

  print "\n TESTING GAUSSIAN MIXTURE MODEL\n"
  assume('expected-mean', gaussian(0, 5)) 
  assume('expected-variance', let([('x', gaussian(2,1))], var('x')*var('x'))) # should never be negative
  assume('alpha', 1) #gaussian(1, 0.2)) # use vague-gamma?
  assume('gen-cluster-mean', apply('DPmem', ['alpha', function(['x'], gaussian('expected-mean', 'expected-variance'))]))
  assume('get-datapoint', mem(function(['id'], gaussian(apply(apply('gen-cluster-mean', 222)), 0.1))))
  assume('outer-noise', 0.1) # gaussian(1, 0.2)) # use vague-gamma?

#  points = {} 
#  for i in xrange(100):
#    print sample(apply('get-datapoint', i))
#  for i in xrange(1000):
#    val = sample(apply('get-datapoint', i))
#    if val in points:
#      points[val] += 1
#    else:
#      points[val] = 1
#  plot_pdf(points, -50, 50, 0.1, name = 'graphs/mixturesample.png')

  observe(gaussian(apply('get-datapoint', 0), let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 2.3)
  observe(gaussian(apply('get-datapoint', 1), let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 2.2)
  observe(gaussian(apply('get-datapoint', 2), let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 1.9)
  observe(gaussian(apply('get-datapoint', 3), let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 2.0)
  observe(gaussian(apply('get-datapoint', 4), let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 2.1)

  #niters, burnin = 100, 100

  print sample(apply('get-datapoint', 0))
  a = follow_prior(apply('get-datapoint', 0), 10, 10)
  print sample(apply('get-datapoint', 0))
  print sample(apply('get-datapoint', 0))
  print sample(apply('get-datapoint', 0))
  print a
  #print format(get_pdf(a, -4, 4, .5), '%0.2f') 

  #print 'running', niters, 'times,', burnin, 'burnin'

  #t = time()
  #a = follow_prior('expected-mean', niters, burnin)
  #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
  #print 'time taken', time() - t

  #concentration = 1
  #uniform_base_measure = uniform_no_args_XRP(2)
  #print [sample(apply('DP', [concentration, uniform_base_measure])) for i in xrange(10)]
  #expr = beta_bernoulli_1()

def test():
  reset()
  print " \n TESTING BLAH\n"
  
  print "description"
  expr = beta_bernoulli_1()
  print [sample(apply(coin_1)) for i in xrange(10)]
  
if simpletests:
  test_expressions()
  test_recursion()
  test_beta_bernoulli()
test_CRP()

#test_mem()
#test_bayes_nets() 
#test_xor()  # needs like 500 to mix 
#test_tricky() 
#test_geometric()   
test_DPmem()

#L0test([], [])
