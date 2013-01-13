import os
import sys
import math

class Value:
  def stringify(self, extrarg):
    return 'Value' + extrarg
  def __str__(self):
    return 'Value'
  def __le__(self, other):
    return True
  def __ge__(self, other):
    return False
  pass

class StrValue(Value):
  def __init__(self, strv):
    self.type = 'str'
    self.str = strv 

  def stringify(self, extrarg):
    return 'StrValue' + extrarg
  def __str__(self):
    return self.type + str(self.str)
  def __hash__(self):
    return 124123
  def __le__(self, other):
    return True
  def __ge__(self, other):
    return False

class IntValue(Value):
  def __init__(self, intv, secondint = None):
    self.type = 'int'
    self.int = intv 
    if secondint is None:
      self.secondint = intv
    else:
      self.secondint = secondint
  def stringify(self, extrarg):
    return 'IntValue' + extrarg
  def __hash__(self):
    return self.int

  def __str__(self):
    return self.type + str(self.int) + str(self.secondint)

class BoolValue(Value):
  def __init__(self, boolv):
    self.type = 'bool'
    self.bool = boolv

  def stringify(self, extrarg):
    return 'BoolValue' + extrarg
  def __str__(self):
    return self.type + str(self.bool)
  def __hash__(self):
    return int(self.bool)
  def __le__(self, other):
    return True
  def __ge__(self, other):
    return False

def act(val):
  if val.type == 'str':
    c = StrValue('Wheee')
    print val.str[0]
  elif val.type == 'int':
    c = IntValue(3333, 3)
  else:
    c = BoolValue(True)
  return c > val

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

    x=  [a, b, c]
    y = ','.join([yy.__str__() for yy in x])
    z = ','.join([zz.stringify('cat') for zz in x])

    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
