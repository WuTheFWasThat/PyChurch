from utils.infertools import * 
from time import *

import unittest

test_expressions = True
test_recursion = True
test_mem = True

test_HMM = True
test_bayes_nets = True

test_xor = False 

test_tricky  = False 

# something wrong with this test
test_geometric = False

test_DPmem = False
test_CRP = False

test_easy_mixture = False

running_main = False

""" TESTS """

class TestDirectives(unittest.TestCase):
  def setUp(self):
    reset()

  @unittest.skipIf(not test_expressions, "skipping test_expressions")
  def test_expressions(self):
  
    f = function(['x','y','z'], ifelse(var('x'), var('y'), var('z')))
    self.assertTrue(sample(f).type == 'procedure')
    
    g = function(['x', 'z'], apply(f, [var('x'), num_expr(0), var('z')] ))
    self.assertTrue(sample(g).type == 'procedure')
    
    a = bernoulli(num_expr(0.5)) 
    #d = count_up([resample(a).num for i in range(1000)])
    #self.assertTrue(d[True] + d[False] == 1000)
    #self.assertTrue(450 < d[True] < 550)
    
    x = apply(g, [a, uniform(num_expr(22))])
    b = ifelse(bernoulli(num_expr(0.2)), beta(num_expr(3),num_expr(4)), beta(num_expr(4),num_expr(3)))
    c = (~bernoulli(num_expr(0.3)) & bernoulli(num_expr(0.4))) | bernoulli(b)
    d = function(['x'], ('apply', f, [a,c,var('x')]))
    e = apply( d, [b])
  
    # Testing closure
    f = function(['x', 'y'], apply(var('x'), [var('y')]))
    g = function(['x'], var('x') + num_expr(1))
    self.assertTrue(sample(apply(f, [g, num_expr(21)])) == NumValue(22))

    assume('f', f)
    assume('g', g)
    a = let([('b', num_expr(1))], var('b') + num_expr(3))
    self.assertTrue(sample(a) == NumValue(4))

    b = let([('c', num_expr(21)), ('d', var('f'))], apply(var('d'), [var('g'), var('c')]))
    self.assertTrue(sample(b) == NumValue(22))


  @unittest.skipIf(not test_tricky, "skipping test_tricky")
  def test_tricky(self):
    noise_level = .01
  
    assume('make-coin', function([], apply(function(['weight'], function([], bernoulli(var('weight')))), beta(num_expr(1), num_expr(1)))))
  
    assume('tricky-coin', apply(var('make-coin')))
    assume('tricky-coin2', apply(var('make-coin')))
  
    assume('fair-coin', function([], bernoulli(num_expr(0.5))))
  
    assume('is-fair', bernoulli(num_expr(0.5)))
    assume('coin', ifelse(var('is-fair'), var('fair-coin'), var('tricky-coin'))) 

    d = test_prior(1000, 10)
    print d
    #self.assertTrue(test_prior_bool(d, 'is-fair') < 0.05)
  
    ## EXTENSIVE TEST

    nheads = 2
    niters, burnin = 1000, 10
  
    print infer_many(var('is-fair'), niters, burnin)
    
    for i in range(nheads):
      print '\nsaw', i+1, 'heads'
      observe(noisy(apply(var('coin')), noise_level), BoolValue(True))
      print infer_many(var('is-fair'), niters, burnin)
  
  @unittest.skipIf(not test_CRP, "skipping test_CRP")
  def test_CRP(self):
    print " \n TESTING CHINESE RESTAURANT PROCESS XRP\n"
    
    print "CRP(1)"
    assume('crp1', CRP(1))
    print [sample(apply('crp1')) for i in range(10)]
    
    print "CRP(10)"
    assume('crp2', CRP(10))
    print [sample(apply('crp2')) for i in range(10)]
  
    assume('alpha', gamma(0.1, 20))
    assume('cluster-crp', CRP('alpha'))
    assume('get-cluster-mean', mem(function(['cluster'], gaussian(0, 10))))
    assume('get-cluster-variance', mem(function(['cluster'], gamma(0.1, 100))))
    assume('get-cluster', mem(function(['id'] , apply('cluster-crp'))))
    assume('get-cluster-model', mem(function(['cluster'], function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
    assume('get-datapoint', mem(function(['id'], gaussian(apply(apply('get-cluster-model', apply('get-cluster', 'id'))), 0.1))))
    assume('outer-noise', gamma(0.1, 10)) 
  
    print test_prior(1000, 100)
  
    #points = {} 
    #for i in range(100):
    #  print sample(apply('get-cluster', i)) , " : ", sample(apply('get-datapoint', i))
    #for i in range(1000):
    #  val = sample(apply('get-datapoint', i))
    #  if val in points:
    #    points[val] += 1
    #  else:
    #    points[val] = 1
    #plot_pdf(points, -50, 50, 0.1, name = 'graphs/crpmixturesample.png')
  
    assume('x', apply('get-datapoint', 0))
    observe(gaussian('x', let([('x', gaussian(num_expr(0), var('outer-noise')))], var('x') * var('x'))), NumValue(2.3))
    observe(gaussian(apply('get-datapoint', 1), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), NumValue(2.2))
    observe(gaussian(apply('get-datapoint', 2), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), NumValue(1.9))
    observe(gaussian(apply('get-datapoint', 3), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), NumValue(2.0))
    observe(gaussian(apply('get-datapoint', 4), let([('y', gaussian(0, 'outer-noise'))], var('y') * var('y'))), NumValue(2.1))
  
    niters, burnin = 100, 1000
  
    print sample('x')
    print sample('x')
    a = infer_many(var('x'), 10, 1000)
    print sample('x')
    print sample('x')
    #print sample(apply('get-datapoint', 0))
    #print sample(apply('get-datapoint', 0))
    #print sample(apply('get-datapoint', 0))
    print a
    print format(get_pdf(a, -4, 4, .5), '%0.2f') 
  
    #print 'running', niters, 'times,', burnin, 'burnin'
  
    #t = time()
    #a = infer_many(var('expected-mean'), niters, burnin)
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
    #print 'time taken', time() - t
  
  @unittest.skipIf(not test_HMM, "skipping test_HMM")
  def test_HMM(self):
    n = 5
    t = 20

    assume('dirichlet', xrp(dirichlet_no_args_XRP([1]*n)))
    assume('get-column', mem(function(['i'], apply(var('dirichlet'), []))))
    assume('get-next-state', function(['i'], 
                             let([('loop', \
                                  function(['v', 'j'], \
                                           let([('w', apply(apply(var('get-column'), [var('i')]), [var('j')]))],
                                            ifelse(var('v') < var('w'), var('j'), apply(var('loop'), [var('v') - var('w'), var('j') + num_expr(1)]))))) \
                                 ], \
                                 apply(var('loop'), [uniform(), num_expr(0)])))) 
    assume('state', mem(function(['i'],
                                 ifelse(var('i') == num_expr(0), num_expr(0), apply(var('get-next-state'), [apply(var('state'), [var('i') - num_expr(1)])])))))
  
    assume('start-state', apply(var('state'), [num_expr(0)]))
    assume('second-state', apply(var('state'), [num_expr(t)]))

    print sample(var('second-state'))

    print test_prior(1000, 10)
  

  @unittest.skipIf(not test_bayes_nets, "skipping test_bayes_nets")
  def test_bayes_nets(self):
    print "\n TESTING INFERENCE ON CLOUDY/SPRINKLER\n"
    
    niters, burnin = 1000, 10
    #niters, burnin = 10, 10

    rrandom.random.seed(22342)
  
    assume('cloudy', bernoulli(num_expr(0.5)))
    assume('sprinkler', ifelse(var('cloudy'), bernoulli(num_expr(0.1)), bernoulli(num_expr(0.5))))
    #d = test_prior(niters, burnin)
    #self.assertTrue(test_prior_bool(d, 'cloudy') < 0.1)
    #self.assertTrue(test_prior_bool(d, 'sprinkler') < 0.1)
    print infer_many(var('cloudy'), niters, burnin)
    print 'Should be .5 False, .5 True'
    print infer_many(var('sprinkler'), niters, burnin)
    print 'Should be .7 False, .3 True'
    
    noise_level = .01
    sprinkler_ob = observe(noisy(var('sprinkler'), noise_level), BoolValue(True))
    d = infer_many(var('cloudy'), niters, burnin)
    print d
    #self.assertTrue(  abs(d['cloudy'][False] / (niters + 0.0) - 5 / 6.0) < 0.1)
    #self.assertTrue(test_prior_bool(d, 'sprinkler') < 0.1)
    print 'Should be .833 False, .166 True'
    print infer_many(var('sprinkler'), niters, burnin)
    print 'Should be 0 False, 1 True'
    
    #a = follow_prior(['cloudy', 'sprinkler'], 1000, 100, timer = False)
    #print [(x, count_up(a[x])) for x in a]
  
    forget(sprinkler_ob)
    print infer_many(var('cloudy'), niters, burnin)
    print 'Should be .500 False, .500 True'
  
    #print "\n TESTING BEACH NET\n"
    
    niters, burnin = 1000, 50
    #niters, burnin = 10, 5
  
    reset()
    assume('sunny', bernoulli(num_expr(0.5)))
    assume('weekend', bernoulli(num_expr(0.285714)))
    #assume('beach', bernoulli(ifelse('weekend', ifelse('sunny', 0.9, 0.5), \
    #                                            ifelse('sunny', 0.3, 0.1))))

    #assume('beach', ifelse('weekend', bernoulli(ifelse('sunny', 0.9, 0.5)), \
    #                                  bernoulli(ifelse('sunny', 0.3, 0.1))))

    assume('beach', ifelse(var('weekend'), ifelse(var('sunny'), bernoulli(num_expr(0.9)), bernoulli(num_expr(0.5))), \
                                           ifelse(var('sunny'), bernoulli(num_expr(0.3)), bernoulli(num_expr(0.1)))))
    #  this mixes poorly sometimes because the inactive branch gets stuck

    #print test_prior(1000, 100)
    
    observe(noisy(var('weekend'), noise_level), BoolValue(True))
    print infer_many(var('sunny'), niters, burnin)
    print 'Should be .5 False, .5 True'
    
    observe(noisy(var('beach'), noise_level), BoolValue(True))
    print infer_many(var('sunny'), niters, burnin)
    print 'Should be .357142857 False, .642857143 True'

    #print "\n TESTING BURGLARY NET\n" # An example from AIMA
  
    #pB = 0.001
    #pE = 0.002
    #pAgBE = 0.95
    #pAgBnE = 0.94
    #pAgnBE = 0.29
    #pAgnBnE = 0.001
    #pJgA = 0.9
    #pJgnA = 0.05
    #pMgA = 0.7
    #pMgnA = 0.01
    #
    #pA = pB * pE * pAgBE + (1-pB) * pE * pAgnBE + pB * (1 - pE) * pAgBnE + (1-pB) * (1-pE) * pAgnBnE
    #
    #pJ = pA * pJgA + (1 - pA) * pJgnA
    #
    #pAgnB = (pE * pAgnBE + (1 - pE) * pAgnBnE) / (1 - pB)
    #pJgnB = pJgA * pAgnB + pJgnA * (1 - pAgnB) 
    #
    #pAgM = pMgA * pA / (pMgA * pA + pMgnA * (1 - pA))
    #pJgM = pAgM * pJgA + (1 - pAgM) * pJgnA
    #
    #pJnB = pJgnB * (1 - pB)

    print "\n TESTING MODIFIED BURGLARY NET\n" # An example from AIMA
    reset()
  
    niters, burnin = 1000, 100
    #niters, burnin = 10, 10
  
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
    
    assume('burglary', bernoulli(num_expr(pB)))
    assume('earthquake', bernoulli(num_expr(pE)))
    assume('alarm', ifelse(var('burglary'), ifelse(var('earthquake'), bernoulli(num_expr(pAgBE)), bernoulli(num_expr(pAgBnE))), \
                                            ifelse(var('earthquake'), bernoulli(num_expr(pAgnBE)), bernoulli(num_expr(pAgnBnE)))))
  
    assume('johnCalls', ifelse(var('alarm'),  bernoulli(num_expr(pJgA)), bernoulli(num_expr(pJgnA))))
    assume('maryCalls', ifelse(var('alarm'),  bernoulli(num_expr(pMgA)), bernoulli(num_expr(pMgnA))))
    print test_prior(1000, 100, timer = False)
  
    print infer_many(var('alarm'), niters, burnin)
    print 'Should be %f True' % pA
  
    mary_ob = observe(noisy(var('maryCalls'), noise_level), BoolValue(True))
    print infer_many(var('johnCalls'), niters, burnin)
    print 'Should be %f True' % pJgM
    forget(mary_ob)
  
    burglary_ob = observe(noisy(~var('burglary'), noise_level), BoolValue(True))
    print infer_many(var('johnCalls'), niters, burnin)
    print 'Should be %f True' % pJgnB
    forget(burglary_ob)
  
  
  @unittest.skipIf(not test_xor, "skipping test_xor")
  def test_xor(self):
    # needs like 500 to mix
    rrandom.random.seed(2222)
    p = 0.6
    q = 0.4
    noise_level = .01
    assume('a', bernoulli(num_expr(p))) 
    assume('b', bernoulli(num_expr(q))) 
    assume('c', var('a') ^ var('b'))

    #d = test_prior(1000, 100, timer = False)
    #print d
    #self.assertTrue(test_prior_bool(d, 'a') < 0.05)
    #self.assertTrue(test_prior_bool(d, 'b') < 0.05)
    #self.assertTrue(test_prior_bool(d, 'c') < 0.05)
  
    xor_ob = observe(noisy(var('c'), noise_level), BoolValue(True)) 
    print infer_many(var('a'), 1000, 500) 
    print 'should be 0.69 true'
    # should be True : p(1-q)/(p(1-q)+(1-p)q), False : q(1-p)/(p(1-q) + q(1-p)) 
    # I believe this gets skewed because it has to pass through illegal states, and the noise values get rounded badly 
  
  @unittest.skipIf(not test_recursion, "skipping test_recursion")
  def test_recursion(self):
    
    factorial_expr = function(['x'], ifelse(var('x') == num_expr(0), num_expr(1), \
                var('x') * apply(var('factorial'), [var('x') - num_expr(1)]))) 
    assume('factorial', factorial_expr) 
    
    self.assertTrue(sample(apply(var('factorial'), [num_expr(5)])).num == 120)
    self.assertTrue(sample(apply(var('factorial'), [num_expr(10)])).num == 3628800)
  
  @unittest.skipIf(not test_mem, "skipping test_mem")
  def test_mem(self):
    fibonacci_expr = function(['x'], ifelse(var('x') <= num_expr(1), num_expr(1), \
                  apply(var('fibonacci'), [var('x') - num_expr(1)]) + apply(var('fibonacci'), [var('x') - num_expr(2)]) )) 
    assume('fibonacci', fibonacci_expr) 
    
    t1 = time()

    self.assertTrue(sample(apply(var('fibonacci'), [num_expr(20)])).num == 10946)
    t1 = time() - t1

    assume('bad_mem_fibonacci', mem(var('fibonacci'))) 
  
    t2 = time()
    assume('bad_fib_20', apply(var('bad_mem_fibonacci'), [num_expr(20)]))
    t2 = time() - t2

    t3 = time()
    self.assertTrue(sample(var('bad_fib_20')).num == 10946)
    t3 = time() - t3

    mem_fibonacci_expr = function(['x'], ifelse(var('x') <= num_expr(1), num_expr(1), \
                  apply(var('mem_fibonacci'), [var('x') - num_expr(1)]) + apply(var('mem_fibonacci'), [var('x') - num_expr(2)]) )) 
    assume('mem_fibonacci', mem(mem_fibonacci_expr)) 
  
    t4 = time()
    self.assertTrue(sample(apply(var('mem_fibonacci'), [num_expr(20)])).num == 10946)
    t4 = time() - t4

    print t1, t2, t3, t4
    self.assertTrue(0.5 < (t1 / t2) < 2)
    self.assertTrue((t3 / t2) < .5)
    self.assertTrue((t4 / t2) < .1)
  
  @unittest.skipIf(not test_geometric, "skipping test_geometric")
  def test_geometric(self):
    a, b = 3, 2
    timetodecay = 1
    bucketsize = .01
  
    niters, burnin = 1000, 100 
  
    assume('decay', beta(num_expr(a), num_expr(b)))
    assume('geometric', function(['x'], ifelse(bernoulli(var('decay')), var('x'), apply(var('geometric'), [var('x') + num_expr(1)]))))
    assume('timetodecay', apply(var('geometric'), [num_expr(0)]))

    d = test_prior(1000, 100, timer = False)
    print d
    #self.assertTrue(test_prior_L0(d, 'decay', 0, 1, .01) < .1)
    #self.assertTrue(test_prior_L0(d, 'timetodecay', 0, 100, 1) < .1)

    # hmm... random walk systematically decays faster
  
    observe(noisy(var('timetodecay') == num_expr(timetodecay), .001), BoolValue(True))
    dist = infer_many(var('decay'), niters, burnin)
    #print dist 
    #print 'pdf:', get_pdf(dist, 0, 1, .1)
    #print 'cdf:', get_cdf(dist, 0, 1, .1)
  
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
  
    def count_distinct(ls):
      d = Set()
      dd = Set()
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
                    let([('sticks', mem(function(['j'], beta(1, 'concentration')))),
                         ('atoms',  mem(function(['j'], apply('basemeasure')))),
                         ('loop', \
                          function(['j'], \
                                   ifelse(bernoulli(apply('sticks', 'j')), \
                                          apply('atoms', 'j'), \
                                          apply('loop', var('j')+1)))) \
                        ], \
                        function([], apply('loop', 1))))) 
  
    print "TEST VERSION"
    assume('DPgaussian', apply('DP', [concentration, measure]))
    print 'DPGaussian = ', sample('DPgaussian')
    ls = [sample(apply('DPgaussian')) for i in range(10)]
    print ls
    print count_distinct(ls)
  
    """TESTING DP"""
    if simpletests:
      concentration = .1 # when close to 0, lots of repeat.  when close to infinity, many new sample 
      assume('DPgaussian', apply('DP', [concentration, function([], gaussian(0, 1))]))
      print [sample(apply('DPgaussian')) for i in range(10)]
  
      concentration = 10 # when close to 0, lots of repeat.  when close to infinity, many new sample 
      assume('DPgaussian', apply('DP', [concentration, function([], gaussian(0, 1))]))
      print [sample(apply('DPgaussian')) for i in range(10)]
  
    print " \n TESTING DPMem\n"
  
    """DEFINITION OF DPMEM"""
    # Only supports function with exactly one argument
    assume('DPmem', \
           function(['concentration', 'proc'], \
                    let([('restaurants', \
                          mem( function(['args'], apply('DP', ['concentration', function([], apply('proc', 'args'))]))))], \
                        function(['args'], apply('restaurants', 'args'))))) 
  
    """TESTING DPMEM"""
    concentration = 1 # when close to 0, just mem.  when close to infinity, sample 
    assume('DPmemflip', apply('DPmem', [concentration, function(['x'], gaussian(0, 1))]))
  
    print "\n TESTING GAUSSIAN MIXTURE MODEL\n"
    assume('expected-mean', gaussian(0, 5)) 
    assume('expected-variance', gamma(1, 2)) 
    assume('alpha', gamma(0.1, 10)) 
    assume('gen-cluster-mean', apply('DPmem', ['alpha', function(['x'], gaussian('expected-mean', 'expected-variance'))]))
    assume('get-datapoint', mem(function(['id'], gaussian(apply(apply('gen-cluster-mean', 222)), 0.1))))
    assume('noise-variance', gamma(0.01, 1))
  
  #  points = {} 
  #  for i in range(100):
  #    print sample(apply('get-datapoint', i))
  #  for i in range(1000):
  #    val = sample(apply('get-datapoint', i))
  #    if val in points:
  #      points[val] += 1
  #    else:
  #      points[val] = 1
  #  plot_pdf(points, -50, 50, 0.1, name = 'graphs/mixturesample.png')
  
    #assume('x', apply(var('get-datapoint'), num_expr(0)))
    #observe(gaussian('x', let([('x', gaussian(num_expr(0), var('outer-noise')))], var('x') * var('x'))), NumValue(2.3))
    #observe(gaussian(apply(var('get-datapoint'), num_expr(1)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.2))
    #observe(gaussian(apply(var('get-datapoint'), num_expr(2)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(1.9))
    #observe(gaussian(apply(var('get-datapoint'), num_expr(3)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.0))
    #observe(gaussian(apply(var('get-datapoint'), num_expr(4)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.1))

    observe(gaussian(apply(var('get-datapoint'), num_expr(0)), var('noise-variance')), NumValue(2.3))
    observe(gaussian(apply(var('get-datapoint'), num_expr(1)), var('noise-variance')), NumValue(2.2))
    observe(gaussian(apply(var('get-datapoint'), num_expr(2)), var('noise-variance')), NumValue(1.9))
    observe(gaussian(apply(var('get-datapoint'), num_expr(3)), var('noise-variance')), NumValue(2.0))
    observe(gaussian(apply(var('get-datapoint'), num_expr(4)), var('noise-variance')), NumValue(2.1))
  
    #niters, burnin = 100, 100
  
    a = infer_many(apply('get-datapoint', 0), 10, 1000)
    print sample(apply('get-datapoint', 0))
    print sample(apply('get-datapoint', 0))
    print sample(apply('get-datapoint', 0))
    print a
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
  
    #print 'running', niters, 'times,', burnin, 'burnin'
  
    #t = time()
    #a = infer_many(var('expected-mean'), niters, burnin)
    #print format(get_pdf(a, -4, 4, .5), '%0.2f') 
    #print 'time taken', time() - t
  
  @unittest.skipIf(not test_easy_mixture, "skipping test_easy_mixture")
  def test_easy_mixture(self):
  
    x = []
    y = []
  
    for i in range(0, 500, 100):
      reset()
      assume('get-cluster-mean', gaussian(0, 10))
      assume('get-cluster-variance', gamma(1, 10))
      assume('get-cluster-model', function([], gaussian('get-cluster-mean', 'get-cluster-variance')))
      assume('get-datapoint-2', mem(function(['id'], apply('get-cluster-model'))))
      assume('get-datapoint', mem(function(['id'], gaussian(apply('get-cluster-model'), 0.1))))
  
      points = [2.2, 2.0, 1.5, 2.1, 1.8, 1.9]
      print "points: " + str(points)
      for (idx, p) in enumerate(points):
        observe(gaussian(apply('get-datapoint-2', idx), 0.1), NumValue(p))
  
      #assume('x', apply(var('get-datapoint'), num_expr(0)))
      #observe(gaussian(var('x'), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.3))
      #observe(gaussian(apply(var('get-datapoint'), num_expr(1)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.2))
      #observe(gaussian(apply(var('get-datapoint'), num_expr(2)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(1.9))
      #observe(gaussian(apply(var('get-datapoint'), num_expr(3)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.0))
      #observe(gaussian(apply(var('get-datapoint'), num_expr(4)), let([('y', gaussian(num_expr(0), var('outer-noise')))], var('y') * var('y'))), NumValue(2.1))
  
      avg_logpdf = 0
      num_repeats = 10
      for j in range(0, num_repeats):
        # start at prior, move i steps towards posterior
        a = infer_many(var('get-cluster-mean'), 1, i)
  
        # read out inferred mean and sig of gaussian
        avg = sample('get-cluster-mean').num
        sig = sample('get-cluster-variance').num
  
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
    #print [sample('x') for i in range(10)]
  
    reset()
  
    print " \n TESTING 2 COMPONENT MIXTURE\n"
  
    assume('cluster-crp', function([], uniform(2)))
    assume('get-cluster-mean', function(['cluster'], gaussian(0, 10)))
    assume('get-cluster-variance', function(['cluster'], gamma(1, 10)))
    assume('get-cluster', function(['id'] , apply('cluster-crp')))
    assume('get-cluster-model', mem(function(['cluster'], function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
    assume('get-datapoint', mem(function(['id'], gaussian(apply(apply('get-cluster-model', apply('get-cluster', 'id'))), 0.1))))
  
    assume('x', apply('get-datapoint', 0))
    #observe(gaussian('x', let([('y', gaussian(0, .1))], var('y') * var('y'))), NumValue(-2.3))
    #observe(gaussian(apply('get-datapoint', 1), let([('y', gaussian(0, .1))], var('y') * var('y'))), NumValue(-2.2))
    #observe(gaussian(apply('get-datapoint', 2), let([('y', gaussian(0, .1))], var('y') * var('y'))), NumValue(-1.9))
    #observe(gaussian(apply('get-datapoint', 3), let([('y', gaussian(0, .1))], var('y') * var('y'))), NumValue(-2.0))
    #observe(gaussian(apply('get-datapoint', 4), let([('y', gaussian(0, .1))], var('y') * var('y'))), NumValue(-2.1))
  
    #a = infer_many(var('x'), 10, 1000)
    #print a
    #print [sample('x') for i in range(10)]

  @unittest.skipIf(True, "Always skip")
  def test():
    print " \n TESTING BLAH\n"
    
    #print "description"
    #expr = beta_bernoulli_1()
    #print [sample(apply(coin_1)) for i in range(10)]
    
    print "description"
    assume('f', mem(let(('x', CRP(1)), function(['id'], apply('x')))))
    #for i in range(20):
    #  print sample(apply('f', i))
    assume('x', apply('f', 0))
    print test_prior(1000, 100)
  
    observe(noisy(apply('f',0) < 2222222222, 0.001), BoolValue(True))
    a = infer_many(apply('f',0), 10, 1000)
    print a
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    print sample(apply('f', 0))
    #print [sample('x') for i in range(10)]

def run_HMM(t, s, niters = 100, burnin = 100, countup = True):
    reset()
    rrandom.random.seed(s)
    n = 5
    assume('dirichlet', xrp(dirichlet_no_args_XRP([1]*n)))
    assume('get-column', mem(function(['i'], apply(var('dirichlet'), []))))
    assume('get-next-state', function(['i'],
                             let([('loop', \
                                  function(['v', 'j'], \
                                           let([('w', apply(apply(var('get-column'), [var('i')]), [var('j')]))],
                                            ifelse(op('<', [var('v'), var('w')]), var('j'), apply(var('loop'), [op('-', [var('v'), var('w')]), op('+', [var('j'), nat_expr(1)])]))))) \
                                 ], \
                                 apply(var('loop'), [uniform(), nat_expr(0)]))))
    assume('state', mem(function(['i'],
                                 ifelse(var('i') == num_expr(0), num_expr(0), apply(var('get-next-state'), [apply(var('state'), [var('i') - nat_expr(1)])])))))
  
    assume('start-state', apply(var('state'), [num_expr(0)]))
    assume('last-state', apply(var('state'), [num_expr(t)]))
    #a = test_prior(niters, burnin, countup)
    print infer_many(var('last-state'), 100, 10)
    return a

def run_topic_model(docsize, s, niters = 1000, burnin = 100, countup = True):
    reset()
    rrandom.random.seed(s)
    ntopics = 5
    nwords = 20

    assume('topics-dirichlet', apply(var('make-symmetric-dirichlet'), [nat_expr(ntopics), nat_expr(1)]))
    assume('words-dirichlet', apply(var('make-symmetric-dirichlet'), [nat_expr(nwords), nat_expr(1)]))

    assume('get-topic-dist', apply(var('topics-dirichlet'), []))
    assume('get-topic-words-dist', apply(var('mem'), [function(['i'], apply(var('words-dirichlet'), []))]))
    assume('sample-dirichlet', function(['prob_array'],
                               let([('loop', 
                                    function(['v', 'i'], 
                                             let([('w', apply(var('prob_array'), [var('i')]))], 
                                              ifelse(op('<', [var('v'), var('w')]), var('i'), apply(var('loop'), [op('-', [var('v'), var('w')]), op('+', [var('i'), nat_expr(1)])])))))
                                   ], 
                                   apply(var('loop'), [uniform(), nat_expr(0)]))))
    assume('get-topic', apply(var('mem'), [function(['i'], apply(var('sample-dirichlet'), [var('get-topic-dist')]))]))
    assume('get-word', apply(var('mem'), [function(['i'], apply(var('sample-dirichlet'), [apply(var('get-topic-words-dist'), [apply(var('get-topic'), [var('i')])])]))]))

    for i in range(docsize):
      assume('get-word' + str(i), apply(var('get-word'), [nat_expr(i)])) 

    reset()
    assume('f', apply(var('mem'), [function([], apply(var('uniform'), [nat_expr(20)]))]))
    assume('e', apply(var('f'), []))

    a = test_prior(niters, burnin, countup, False)

    return a


def run_topic_model_half_collapsed(ntopics, s, niters = 1000, burnin = 100, countup = True):
    reset()
    random.seed(s)
    #ntopics = 5
    nwords = 20
    docsize = 5

    assume('numtopics', ('value', IntValue(ntopics)))
    assume('alpha', gamma(constant(NumValue(1.0)), constant(NumValue(1.0))))
    assume('topics-dirichlet', dirichlet(var('numtopics'), var('alpha')))
    assume('words-dirichlet', dirichlet(constant(IntValue(nwords)), constant(NumValue(1.0)))) #_no_args_XRP([1]*nwords))

    assume('get-topic-dist', apply(var('topics-dirichlet'), []))
    assume('get-topic-words-dist', mem(function(var('i'), apply(var('words-dirichlet'), []))))
    assume('get-topic', mem(function(var('i'), apply(var('get-topic-dist'), []))))
    assume('get-word', mem(function(var('i'), apply(apply(var('get-topic-words-dist'), [apply(var('get-topic'), [var('i')])]),[]))))

    for i in range(docsize):
      assume('word' + str(i), apply(var('get-word'), IntValue(i))) 

    a = test_prior(niters, burnin, countup)
    return a

def run_topic_model_collapsed(nwords, s, niters = 1000, burnin = 100, countup = True):
    reset()
    random.seed(s)
    docsize = 5
    ntopics = 5 
    #nwords = 20

    assume('numwords', nwords)
    assume('numtopics', ntopics)
    assume('alpha', gamma(1, 1))
    assume('topic-model', apply(make_topic_model_XRP(), ['numtopics', 'alpha', 'numwords', 1]))

    for i in range(docsize):
      assume('word' + str(i), apply('topic-model'))

    a = test_prior(niters, burnin, countup)
    return a

def run_mixture(n, s, niters = 1000, burnin = 100, countup = True):
    reset()
    rrandom.random.seed(s)

    assume('alpha', gamma(0.1, 20))
    assume('cluster-crp', CRP('alpha'))
    assume('get-cluster-mean', mem(function(['cluster'], gaussian(0, 10))))
    assume('get-cluster-variance', mem(function(['cluster'], gamma(0.1, 100))))
    assume('get-cluster', mem(function(['id'] , apply('cluster-crp'))))
    assume('get-cluster-model', mem(function(['cluster'], function([], gaussian(apply('get-cluster-mean', 'cluster'), apply('get-cluster-variance', 'cluster'))))))
    assume('get-datapoint', mem(function(['id'], gaussian(apply(apply('get-cluster-model', apply('get-cluster', 'id'))), 0.1))))

    for i in range(n):
      assume('point' + str(i), apply('get-datapoint', i))
    a = test_prior(niters, burnin, countup)
    return a

def run_mixture_uncollapsed(n, s):
    rrandom.random.seed(s)

    print "\n TESTING GAUSSIAN MIXTURE MODEL\n"
    assume('expected-mean', gaussian(num_expr(0), num_expr(5))) 
    assume('expected-variance', gamma(num_expr(1), num_expr(2))) 
    assume('alpha', gamma(num_expr(0.1), num_expr(10)))
    assume('gen-cluster-mean', apply(var('DPmem_uncollapsed'), [var('alpha'), function(['x'], gaussian(var('expected-mean'), [var('expected-variance')]))]))
    assume('get-datapoint', mem(function(['id'], gaussian(apply(apply(var('gen-cluster-mean'), [num_expr(222)]), []), num_expr(0.1)))))
    assume('noise-variance', gamma(num_expr(0.01), num_expr(1)))

    for i in range(n):
      assume('point' + str(i), apply('get-datapoint', i))
    a = infer_many(apply('get-datapoint', 0), 10, 1000)
    return a

def run_bayes_net(k, s, niters = 1000, burnin = 100, countup = True):
    reset()
    rrandom.random.seed(s)
    n = 50

    for i in range(n):
      assume('disease' + str(i), bernoulli(num_expr(0.2)))
    for j in range(n):
      causes = ['disease' + str(random.randbelow(n)) for i in range(k)]
      symptom_expression = bernoulli(ifelse(disjunction(causes), .8, .2))
      assume('symptom' + str(j), symptom_expression)

    a = test_prior(niters, burnin, countup)
    return a

if __name__ == '__main__':
  t = time()
  if running_main:
    unittest.main()
  else:
    a = run_topic_model(5, 222222, 100, 10)
    #a = run_HMM(5, 2223)
  
    #a = run_topic_model_uncollapsed(15, 222222)
    #a = run_mixture(15, 222222)
    #a = run_bayes_net(20, 222222)

    print a

    #sampletimes = a[0]['TIME']
    #print average(sampletimes)
    #print standard_deviation(sampletimes)
    #
    #followtimes = a[1]['TIME']
    #print average(followtimes)
    #print standard_deviation(followtimes)
    #print time() - t
