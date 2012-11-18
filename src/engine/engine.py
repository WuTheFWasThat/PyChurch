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
  def report_directives(self, directive_type):
    raise RException("Not implemented")
  def forget(self, id):
    raise RException("Not implemented")
  def infer(self):
    raise RException("Not implemented")
  def reset(self):
    raise RException("Not implemented")
  
