from utils.rexceptions import RException

class Engine:
  def assume(self, varname, expr, id):
    raise RException("Not implemented")
  def predict(self, expr, id):
    raise RException("Not implemented")
  def observe(self, expr, obs_val, id):
    raise RException("Not implemented")
  def report_value(self, id):
    raise RException("Not implemented")
  def forget(self, id):
    raise RException("Not implemented")
  def infer(self):
    raise RException("Not implemented")
  def reset(self):
    raise RException("Not implemented")
  def get_log_score(self, id):
    raise RException("Not implemented")
  def weight(self):
    raise RException("Not implemented")
  def random_choices(self):
    raise RException("Not implemented")
  def mhstats_on(self):
    raise RException("Not implemented")
  def mhstats_off(self):
    raise RException("Not implemented")
  def mhstats_detailed(self):
    raise RException("Not implemented")
  def mhstats_aggregated(self):
    raise RException("Not implemented")
  
class Node:
  def __leq__(self, other):
    raise RException("Not implemented")
