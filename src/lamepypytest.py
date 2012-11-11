import os
import sys
import math
from pypy.rlib.rarithmetic import *


from pypy.rlib.objectmodel import _hash_float as hash_float


def entry_point(argv):
    a = 0.5

    print hash_float(a)
    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
