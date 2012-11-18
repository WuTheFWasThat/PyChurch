# Class which is just an exception, but guaranteed to have a message

class RException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
