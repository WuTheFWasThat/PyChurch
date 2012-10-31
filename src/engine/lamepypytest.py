import os
import sys

class Value:
  pass

class StrValue(Value):
  def __init__(self, strv):
    self.type = 'str'
    self.str = strv 

  def __str__(self):
    return self.type + str(self.str)

class IntValue(Value):
  def __init__(self, intv, secondint = None):
    self.type = 'int'
    self.int = intv 
    if secondint is None:
      self.secondint = intv
    else:
      self.secondint = secondint

  def __str__(self):
    return self.type + str(self.int) + str(self.secondint)

class BoolValue(Value):
  def __init__(self, boolv):
    self.type = 'bool'
    self.bool = boolv

  def __str__(self):
    return self.type + str(self.bool)

def act(val):
  print val.__str__()
  if val.type == 'str':
    c = StrValue('Wheee')
    print val.int
  elif val.type == 'int':
    print val.int
    c = IntValue(3333, 3)
  else:
    c = BoolValue(True)
  print c

def a(blah):
  if len(blah) == 1:
    return blah[0]
  else:
    ans =  blah[0]
    for x in blah[1:]:
      ans = ans + a(x)
    return ans

def entry_point(argv):
    a = BoolValue(True)
    act(a)
    b = IntValue(3, 4)
    act(b)
    c = IntValue(3.1415, 9265)
    act(c)
    d = StrValue('fish')
    act(d)
    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
