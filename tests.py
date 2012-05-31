from directives import * 
from mem import *
from time import *
import matplotlib.pyplot as plot

def bernoulli_noise(expression, error):
  return bernoulli(ifelse(expression, 1, error))

def get_pdf(valuedict, start, end, bucketsize):
  numbuckets = int(math.floor((end - start) / bucketsize))
  density = [0] * numbuckets 
  cumulative = [0] * numbuckets 
  for value in valuedict:
    if not start <= value <= end:
      print 'value %s is not in the interval [%s, %s]' % (str(value), str(start), str(end))
      #assert False
      continue
    index = int(math.floor((value - start) / bucketsize))
    density[index] += valuedict[value]
  return density

def get_cdf(valuedict, start, end, bucketsize):
  density = get_pdf(valuedict, start, end, bucketsize)
  cumulative[0] = density[0]
  for i in range(1, len(cumulative)):
    cumulative[i] = cumulative[i-1] + density[i]
  plot.plot([start + i * bucketsize for i in range(numbuckets)], cumulative)
  return cumulative
  
def format(list, format):
  print [ format % x for x in list]

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
  niters, burnin = 100, 10

  print 'running', niters, 'times,', burnin, 'burnin'

  print '\nsaw', 0, 'heads'
  print follow_prior('is-fair', niters, burnin)
  
  for i in xrange(nheads):
    print '\nsaw', i+1, 'heads'
    observe(bernoulli_noise(apply('coin'), noise_level), True)
    print follow_prior('is-fair', niters, burnin)


def test_beta_bernoulli():
  print " \n TESTING BETA-BERNOULLI XRPs\n"
  
  print "beta_bernoulli_1"
  coin_1 = beta_bernoulli_1()
  print [sample(apply(coin_1)) for i in xrange(10)]
  print coin_1.state
  
  print "beta_bernoulli_2"
  coin_2 = beta_bernoulli_2()
  print [sample(apply(coin_2)) for i in xrange(10)]
  print coin_2.state

def test_bayes_nets():
  print "\n TESTING INFERENCE ON CLOUDY/SPRINKLER\n"
  
  reset()
  assume('cloudy', bernoulli(0.5))
  
  assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5)))
  
  noise_level = .001
  sprinkler_ob = observe(bernoulli_noise('sprinkler', noise_level), True)
  print follow_prior('cloudy', 1000, 100)
  print 'Should be .833 False, .166 True'
  
  forget(sprinkler_ob)
  print follow_prior('cloudy', 1000, 100)
  print 'Should be .500 False, .500 True'

  print "\n TESTING BEACH NET\n"
  
  reset()
  assume('sunny', bernoulli(0.5))
  assume('weekend', bernoulli(0.285714))
  assume('beach', ifelse('weekend', ifelse('sunny', bernoulli(0.9), bernoulli(0.5)), \
                                    ifelse('sunny', bernoulli(0.3), bernoulli(0.1))))
  
  observe(bernoulli_noise('weekend', noise_level), True)
  print follow_prior('sunny', 1000, 100)
  print 'Should be .5 False, .5 True'
  
  observe(bernoulli_noise('beach', noise_level), True)
  print follow_prior('sunny', 1000, 100)
  print 'Should be .357142857 False, .642857143 True'

  print "\n TESTING MODIFIED BURGLARY NET\n" # An example from AIMA
  reset()

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

  print follow_prior('alarm', 1000, 100)
  print 'Should be %f True' % pA

  mary_ob = observe(bernoulli_noise('maryCalls', noise_level), True)
  print follow_prior('johnCalls', 1000, 100)
  print 'Should be %f True' % pJgM
  forget(mary_ob)

  burglary_ob = observe(bernoulli_noise(~var('burglary'), noise_level), True)
  print follow_prior('johnCalls', 1000, 100)
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

  print follow_prior('alarm', 1000, 100)
  print 'Should be %f True' % pA

  mary_ob = observe(bernoulli_noise('maryCalls', noise_level), True)
  print follow_prior('johnCalls', 1000, 100)
  print 'Should be %f True' % pJgM
  forget(mary_ob)

  burglary_ob = observe(bernoulli_noise(~var('burglary'), noise_level), True)
  print follow_prior('johnCalls', 1000, 100)
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
  assume('c', (var('a') & ~var('b')) |(~var('a') & var('b'))) 

  #print follow_prior('a', 10000, 100) 
  #print 'should be 0.60 true'
  # should be True : p, False : 1 - p

  xor_ob = observe(bernoulli_noise('c', noise_level), True) 
  print follow_prior('a', 10000, 50) 
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
  print "factorial(10) =", sample(apply('factorial', 10)) 

def test_mem():
  print "\n MEM TEST, FIBONACCI\n" 
  reset() 
  
  fibonacci_expr = function('x', ifelse(var('x') <= 1, 1, \
                apply('fibonacci', var('x') - 1) + apply('fibonacci', var('x') - 2) )) 
  assume('fibonacci', fibonacci_expr) 
  
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
  assume('decay', beta(1, 1))
  #assume('decay', 0.5)
  #assume('decay', uniform(5))
  assume('geometric', function('x', ifelse(bernoulli('decay'), 'x', apply('geometric', var('x') + 1))))
  print "decay", globals.env.lookup('decay')
  print [sample(apply('geometric', 0)) for i in xrange(10)]
  observe(bernoulli_noise(apply('geometric', 0) == 10, .01), True)
  print get_pdf(follow_prior('decay', 100, 100), 0, 1, .1)

def test_DPmem():
  reset()
  print " \n TESTING DPMem\n"

  """DEFINITION OF DP"""
  sticks_expr = mem(function('j', beta(1, 'concentration2')))
  atoms_expr = mem(function('j', apply('basemeasure2')))

  loop_body_expr = function('j', ifelse( bernoulli(apply('sticks', 'j')), apply('atoms', 'j'), apply(apply('loophelper', ['concentration2', 'basemeasure2']), var('j') + 1))) 
  loop_expr = apply(  function(['sticks', 'atoms'], loop_body_expr), [sticks_expr , atoms_expr])
  assume('loophelper', function(['concentration2', 'basemeasure2'], loop_expr))
  assume( 'DP', function(['concentration', 'basemeasure'], apply(apply('loophelper', ['concentration', 'basemeasure']), 1)))

  """DEFINITION OF DPMEM"""
  restaurants_expr = mem( function('args', apply('DP', ['alpha', function([], apply('proc', 'args'))])))
  assume('DPmem', function(['alpha', 'proc'], function('args', apply(restaurants_expr, 'args'))))


  """TESTING DPMEM"""

  concentration = 1 # when close to 0, just mem.  when close to infinity, sample 
  assume('DPmemflip', apply('DPmem', [concentration, function(['x'], bernoulli(0.5))]))
  print [sample(apply('DPmemflip', 5)) for i in xrange(10)]

  print "\n TESTING GAUSSIAN MIXTURE MODEL\n"
  assume('concentration', gaussian(1, 0.2)) # use vague-gamma? 
  assume('expected-mean', gaussian(0, 1))
  assume('expected-variance', gaussian(0, 1))
  assume('gen-cluster-mean', gaussian(0, 1))
  assume('get-datapoint', mem( function(['id'], gaussian('gen-cluster-mean', 1.0))))
  assume('outer-noise', gaussian(1, 0.2)) # use vague-gamma?

  observe(gaussian(apply('get-datapoint', 0), 'outer-noise'), 1.3)
  observe(gaussian(apply('get-datapoint', 0), 'outer-noise'), 1.2)

  t = time()
  print format(get_pdf(follow_prior('expected-mean', 100, 30), -4, 4, .5), '%0.2f') 
  print 'time taken', time() - t

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
  
#test_expressions()
#test_recursion()
#test_beta_bernoulli()

#test_mem()

#test_bayes_nets() 

#test_xor()  # needs like 500 to mix 

test_tricky() 
#test_geometric()   
#test_DPmem()

