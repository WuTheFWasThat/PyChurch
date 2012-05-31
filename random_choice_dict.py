import random
# A dictionary which also supports fetching a random key in O(1)
# See http://stackoverflow.com/questions/10840901/python-get-random-key-in-a-dictionary-in-o1

class RandomChoiceDict(object):
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

        if lastKey == key:
          return
        else:
          self.idToKey[delId] = lastKey
          self.keyToId[lastKey] = delId 

    def randomKey(self): 
        return self.idToKey[random.randrange(len(self.idToKey))]

    def __str__(self):
        return self.dict.__str__()
