from utils.rexceptions import RException

class Environment:
  def __init__(self, parent = None):
    self.parent = parent # The parent environment
    self.assignments = {} # Dictionary from names to values
    return

  def reset(self):
    if self.parent is not None:
      raise RException("Resetting non-root environment")
    self.__init__()

  def set(self, name, value):
    self.assignments[name] = value

  def lookup(self, name):
    if name in self.assignments:
      return (self.assignments[name], self)
    else:
      if self.parent is None:
        raise RException('Variable %s undefined in env:\n%s' % (name, self.__str__()))
      else:
        return self.parent.lookup(name)

  def spawn_child(self): 
    return Environment(self)

  def __setitem__(self, name, value):
    self.set(name, value) 

  def __getitem__(self, name):
    return self.lookup(name) 

  def __str__(self):
    string = ''
    for x in self.assignments:
      string += str(x)
      string += ' : '
      string += str(self.assignments[x])
      string += '\n'
    return string

