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


class MaxHeap():
    def __init__(self):
        """Initially empty priority queue."""
        self.heap = []
        self.index = {}
        self.values = {} 
    
    def __len__(self):
        return len(self.heap) 

    def val(self, index):
        return self.values[self.heap[index]]

    def swap(self, index1, index2):
      key1 = self.heap[index1]
      key2 = self.heap[index2]
      self.index[key2] = index1
      self.heap[index1] = key2
      self.index[key1] = index2
      self.heap[index2] = key1
      return index2
    
    def add(self, key, val):
        i = len(self.heap)
        self.heap.append(key)
        self.values[key] = val
        self.index[key] = i
        self.heapify_up(i)

    def max(self):
        return self.val(0)
    
    def delete(self, key):
        if key not in self.index:
          raise RException("Key not in heap")
        i = self.index[key]
        last = len(self.heap) - 1
        if (i != last):
          self.swap(i, last)
        lastkey = self.heap.pop()
        assert lastkey == key
        assert self.index[key] == last
        del self.index[key]
        del self.values[key]
        if (i != last):
          i = self.heapify_up(i)
          i = self.heapify_down(i)
        
    def heapify_up(self, i):
        while i > 0:
            if self.val(i) > self.val((i-1) / 2):
                i = self.swap(i, (i-1) / 2)
            else:
                break
        return i
    
    def heapify_down(self, i):
        while True:
            left = i * 2 + 1
            if left >= len(self.heap):
                break
            child = left

            right = i * 2 + 2
            if right < len(self.heap) and self.val(right) > self.val(left):
              child = right

            if self.val(i) >= self.val(child):
                break
            i = self.swap(i, child)
        return i

class WeightedRandomChoiceDict():
  def __init__(self):
      self.dict = {} 
      self.idToKey = []
      self.keyToId = {}
      self.heap = MaxHeap()

  def __getitem__(self, key): 
      return self.dict[key]

  def __setitem__(self, key, value, weight): 
      if weight == 0:
        return
      if key not in self.dict:
          self.keyToId[key] = len(self.idToKey) 
          self.idToKey.append(key)
      self.heap.add(key, weight)
      self.dict[key] = (value, weight)

  def __delitem__(self, key): 
      if key not in self.dict:
        return

      (value, weight) = self.dict[key]

      del self.dict[key]
      self.heap.delete(key)

      delId = self.keyToId.pop(key)
      lastKey = self.idToKey.pop()

      if delId < len(self.idToKey):
        self.idToKey[delId] = lastKey
        self.keyToId[lastKey] = delId 

  def randomKey(self): 
      if len(self.idToKey) == 0:
        raise RException("No keys to get")
      max = self.heap.max()
      while True:
        index =  rrandom.random.randbelow(len(self.idToKey))
        key = self.idToKey[index]
        p =  rrandom.random.random()
        (value, weight) = self.dict[key]
        if p * max < weight:
          return key

  def __str__(self):
      return self.dict.__str__()

  def __iter__(self):
      return self.dict.__iter__()

  def __contains__(self, x):
      return (x in self.dict)

  def __len__(self):
      return len(self.dict)

