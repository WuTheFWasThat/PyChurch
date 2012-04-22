from directives import * 
from mem import *
from time import *

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
  
  d = function(['x'], ('apply', f, [a,c,'x']))
  print 'Sample of\n%s\n= %s\n' % (str(d), str(resample(d)))
  
  e = apply( d, b)
  print 'Some samples of\n%s:' % (str(e))
  print [resample(e) for i in xrange(10)]
  print

def test_tricky():
  print " \n COIN TEST\n "
  
  assume('make-coin', function([], apply(function(['weight'], function([], bernoulli('weight'))), beta(1, 1))))
  print globals.env.lookup('make-coin')
  
  assume('tricky-coin', apply('make-coin'))
  print globals.env.lookup('tricky-coin')
  print "flips: ", [sample(apply('tricky-coin')) for i in xrange(10)]
  
  #assume('my-coin-2', apply('make-coin'))
  #print globals.env.lookup('my-coin-2')
  #print "flips: ", [sample(apply('my-coin-2')) for i in xrange(10)]

  assume('fair-coin', function([], bernoulli(0.5)))
  print globals.env.lookup('fair-coin')
  print "flips: ", [sample(apply('fair-coin')) for i in xrange(10)]

  assume('is-fair', bernoulli(0.5))
  assume('coin', ifelse('is-fair', 'fair-coin', 'tricky-coin')) 

  for i in xrange(100):
    observe(apply('coin'), True)

  print follow_prior('is-fair', 100, 50)


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
  
  observe('sprinkler', True)
  print follow_prior('cloudy', 1000, 50)
  print 'Should be .833 False, .166 True'
  
  forget('sprinkler')
  print follow_prior('cloudy', 1000, 50)
  print 'Should be .500 False, .500 True'

  print "\n TESTING BEACH NET\n"
  
  reset()
  assume('sunny', bernoulli(0.5))
  assume('weekend', bernoulli(0.285714))
  assume('beach', ifelse('weekend', ifelse('sunny', bernoulli(0.9), bernoulli(0.5)), \
                                    ifelse('sunny', bernoulli(0.3), bernoulli(0.1))))
  
  observe('weekend', True)
  print follow_prior('sunny', 1000, 50)
  print 'Should be .5 False, .5 True'
  
  observe('beach', True)
  print follow_prior('sunny', 1000, 50)
  print 'Should be .357142857 False, .642857143 True'

  print "\n TESTING BURGLARY NET\n" # An example from AIMA
  reset()
  assume('burglary', bernoulli(0.001))
  assume('earthquake', bernoulli(0.002))
  assume('alarm', ifelse('burglary', ifelse('earthquake', bernoulli(0.95), bernoulli(0.94)), \
                                    ifelse('earthquake', bernoulli(0.29), bernoulli(0.001))))
  assume('johnCalls', ifelse('alarm',  bernoulli(0.90), bernoulli(0.05)))
  assume('maryCalls', ifelse('alarm',  bernoulli(0.70), bernoulli(0.01)))
  
  print follow_prior('alarm', 10000, 1)
  print 'Should be .9975 False, .0025 True'

  observe('maryCalls', True)
  print follow_prior('johnCalls', 1000, 50)
  print 'Should be .1775766 True'
  forget('maryCalls')

  observe('burglary', False)
  print follow_prior('johnCalls', 1000, 50)
  print 'Should be .95 False, .0513413 True'
  forget('burglary')

def test_xor():
  print "\n XOR TEST\n"

  reset()
 
  p = 0.6
  q = 0.4
  assume('a', bernoulli(p)) 
  assume('b', bernoulli(q)) 
  assume('c', (var('a') & ~var('b')) |(~var('a') & var('b'))) 

  observe('c', True) 
  print follow_prior('a', 1000, 50) 
  # should be True : p(1-q)/(p(1-q)+(1-p)q), False : q(1-p)/(p(1-q) + q(1-p)) 
  # I believe this gets skewed because it has to pass through illegal states, and the noise values get rounded badly 

  forget('c') 
  print follow_prior('a', 1000, 50) 
  # should be True : p, False : 1 - p

def test_recursion():
  print "\n TESTING RECURSION, FACTORIAL\n" 
  reset() 
  
  factorial_expr = function(['x'], ifelse(var('x') == 0, 1, \
              var('x') * apply('factorial', var('x') - 1))) 
  assume('factorial', factorial_expr) 
  
  print "factorial" 
  print factorial_expr 
  print "factorial(5) =", sample(apply('factorial', 5)) 
  print "factorial(10) =", sample(apply('factorial', 10)) 

def test_mem():
  print "\n MEM TEST, FIBONACCI\n" 
  reset() 
  
  fibonacci_expr = function(['x'], ifelse(var('x') <= 1, 1, \
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

  assume('mem_xrp', mem_XRP()) 
  assume('bad_mem_fibonacci', apply('mem_xrp', 'fibonacci')) 
  # Notice that this mem'ed fibonacci doesn't recurse using itself.  It still calls fibonacci

  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"
  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"

  mem_fibonacci_expr = function(['x'], ifelse(var('x') <= 1, 1, \
                apply('mem_fibonacci', var('x') - 1) + apply('mem_fibonacci', var('x') - 2) )) 
  assume('mem_fibonacci', apply('mem_xrp', mem_fibonacci_expr)) 

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
  assume('geometric', function(['x'], ifelse(bernoulli('decay'), 'x', apply('geometric', var('x') + 1))))
  print "decay", globals.env.lookup('decay')
  print [sample(apply('geometric', 0)) for i in xrange(10)]
  observe(apply('geometric', 0), 3)
  print follow_prior('decay', 100, 25)

def test():
  reset()
  print " \n TESTING BLAH\n"
  
  print "description"
  expr = beta_bernoulli_1()
  print [sample(apply(coin_1)) for i in xrange(10)]
  
#test_expressions()
#test_recursion()
#test_beta_bernoulli()

test_bayes_nets()
test_xor()
test_tricky()
test_geometric()
test_mem()

