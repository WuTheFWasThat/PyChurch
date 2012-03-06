import random
import warnings

def infer(variable, niter = 1000, burnin = 100):
  if variable.__class__.__name__ != 'Random_Variable':
    warnings.warn('Attempting to infer something which isn\'t a random variable.')
    return variable

  t = 0
  while t < burnin:
    x1 = 
    a1 = p(x0) / p(x1)
    a2 = q(x1, x0) / q(x0, x1)
    a = a1 * a2
    if a >= 1:
      x0 = x1
    
def chapel_flip(p):
  return Random_Variable('flip', p)

def chapel_unif(n):
  return Random_Variable('uniform', n)

def forget(var):
  return var.forget()

# Class representing random variables
class Random_Variable:

  # Initializing, taking a type string, and a list of other parameter arguments
  def __init__(self, type, args):
    self.type = type
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
    else:
      self.op = args[0]
      self.children = args[1]
    self.val = self.sample() 

  # Draws a sample value, and sets it
  def sample(self):
    if self.type == 'flip':
      if random.random() < self.p:
        self.val = True  
      else:
        self.val = False
    elif self.type == 'uniform':
      self.val = random.randint(0, self.n-1)
    elif self.type == 'constant':
      self.val = self.v
    else:
      self.val = self.op([x.getval() for x in self.children])
    return self.val

  # Gets the value, sampling if there is none yet
  def getval(self):
    if self.val is None:
      self.val = self.sample()
    return self.val

  # Forgets the current value
  def forget(self):
    self.val = None

  # Returns the probability of this particular sampling
  def prob(self):
    self.getval()
    if self.type == 'flip':
      if self.val:
        return self.p
      else:
        return 1 - self.p
    elif self.type == 'uniform':
      return (1.0 / self.n)
    elif self.type == 'constant':
      return 1
    else:
      # This isn't correct in general, of course, as children may be correlated
      return reduce(lambda x, y : x * y, [child.prob() for child in self.children])

  def __str__(self):
    return str(self.val)

  def __repr__(self):
    return '<Random_Variable with value ' + str(self.val) + '>'

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
print a

