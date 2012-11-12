import socket
import time
import sys

if __name__ == "__main__":
  a = socket.create_connection(('localhost', 5000))
  print a.recv(1024)

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
      a.send(msg)
      print
      print a.recv(2024)
      print
    line = f.readline()
  a.send('exit')
  a.recv(1024)
  
  f.close()
  a.close()
  t = time.time() - t
  print "Time connected (seconds):  ", t
