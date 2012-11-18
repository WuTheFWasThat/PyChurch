import utils.expr_parser as parser

try:
  from pypy.rlib import rsocket
  use_pypy = True
except:
  import socket as rsocket
  use_pypy = False

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
      ret_msg = parser.parse_directive(msg)
    except Exception as e:
      if use_pypy:
        ret_msg = "Error occured"
      else:
        ret_msg = e.message
    print
    print ret_msg 
    print
