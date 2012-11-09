class Engine:
  def assume(self, varname, expr):
    raise Exception("Not implemented")
  def sample(self, expr):
    raise Exception("Not implemented")
  def observe(self, expr, obs_val, id):
    raise Exception("Not implemented")
  def forget(self, id):
    raise Exception("Not implemented")
  def infer(self):
    raise Exception("Not implemented")
  def rerun(self, reflip):
    raise Exception("Not implemented")
  def reset(self):
    raise Exception("Not implemented")
  
