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

def test_coin():
  print " \n COIN TEST\n "
  
  assume('make-coin', function([], apply(function(['weight'], function([], bernoulli('weight'))), beta(1, 1))))
  print globals.env.lookup('make-coin')
  
  assume('my-coin', apply('make-coin'))
  
  print globals.env.lookup('my-coin')
  print "flips: ", [sample(apply('my-coin')) for i in xrange(10)]
  
  assume('my-coin-2', apply('make-coin'))
  print globals.env.lookup('my-coin-2')
  print "flips: ", [sample(apply('my-coin-2')) for i in xrange(10)]

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

def test_cloudy():
  print "\n TESTING INFERENCE\n"
  
  reset()
  assume('cloudy', bernoulli(0.5))
  
  print sample('cloudy')
  print sample('cloudy')
  
  assume('sprinkler', ifelse('cloudy', bernoulli(0.1), bernoulli(0.5)))
  
  observe('sprinkler', True)
  print infer_many('cloudy', 1000, 25)
  
  forget('sprinkler')
  print infer_many('cloudy', 1000, 25)

def test_xor():
  print "\n XOR TEST\n"

  reset()

  assume('a', bernoulli(0.8)) 
  assume('b', bernoulli(0.2)) 
  assume('c', (var('a') & ~var('b')) |(~var('a') & var('b'))) 

  observe('c', True) 
  print infer_many('a', 1000, 25) 

  forget('c') 
  print infer_many('a', 1000, 25) 

def test_mem():
  print "\n TESTING RECURSION, FACTORIAL\n" 
  reset() 
  
  factorial_expr = function(['x'], ifelse(var('x') == 0, 1, \
              var('x') * apply('factorial', var('x') - 1))) 
  assume('factorial', factorial_expr) 
  
  print "factorial" 
  print factorial_expr 
  print "factorial(5) =", sample(apply('factorial', 5)) 
  print "factorial(10) =", sample(apply('factorial', 10)) 

  print "\n MEM TEST\n" 
  print "\n TESTING RECURSION, FIBONACCI\n" 
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
  # Notice that mem'ed fibonacci doesn't recurse using itself.  It still calls fibonacci

  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"
  t = time()
  print "bad_mem_fibonacci(20) =", sample(apply('bad_mem_fibonacci', 20))
  print "      took", time() - t, "seconds"

  mem_fibonacci_expr = function(['x'], ifelse(var('x') <= 1, 1, \
                apply('mem_fibonacci', var('x') - 1) + apply('mem_fibonacci', var('x') - 2) )) 
  assume('mem_fibonacci', apply('mem_xrp', mem_fibonacci_expr)) 
  # Notice that mem'ed fibonacci doesn't recurse using itself.  It still calls fibonacci

  print "mem_fibonacci(20) =", sample(apply('mem_fibonacci', 20))
  print "      took", time() - t, "seconds"
  t = time()
  print "mem_fibonacci(20) =", sample(apply('mem_fibonacci', 20))
  print "      took", time() - t, "seconds"

test_expressions()
test_coin()
test_beta_bernoulli()
test_mem()
test_cloudy()
test_xor()

