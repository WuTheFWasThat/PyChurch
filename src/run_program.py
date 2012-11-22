from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

import time
import sys

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

try:
  from pypy.rlib import rsocket
  use_pypy = True
except:
  use_pypy = False
  
if __name__ == "__main__":
  t = time.time()
  f = open(sys.argv[1], 'r')
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
