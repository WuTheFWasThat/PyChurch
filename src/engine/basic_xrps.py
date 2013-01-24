from values import *
import math
from utils.rexceptions import RException

# HELPERS

def check_num_args(args, num):
  if len(args) != num:
    raise RException("if must take %d arguments" % num)

class if_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 3)
    (cond, true, false) = (args[0], args[1], args[2])
    if cond.bool:
      return args[1]
    else:
      return args[2]
  def __str__(self):
    return 'if'

class eq_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__eq__(args[1])
  def __str__(self):
    return '+'

class lt_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__lt__(args[1])
  def __str__(self):
    return '<'

class gt_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__gt__(args[1])
  def __str__(self):
    return '>'

class le_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__le__(args[1])
  def __str__(self):
    return '<='

class ge_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__ge__(args[1])
  def __str__(self):
    return '>='

class sum_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    sum_val = NatValue(0)
    for arg in args:
      sum_val = sum_val.__add__(arg)
    return sum_val
  def __str__(self):
    return '+'

class sub_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    sub_val = args[0]
    for i in range(1, len(args)):
      arg = args[i]
      sub_val = sub_val.__sub__(arg)
    return sub_val
  def __str__(self):
    return '-'

class mul_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    prod_val = NatValue(1)
    for arg in args:
      prod_val = prod_val.__mul__(arg)
    return prod_val
  def __str__(self):
    return '*'

class div_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    div_val = args[0]
    for i in range(1, len(args)):
      arg = args[i]
      div_val = div_val.__div__(arg)
    return div_val
  def __str__(self):
    return '/'

class pow_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__pow__(args[1])
  def __str__(self):
    return '**'

class mod_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return args[0].__mod__(args[1])
  def __str__(self):
    return '%'

class abs_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__abs__()
  def __str__(self):
    return 'abs'

class int_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__int__()
  def __str__(self):
    return 'int'

class round_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__round__()
  def __str__(self):
    return 'round'

class floor_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__floor__()
  def __str__(self):
    return 'floor'

class ceil_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__ceil__()
  def __str__(self):
    return 'ceil'

# TODO : short-circuit?

class and_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    and_val = BoolValue(True)
    for arg in args:
      and_val = and_val.__and__(arg)
    return and_val
  def __str__(self):
    return '&'

class or_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    or_val = NatValue(False)
    for arg in args:
      or_val = or_val.__or__(arg)
    return or_val
  def __str__(self):
    return '|'

class xor_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    xor_val = BoolValue(True)
    for arg in args:
      xor_val = xor_val.__xor__(arg)
    return xor_val
  def __str__(self):
    return '^'

class not_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return args[0].__inv__()
  def __str__(self):
    return '~'

# TRIG

class sin_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.sin(args[0].num))
  def __str__(self):
    return 'sin'

class cos_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.cos(args[0].num))
  def __str__(self):
    return 'cos'

class tan_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.tan(args[0].num))
  def __str__(self):
    return 'tan'

class asin_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.asin(args[0].num))
  def __str__(self):
    return 'asin'

class acos_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.acos(args[0].num))
  def __str__(self):
    return 'acos'

class atan_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 1)
    return NumValue(math.atan(args[0].num))
  def __str__(self):
    return 'atan'

class atan2_XRP(XRP):
  def __init__(self):
    self.initialize()
    self.resample = True
  def apply(self, args = None):
    check_num_args(args, 2)
    return NumValue(math.atan2(args[0].num, args[1].num))
  def __str__(self):
    return 'atan2'

