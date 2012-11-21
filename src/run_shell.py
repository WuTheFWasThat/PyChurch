from engine.directives import Directives 
from engine.traces import *
from engine.reducedtraces import *
from engine.randomdb import *

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

if __name__ == "__main__":
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
