import random

class xrp:
  def __init__(self, start_state, sample_f, incorporate_f):
    self.state = start_state
    self.sample_f = sample_f
    self.incorporate_f = incorporate_f
  def sample(self, arg = None):
    return self.sample_f(self.state, arg)
  def incorporate(self, val, arg = None):
    self.state = self.incorporate_f(self.state, val, arg = None)
    return self.state

def coin_sample(state, arg):
  (h, t) = state
  if random.random() * (h + t) < h:
    return 1
  else:
    return 0

def coin_incorporate(state, val, arg = None):
  (h, t) = state
  if val:
    h += 1
  else:
    t += 1
  return (h, t)

a = xrp((1, 1), coin_sample, coin_incorporate)

print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
print a.incorporate(a.sample()),  a.state
