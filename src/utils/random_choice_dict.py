import rrandom
from utils.rexceptions import RException

# A dictionary which also supports fetching a random key in O(1)
# See http://stackoverflow.com/questions/10840901/python-get-random-key-in-a-dictionary-in-o1
class RandomChoiceDict():
  def __init__(self):
      self.dict = {} 
      self.idToKey = []
      self.keyToId = {}

  def __getitem__(self, key): 
      return self.dict[key]

  def __setitem__(self, key, value): 
      if key not in self.dict:
          self.keyToId[key] = len(self.idToKey) 
          self.idToKey.append(key)
      self.dict[key] = value

  def __delitem__(self, key): 
      if key not in self.dict:
        return

      del self.dict[key]
      delId = self.keyToId.pop(key)
      lastKey = self.idToKey.pop()

      if delId < len(self.idToKey):
        self.idToKey[delId] = lastKey
        self.keyToId[lastKey] = delId 

  def randomKey(self): 
      if len(self.idToKey) == 0:
        raise RException("No keys to get")
      index =  rrandom.random.randbelow(len(self.idToKey))
      return self.idToKey[index]
      # return self.idToKey[random.randrange(len(self.idToKey))]

  def __str__(self):
      return self.dict.__str__()

  def __iter__(self):
      return self.dict.__iter__()

  def __contains__(self, x):
      return (x in self.dict)

  def __len__(self):
      return len(self.dict)
