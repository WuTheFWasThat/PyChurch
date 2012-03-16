import random
import warnings

def chapel_infer(variable, niter = 1000, burnin = 100):
  if variable.__class__.__name__ != 'Random_Variable':
    warnings.warn('Attempting to infer something which isn\'t a random variable.')
    return variable

  dict = {}
  for n in xrange(niter):
    # re-draw from prior
    for var in chapel_stack:
      if var not in chapel_obs:
        var.sample()
    for t in xrange(burnin):
      i = random.randint(0, len(chapel_stack) -1)
      var = chapel_stack[i]
      if not var.observed:
        oldp = chapel_prob()
        oldval = var.getval()
        var.sample()
        if random.random() + (chapel_prob() / oldp) < 1:
          var.setval(oldval) 
    flag = True
    for var in chapel_obs:
      obsval = var.getval()
      if var in chapel_stack and var.getval() != obsval:
        var.setval(obsval)
        flag = False
        break
    if flag:
      val = variable.getval()
      if val in dict:
        dict[val] += 1
      else:
        dict[val] = 1

  z = sum([dict[val] for val in dict])
  for val in dict:
    dict[val] = dict[val] / (z + 0.0) 
  return dict 
      
# A table which records all random choices made
chapel_obs = []
chapel_stack = []

def chapel_prob():
  ans = 1
  for var in chapel_stack:
    ans *= var.prob()
  return ans

def chapel_flip(p):
  var = Random_Variable('flip', p)
  chapel_stack.append(var)
  return var

def chapel_unif(n):
  var = Random_Variable('uniform', n)
  chapel_stack.append(var)
  return var

def chapel_if(ifvar, p, q):
  var = Random_Variable('if', [ifvar, [p, q]])
  chapel_stack.append(var)
  return var

def chapel_ifp(ifvar, falsevar, truevar):
  var = Random_Variable('switch', [ifvar, [truevar, falsevar]])
  chapel_stack.append(var)
  return var

def chapel_switch(switchvar, array):
  var = Random_Variable('switch', [switchvar, array])
  return var

def forget(var):
  return var.forget()

# Class representing random variables
class Random_Variable:

  # Initializes a random variable, taking in a type string, and a list of other parameter arguments 
  def __init__(self, type, args):
    self.create(type, args)

  # Sets parameters of random variable, taking a type string, and a list of other parameter arguments
  def create(self, type, args):
    self.type = type
    self.observed = False
    self.children = []
    if type == 'flip':
      if not 0 <= args <= 1: 
        try:
          raise InputError(args, 'The probability must be a float between 0 and 1')
        except InputError as e:
          print e.msg
      else:
        self.p = args
    elif type == 'uniform':
      self.n = args
    elif type == 'constant':
      self.v = args
    elif self.type == 'switch':
      self.index = args[0]
      self.children = args[1]
      self.n = len(self.children)
    elif self.type == 'if':
      self.index = args[0]
      self.p = args[1][0]
      self.q = args[1][1]
    else:
      self.op = args[0]
      self.children = args[1]
    self.val = self.sample() 

  # Draws a sample value (without re-sampling other values), and sets it
  def sample(self):
    if self.observed:
      print 'This variable has been observed.  It must first be forgotten'
      return self.val 
    if self.type == 'flip':
      if random.random() < self.p:
        self.val = True  
      else:
        self.val = False
    elif self.type == 'uniform':
      self.val = random.randint(0, self.n-1)
    elif self.type == 'constant':
      self.val = self.v
    elif self.type == 'switch':
      i = self.index.getval()
      self.el = self.children[i]
      self.val = self.el.sample()
    elif self.type == 'if':
      if self.index.getval():
        if random.random() < self.p:
          self.val = True  
        else:
          self.val = False
      else:
        if random.random() < self.q:
          self.val = True  
        else:
          self.val = False
    else:
      self.val = self.op([x.getval() for x in self.children])
    return self.val

  # Resets a value to some particular value
  def setval(self, value):
    if self.observed:
      print 'Can\'t set observed variable.'
    if self.type == 'switch':
      self.el = self.children[self.index.getval()]
      self.el.setval(value)
    self.val = value 
    return self.val

  # Gets the value, sampling if there is none yet
  def getval(self):
    if self.val is None:
      self.val = self.sample()
    if self.type == 'switch':
      i = self.index.getval()
      self.el = self.children[i]
      self.val = self.el.getval()
    return self.val

  # Observes a value 
  def observe(self, value):
    if self.type == 'flip':
      if type(value).__name__ != 'bool': 
        print "Observation inconsistent with type: %s." % (self.type)
    elif self.type == 'uniform':
      if type(value).__name__ != 'int': 
        print "Observation inconsistent with type: %s." % (self.type)
      elif value >= self.n or value < 0: 
        print "Observation inconsistent with domain: [0, %d]." % (self.n - 1)
    elif self.type == 'constant':
      warnings.warn('Attempting to observe a constant.')
      return
    elif self.type == 'switch':
    #   WANT TO DO THIS, BUT THERE IS PROBLEM WITH INFERENCE, THEN
      for var in self.children:
        var.observe(value)
    elif self.type == 'if':
      pass
    chapel_obs.append(self)
    self.observed = True
    self.val = value
    return

  # Forgets the current value
  def forget(self):
    if self.type == 'switch':
      for var in self.children:
        var.forget()
    # MUST BE CAREFUL WITH REMOVES!!
    chapel_obs.remove(self)
    self.observed = False 
    self.val = None
    return

  # Returns the probability of this particular sampling
  # Makes (often wrong) assumptions about independence 
  def prob(self):
    self.getval()
    if self.type == 'flip':
      if self.val:
        return self.p
      else:
        return 1.0 - self.p
    elif self.type == 'uniform':
      return (1.0 / self.n)
    elif self.type == 'constant':
      return 1.0
    elif self.type == 'switch':
      self.el = self.children[self.index.getval()]
      if not self.val == self.el.val:
        warnings.warn('Inconsistent values.')
      return self.el.prob()
    elif self.type == 'if':
      if self.index.getval():
        if self.val:
          return self.p
        else:
          return 1.0 - self.p
      else:
        if self.val:
          return self.q
        else:
          return 1.0 - self.q
    else:
      return 1.0
      #return reduce(lambda x, y : x * y, [child.prob() for child in self.children])

  def __str__(self):
    return '%s [prob = %f]' % (str(self.val), self.prob())

  def __repr__(self):
    return '<Random_Variable of type %s with value %s>' % (self.type, str(self.val))

  def __nonzero__(self):
    return self.val

  def __cmp__(self, other):
    if other.__class__.__name__ == 'Random_Variable':
      if (self.val == other.val):
        return 0
      elif (self.val > other.val):
        return 1
      else:
        return -1
    else:
      if (self.val == other):
        return 0
      elif (self.val > other):
        return 1
      else:
        return -1

  # Performs a general operation 
  def operate(self, op, other = None):
    if other is None:
      return Random_Variable('op', [op, [self]]) 
    elif other.__class__.__name__ == 'Random_Variable':
      return Random_Variable('op', [op, [self, other]]) 
    else:
      other_variable = Random_Variable('constant', other) 
      return Random_Variable('op', [op, [self, other_variable]]) 

  def __add__(self, other):
    return self.operate(lambda x : x[0] + x[1], other)
  def __sub__(self, other):
    return self.operate(lambda x : x[0] - x[1], other)
  def __mul__(self, other):
    return self.operate(lambda x : x[0] * x[1], other)
  def __div__(self, other): 
    return self.operate(lambda x : x[0] / x[1], other)
  def __truediv__(self, other): 
    return self.operate(lambda x : x[0] / x[1], other)
  def __floordiv__(self, other): 
    return self.operate(lambda x : x[0] // x[1], other)
  def __mod__(self, other): 
    return self.operate(lambda x : x[0] % x[1], other)
  def __divmod__(self, other): 
    return self.operate(lambda x : divmod(x[0], x[1]), other)
  def __pow__(self, other): 
    return self.operate(lambda x : x[0] ** x[1], other)
  def __lshift__(self, other): 
    return self.operate(lambda x : x[0] << x[1], other)
  def __rshift__(self, other): 
    return self.operate(lambda x : x[0] >> x[1], other)
  def __and__(self, other): 
    return self.operate(lambda x : x[0] & x[1], other)
  def __xor__(self, other): 
    return self.operate(lambda x : x[0] ^ x[1], other)
  def __or__(self, other): 
    return self.operate(lambda x : x[0] | x[1], other)
  def __radd__(self, other):
    return self.operate(lambda x : x[1] + x[0], other)
  def __rsub__(self, other):
    return self.operate(lambda x : x[1] - x[0], other)
  def __rmul__(self, other):
    return self.operate(lambda x : x[1] * x[0], other)
  def __rdiv__(self, other): 
    return self.operate(lambda x : x[1] / x[0], other)
  def __rtruediv__(self, other): 
    return self.operate(lambda x : x[1] / x[0], other)
  def __rfloordiv__(self, other): 
    return self.operate(lambda x : x[1] // x[0], other)
  def __rmod__(self, other): 
    return self.operate(lambda x : x[1] % x[0], other)
  def __rdivmod__(self, other): 
    return self.operate(lambda x : divmod(x[1], x[0]), other)
  def __rpow__(self, other): 
    return self.operate(lambda x : x[1] ** x[0], other)
  def __rlshift__(self, other): 
    return self.operate(lambda x : x[1] << x[0], other)
  def __rrshift__(self, other): 
    return self.operate(lambda x : x[1] >> x[0], other)
  def __rand__(self, other): 
    return self.operate(lambda x : x[1] & x[0], other)
  def __rxor__(self, other): 
    return self.operate(lambda x : x[1] ^ x[0], other)
  def __ror__(self, other): 
    return self.operate(lambda x : x[1] | x[0], other)
  def __neg__(self): 
    return self.operate(lambda x : -x[0])
  def __pos__(self): 
    return self.operate(lambda x : +x[0])
  def __abs__(self): 
    return self.operate(lambda x : abs(x[0]))
  def __invert__(self): 
    return self.operate(lambda x : ~x[0])
  def __complex__(self): 
    return self.operate(lambda x : complex(x[0]))
  def __int__(self): 
    return self.operate(lambda x : int(x[0]))
  def __long__(self): 
    return self.operate(lambda x : long(x[0]))
  def __float__(self): 
    return self.operate(lambda x : float(x[0]))

"""
a = chapel_flip(.99)
b = chapel_unif(4)
c = chapel_unif(4)

print "a, b, c = " + str( a),str( b), str(c)
print "a + b = " + str(a + b)
print "c - b = " + str(c - b)
print "(a + b) * c = " + str((a + b) * c)
print "(a <= b) = " + str((a <= b))
print "(a < 4) = " + str((a < 4))
print "(a - 4) = " + str((a - 4))
print "(4- a) = " + str((4-a))
print "(4- a) << 3 = " + str((4-a) << 3)
print "4 << (4- a) = " + str(4 << (4-a) )
"""

cloudy = chapel_flip(0.5)

print cloudy.sample()
print cloudy
print cloudy.sample()
print cloudy

#sprinkler = chapel_ifp(cloudy, Random_Variable('flip', 0.1), Random_Variable('flip',0.5)) 
sprinkler = chapel_if(cloudy, 0.1, 0.5) 

cloudy.setval(True)
sprinkler.setval(True)
print '\nT, T'
print chapel_prob()
cloudy.setval(True)
sprinkler.setval(False)
print 'T, F'
print chapel_prob()
cloudy.setval(False)
sprinkler.setval(True)
print 'F, T'
print chapel_prob()
cloudy.setval(False)
sprinkler.setval(False)
print 'F, F'
print chapel_prob()


print sprinkler


sprinkler.observe(True)

print chapel_obs

print chapel_infer(cloudy)

sprinkler.forget()

print chapel_stack

print chapel_infer(cloudy)
