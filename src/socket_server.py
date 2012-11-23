"""
Based on the PyPy tutorial by Andrew Brown
Parts copied from http://www.smipple.net/snippet/Shibukawa%20Yoshi/RPython%20echo%20server
"""

import os
import sys
import utils.expr_parser as parser
from utils.rexceptions import RException

import argparse

from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

try:
  from pypy.rlib import rsocket
  use_pypy = True
except:
  import socket as rsocket
  use_pypy = False

try:
  from pypy.rlib.jit import JitDriver
  jitdriver = JitDriver(greens = [ \
                                 ### INTs 
                                 ### REFs 
                                     'msg'
                                 ### FLOATs 
                                 ],  \
                        reds   = [  \
                                 ### INTs 
                                 ### REFs 
                                     'client_sock'
                                 ### FLOATs 
                                 ])
  def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()
  use_jit = True
except:
  use_jit = False

sys.setrecursionlimit(10000)


def run(directives):

    hostip = rsocket.gethostbyname('localhost')
    if use_pypy:
      host = rsocket.INETAddress(hostip.get_host(), 2222)
      socket = rsocket.RSocket(rsocket.AF_INET, rsocket.SOCK_STREAM)
    else:
      host = (hostip, 2222)
      socket = rsocket.socket(rsocket.AF_INET, rsocket.SOCK_STREAM)
    
    socket.bind(host)
    socket.listen(1)
   
    bufsize = 1048576
    while True:
      if use_pypy:
        (client_sock_fd, client_addr) = socket.accept()
        client_sock = rsocket.fromfd(client_sock_fd, rsocket.AF_INET, rsocket.SOCK_STREAM)
      else:
        (client_sock, client_addr) = socket.accept()
      client_sock.send("Server ready!\n")
      print 'Client contacted'
      while True:
        msg = client_sock.recv(bufsize)

        if use_jit:
          jitdriver.jit_merge_point( \
                                     # INTs
                                     ## REFs
                                     msg = msg,
                                     client_sock = client_sock
                                     # FLOATs
                                     )

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
    parser = argparse.ArgumentParser(description='Engine of Church implementation.  Use socket ripl to connect.')
    parser.add_argument('--e', default='traces', dest = 'engine',
                       help='Type of engine (db, traces, reduced_trace)')
    
    args = parser.parse_args()
    print args

    engine_type = args.engine
    if engine_type in ['rt', 'reduced', 'reduced_trace', 'reduced_traces', 'reducedtrace', 'reducedtraces']:
      engine = ReducedTraces()
    elif engine_type in ['t', 'trace', 'traces']:
      engine = Traces()
    elif engine_type in ['r', 'db', 'randomdb']:
      engine = RandomDB()
    else:
      raise RException("Engine %s is not implemented" % engine_type)
    
    directives = Directives(engine)

    run(10)
    
    return 0

def target(*args):
    return entry_point, None
    
if __name__ == "__main__":
    entry_point(sys.argv)
