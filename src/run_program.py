from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

import time

import argparse

try:
  from pypy.rlib import rsocket
  use_pypy = True
except:
  use_pypy = False
  
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Engine of Church implementation.  Use socket ripl to connect.')
  parser.add_argument('-e', default='traces', dest = 'engine',
                     help='Type of engine (db, traces, reduced_trace)')
  parser.add_argument('program', action = "store", help='Program to run')
  
  args = parser.parse_args()
  
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

  t = time.time()
  f = open(args.program, 'r')
  line = f.readline()
  while line:
    line = line.rstrip("\n")
    print ">>>", line

    msg = ""
    i = line.find(',')
    while i != -1: 
      for j in range(i+1, len(line)):
        if line[j] != ' ':
          print "Warning:  Characters after ',' ignored"
          break
      msg += line[:i] + ' ' 
      line = f.readline()
      line = line.rstrip("\n")
      print "...", line
      i = line.find(',')

    msg += line

    if msg == 'exit':
      break
    elif msg:
      try:
        ret_msg = directives.parse_and_run_command(msg)
      except Exception as e:
        if use_pypy:
          ret_msg = "Error occured"
        else:
          ret_msg = e.message
      print
      print ret_msg
      print
    line = f.readline()
    
  f.close()
  t = time.time() - t
  print "Time (seconds):  ", t
