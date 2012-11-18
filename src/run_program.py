import utils.expr_parser as parser
import time
import sys

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
        ret_msg = parser.parse_directive(msg)
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
