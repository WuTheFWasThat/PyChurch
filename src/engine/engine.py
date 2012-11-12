class Engine:
  def assume(self, varname, expr, id):
    raise Exception("Not implemented")
  def predict(self, expr, id):
    raise Exception("Not implemented")
  def observe(self, expr, obs_val, id):
    raise Exception("Not implemented")
  def report_directives(self, directive_type):
    raise Exception("Not implemented")
  def forget(self, id):
    raise Exception("Not implemented")
  def infer(self):
    raise Exception("Not implemented")
  def rerun(self):
    raise Exception("Not implemented")
  def reset(self):
    raise Exception("Not implemented")
  
