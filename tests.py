from mem import *
from infertools import * 
from time import *

import unittest

test_expressions = True
test_recursion = False
test_beta_bernoulli = False

test_mem = False
test_bayes_nets = True
test_xor = False # needs like 500 to mix
test_tricky  = False
test_geometric = False
test_DPmem = False
test_CRP = False

test_easy_mixture = False

""" TESTS """

class TestDirectives(unittest.TestCase):
  def setUp(self):
    reset()

  @unittest.skipIf(not test_expressions, "skipping test_expressions")
  def test_expressions(self):
  
    f = function(('x','y','z'), ifelse(var('x'), var('y'), var('z')))
    self.assertTrue(sample(f).type == 'procedure')
    
    g = function( ('x', 'z'), apply(f, [var('x'), constant(0), var('z')] ))
    self.assertTrue(sample(g).type == 'procedure')
    
    a = bernoulli(0.5) 
    d = count_up([resample(a).val for i in xrange(1000)])
    self.assertTrue(d[True] + d[False] == 1000)
    self.assertTrue(450 < d[True] < 550)
    
    x = apply(g, [a, uniform(22)])
    b = ifelse(bernoulli(0.2), beta(3,4), beta(4,3))
    c = (~bernoulli(0.3) & bernoulli(0.4)) | bernoulli(b)
    d = function('x', ('apply', f, [a,c,'x']))
    e = apply( d, b)
  
    # Testing closure
    f = function(('x', 'y'), apply('x', 'y'))
    g = function('x', var('x') + 1)
    self.assertTrue(sample(apply(f, [g, 21])) == 22)

    assume('f', f)
    assume('g', g)
    a = let([('b', 1)], var('b') + 3)
    self.assertTrue(sample(a) == 4)

    b = let([('c', 21), ('d', 'f')], apply('d', ['g', 'c']))
    self.assertTrue(sample(b) == 22)


  @unittest.skipIf(not test_tricky, "skipping test_tricky")
  def test_tricky(self):
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
    print test_prior(1000, 100)
  
    nheads = 5
    niters, burnin = 1000, 100
  
    print 'running', niters, 'times,', burnin, 'burnin'
  
    print '\nsaw', 0, 'heads'
    print infer_many('is-fair', niters, burnin)
    
    for i in xrange(nheads):
      print '\nsaw', i+1, 'heads'
      observe(noisy(apply('coin'), noise_level), True)
      print infer_many('is-fair', niters, burnin)
  
  @unittest.skipIf(not test_beta_bernoulli, "skipping test_beta_bernoulli")
  def test_beta_bernoulli(self):
    print " \n TESTING BETA-BERNOULLI XRPs\n"
    
    print "beta_bernoulli_1"
    coin1 = beta_bernoulli_1()
    print [sample(apply(coin1)) for i in xrange(10)]
    print coin1.state
    
    print "beta_bernoulli_2"
    coin_2 = beta_bernoulli_2()
    print [sample(apply(coin_2)) for i in xrange(10)]
    print coin_2.state
  
  @unittest.skipIf(not test_CRP, "skipping test_CRP")
  def test_CRP(self):
    print " \n TESTING CHINESE RESTAURANT PROCESS XRP\n"
    
    print "CRP(1)"
    assume('crp1', CRP(1))
    print [sample(apply('crp1')) for i in xrange(10)]
    
    print "CRP(10)"
    assume('crp2', CRP(10))
    print [sample(apply('crp2')) for i in xrange(10)]
  
    assume('alpha', gamma(0.1, 20))
    assume('cluster-crp', CRP('alpha'))
    assume('get-cluster-mean', mem(function('cluster', gaussian(0, 10))))
    assume('get-cluster-variance', mem(function('cluster', gamma(0.1, 100))))
    assume('get-cluster', mem(function('id' , apply('cluster-crp'))))
    assume('get-cluster-model', mem(function('cluster', function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
    assume('get-datapoint', mem(function('id', gaussian(apply(apply('get-cluster-model', apply('get-cluster', 'id'))), 0.1))))
    assume('outer-noise', gamma(0.1, 10)) 
  
    print test_prior(1000, 100)
  
    #points = {} 
    #for i in xrange(100):
    #  print sample(apply('get-cluster', i)) , " : ", sample(apply('get-datapoint', i))
    #for i in xrange(1000):
    #  val = sample(apply('get-datapoint', i))
    #  if val in points:
    #    points[val] += 1
    #  else:
    #    points[val] = 1
    #plot_pdf(points, -50, 50, 0.1, name = 'graphs/crpmixturesample.png')
  
    assume('x', apply('get-datapoint', 0))
    observe(gaussian('x', let([('x', gaussian(0, 'outer-noise'))], var('x') * var('x'))), 2.3)
    observe(gaussian(apply('get-datapoint', 1), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), 2.2)
    observe(gaussian(apply('get-datapoint', 2), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), 1.9)
    observe(gaussian(apply('get-datapoint', 3), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), 2.0)
    observe(gaussian(apply('get-datapoint', 4), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), 2.1)
  
    niters, burnin = 100, 1000
  
    print sample('x')
    print sample('x')
    a = infer_many('x', 10, 1000)
    print sample('x')
    print sample('x')
    #print sample(apply('get-datapoint', 0))
    #print sample(apply('get-datapoint', 0))
    #print sample(apply('get-datapoint', 0))
    print a
    print format(get_pdf(a, -4, 4, .5), '%0.2f') 
  
    #print 'running', niters, 'times,', burnin, 'burnin'
  
    #t = time()
    #a = infer_many('expected-mean', niters, burnin)
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
    #print 'time taken', time() - t
  
  @unittest.skipIf(not test_bayes_nets, "skipping test_bayes_nets")
  def test_bayes_nets(self):
    print "\n TESTING INFERENCE ON CLOUDY/SPRINKLER\n"
    
    niters, burnin = 100, 100
  
    reset()
    assume('cloudy', bernoulli(0.5))
    assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5)))
    #print test_prior(1000, 100)
    #print infer_many('cloudy', 1000, 100)
    #print infer_many('sprinkler', 1000, 100)
    
    noise_level = .001
    sprinkler_ob = observe(noisy('sprinkler', noise_level), True)
    print infer_many('cloudy', niters, burnin)
    print 'Should be .833 False, .166 True'
    
    # TODO: remove
    return
  
    a = follow_prior(['cloudy', 'sprinkler'], 1000, 100)
    print [(x, count_up(a[x])) for x in a]
  
    forget(sprinkler_ob)
    print infer_many('cloudy', niters, burnin)
    print 'Should be .500 False, .500 True'
  
    print "\n TESTING BEACH NET\n"
    
    niters, burnin = 100, 100
  
    reset()
    assume('sunny', bernoulli(0.5))
    assume('weekend', bernoulli(0.285714))
    assume('beach', ifelse('weekend', ifelse('sunny', bernoulli(0.9), bernoulli(0.5)), \
                                      ifelse('sunny', bernoulli(0.3), bernoulli(0.1))))
    print test_prior(1000, 100)
    
    observe(noisy('weekend', noise_level), True)
    print infer_many('sunny', niters, burnin)
    print 'Should be .5 False, .5 True'
    
    observe(noisy('beach', noise_level), True)
    print infer_many('sunny', niters, burnin)
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
    print test_prior(1000, 100)
  
    print infer_many('alarm', niters, burnin)
    print 'Should be %f True' % pA
  
    mary_ob = observe(noisy('maryCalls', noise_level), True)
    print infer_many('johnCalls', niters, burnin)
    print 'Should be %f True' % pJgM
    forget(mary_ob)
  
    burglary_ob = observe(noisy(~var('burglary'), noise_level), True)
    print infer_many('johnCalls', niters, burnin)
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
    print test_prior(1000, 100)
  
    print infer_many('alarm', niters, burnin)
    print 'Should be %f True' % pA
  
    mary_ob = observe(noisy('maryCalls', noise_level), True)
    print infer_many('johnCalls', niters, burnin)
    print 'Should be %f True (BUT WONT BE)' % pJgM
    forget(mary_ob)
  
    burglary_ob = observe(noisy(~var('burglary'), noise_level), True)
    print infer_many('johnCalls', niters, burnin)
    print 'Should be %f True' % pJgnB
    forget(burglary_ob)
  
  @unittest.skipIf(not test_xor, "skipping test_xor")
  def test_xor(self):
    print "\n XOR TEST\n"
  
    reset()
   
    p = 0.6
    q = 0.4
    noise_level = .01
    assume('a', bernoulli(p)) 
    assume('b', bernoulli(q)) 
    assume('c', var('a') ^ var('b'))
    print test_prior(1000, 100)
  
    #print infer_many('a', 10000, 100) 
    #print 'should be 0.60 true'
    # should be True : p, False : 1 - p
  
    xor_ob = observe(noisy('c', noise_level), True) 
    print infer_many('a', 1000, 50) 
    print 'should be 0.69 true'
    # should be True : p(1-q)/(p(1-q)+(1-p)q), False : q(1-p)/(p(1-q) + q(1-p)) 
    # I believe this gets skewed because it has to pass through illegal states, and the noise values get rounded badly 
  
  @unittest.skipIf(not test_recursion, "skipping test_recursion")
  def test_recursion(self):
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
  
  @unittest.skipIf(not test_mem, "skipping test_mem")
  def test_mem(self):
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
  
  @unittest.skipIf(not test_geometric, "skipping test_geometric")
  def test_geometric(self):
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
    print test_prior(1000, 100)
  
    print "decay", globals.env.lookup('decay')
    print [sample(apply('geometric', 0)) for i in xrange(10)]
    observe(noisy(apply('geometric', 0) == timetodecay, .001), True)
    dist = infer_many('decay', niters, burnin)
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
  
  @unittest.skipIf(not test_DPmem, "skipping test_DPmem")
  def test_DPmem(self):
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
  
    a = infer_many(apply('get-datapoint', 0), 10, 1000)
    print sample(apply('get-datapoint', 0))
    print sample(apply('get-datapoint', 0))
    print sample(apply('get-datapoint', 0))
    print a
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
  
    #print 'running', niters, 'times,', burnin, 'burnin'
  
    #t = time()
    #a = infer_many('expected-mean', niters, burnin)
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
    #print 'time taken', time() - t
  
  @unittest.skipIf(not test_easy_mixture, "skipping test_easy_mixture")
  def test_easy_mixture(self):
    print " \n TESTING 1 COMPONENT MIXTURE\n"
  
    x = []
    y = []
  
    for i in range(0, 500, 100):
      reset()
      assume('get-cluster-mean', gaussian(0, 10))
      assume('get-cluster-variance', gamma(1, 10))
      assume('get-cluster-model', function([], gaussian('get-cluster-mean', 'get-cluster-variance')))
      assume('get-datapoint-2', mem(function('id', apply('get-cluster-model'))))
      assume('get-datapoint', mem(function('id', gaussian(apply('get-cluster-model'), 0.1))))
  
      points = [2.2, 2.0, 1.5, 2.1, 1.8, 1.9]
      print "points: " + str(points)
      for (idx, p) in enumerate(points):
        observe(gaussian(apply('get-datapoint-2', idx), 0.1), p)
  
      #assume('x', apply('get-datapoint', 0))
      #observe(gaussian('x', let([('y', gaussian(0, .1))], var('y') * var('y'))), point)
  
      avg_logpdf = 0
      num_repeats = 10
      for j in range(0, num_repeats):
        # start at prior, move i steps towards posterior
        a = infer_many('get-cluster-mean', 1, i)
  
        # read out inferred mean and sig of gaussian
        avg = sample('get-cluster-mean').val
        sig = sample('get-cluster-variance').val
  
        print "  mean: " + str(avg) + " +- " + str(sig)
  
        logpdf = 0
        for point in points:  
          logpdf += -((point - avg)/(sig + 0.0))**2
        logpdf /= float(len(points))
        print "  logpdf for trial " + str(j) + " iters " + str(i) + " : " + str(logpdf)
  
        avg_logpdf += logpdf
  
      print "total logpdf: " + str(avg_logpdf)
      avg_logpdf /= float(num_repeats)
      print "avg_logpdf: " + str(avg_logpdf)
  
      y.append(avg_logpdf) # log pdf at point
      x.append(i)
    plot(x, y, name = 'graphs/mixture1component.png')
    #print [sample('x') for i in xrange(10)]
  
    reset()
  
    print " \n TESTING 2 COMPONENT MIXTURE\n"
  
    assume('cluster-crp', function([], uniform(2)))
    assume('get-cluster-mean', function('cluster', gaussian(0, 10)))
    assume('get-cluster-variance', function('cluster', gamma(1, 10)))
    assume('get-cluster', function('id' , apply('cluster-crp')))
    assume('get-cluster-model', mem(function('cluster', function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
    assume('get-datapoint', mem(function('id', gaussian(apply(apply('get-cluster-model', apply('get-cluster', 'id'))), 0.1))))
  
    assume('x', apply('get-datapoint', 0))
    #observe(gaussian('x', let([('y', gaussian(0, .1))], var('y') * var('y'))), -2.3)
    #observe(gaussian(apply('get-datapoint', 1), let([('y', gaussian(0, .1))], var('y') * var('y'))), -2.2)
    #observe(gaussian(apply('get-datapoint', 2), let([('y', gaussian(0, .1))], var('y') * var('y'))), -1.9)
    #observe(gaussian(apply('get-datapoint', 3), let([('y', gaussian(0, .1))], var('y') * var('y'))), -2.0)
    #observe(gaussian(apply('get-datapoint', 4), let([('y', gaussian(0, .1))], var('y') * var('y'))), -2.1)
  
    #a = infer_many('x', 10, 1000)
    #print a
    #print [sample('x') for i in xrange(10)]

  @unittest.skipIf(True, "Always skip")
  def test():
    reset()
    print " \n TESTING BLAH\n"
    
    #print "description"
    #expr = beta_bernoulli_1()
    #print [sample(apply(coin_1)) for i in xrange(10)]
    
    print "description"
    assume('f', mem(let(('x', CRP(1)), function(['id'], apply('x')))))
    #for i in range(20):
    #  print sample(apply('f', i))
    assume('x', apply('f', 0))
    print test_prior(1000, 100)
  
    observe(noisy(apply('f',0) < 2222222222, 0.001), True)
    a = infer_many(apply('f',0), 10, 1000)
    print a
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    #print [sample('x') for i in xrange(10)]

if __name__ == '__main__':
  unittest.main()
