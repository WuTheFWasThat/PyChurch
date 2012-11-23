from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

import argparse

engine_type = 'reduced traces'
if engine_type == 'reduced traces':
  engine = ReducedTraces()
elif engine_type == 'traces':
  engine = Traces()
elif engine_type == 'randomdb':
  engine = RandomDB()
else:
  raise RException("Engine %s is not implemented" % engine_type)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Church interpreter.')
  parser.add_argument('-e', default='traces', dest = 'engine',
                     help='Type of engine (db, traces, reduced_trace)')
  
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

  while True:
    line = raw_input(">>> ")

    msg = ""
    i = line.find(',')
    while i != -1:
      for j in range(i+1, len(line)):
        if line[j] != ' ':
          print "Warning:  Characters after ',' ignored"
          break
      msg += line[:i] + ' '
      line = raw_input("... ")
      i = line.find(',')
    msg += line

    if msg == 'exit':
      break
    try:
      ret_msg = directives.parse_and_run_command(msg)
    except Exception as e:
      ret_msg = e.message
    print
    print ret_msg 
    print
