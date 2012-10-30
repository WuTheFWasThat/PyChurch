import os
import sys

def a(blah):
  if len(blah) == 1:
    return blah[0]
  else:
    ans =  blah[0]
    for x in blah[1:]:
      ans = ans + a(x)
    return ans

def entry_point(argv):
    print a([1])
    print a([2])
    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
