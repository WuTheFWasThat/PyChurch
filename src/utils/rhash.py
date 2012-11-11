try:
    from pypy.rlib.rarithmetic import r_uint, intmask
except:
    def r_uint(x):
      return x
    def intmask(x):
      return x

def hash_pair(a, b):
  return intmask((r_uint(a) * r_uint(12345) + r_uint(b)) % r_uint(18446744073709551557))

def hash_many(args):
  hashval = 0
  for arg in args:
    hashval = hash_pair(hashval, arg)
  return hashval

try:
  from pypy.rlib.objectmodel import _hash_float as hash_float
except:
  def hash_float(num):
    return hash(num)

