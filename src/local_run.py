import socket
import time
import sys

if __name__ == "__main__":
  a = socket.create_connection(('localhost', 5000))
  print a.recv(1024)

  t = time.time()
  f = open(sys.argv[1], 'r')
  msg = f.readline()
  while msg:
    msg = msg.rstrip("\n")
    if msg == 'exit':
      break
    elif msg:
      a.send(msg)
      print ">>>", msg
      print a.recv(1024)
    msg = f.readline()
  a.send('exit')
  a.recv(1024)
  
  f.close()
  a.close()
  t = time.time() - t
  print "Time connected (seconds):  ", t
