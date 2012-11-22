"""
Based on the PyPy tutorial by Andrew Brown
Parts copied from http://www.smipple.net/snippet/Shibukawa%20Yoshi/RPython%20echo%20server
"""

import os
import sys
from utils.rexceptions import RException


from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

try:
  from pypy.rlib import rsocket as socket
  use_pypy = True
except:
  import socket
  use_pypy = False

engine_type = 'reduced traces'
if engine_type == 'reduced traces':
  engine = ReducedTraces()
elif engine_type == 'traces':
  engine = Traces()
elif engine_type == 'randomdb':
  engine = RandomDB()
else:
  raise RException("Engine %s is not implemented" % engine_type)

directives = Directives(engine)

sys.setrecursionlimit(10000)

def run(fp):

    hostip = socket.gethostbyname('localhost')
    if use_pypy:
      host = socket.INETAddress(hostip.get_host(), 2222)
      socket = socket.RSocket(socket.AF_INET, socket.SOCK_STREAM)
    else:
      host = (hostip, 2222)
      socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    socket.bind(host)
    socket.listen(1)
   
    bufsize = 1048576
    while True:
      if use_pypy:
        (client_sock_fd, client_addr) = socket.accept()
        client_sock = socket.fromfd(client_sock_fd, socket.AF_INET, socket.SOCK_STREAM)
      else:
        (client_sock, client_addr) = socket.accept()
      client_sock.send("Server ready!\n")
      print 'Client contacted'
      while True:
        msg = client_sock.recv(bufsize)
        if not msg:
          client_sock.close()
          break;
        msg = msg.rstrip("\n")
        print "\nRECEIVED:\n%s" % msg
        if msg == "exit":
          client_sock.close()
          break;
        try:
          ret_msg = directives.parse_and_run_command(msg)
        except RException as e:
          ret_msg = e.message
        client_sock.send(ret_msg)
        print "\nSENT:\n%s" % ret_msg
      return 1 # could be unindented, if not for rpython

def mainloop(program, bracket_map):
    pc = 0
    tape = Tape()
    
    while pc < len(program):
      print "im in a loop"

def read(fp):
    program = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        program += read
    return program

def entry_point(argv):

    #run(os.open(filename, os.O_RDONLY, 0777))
    run(10)
    
    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
