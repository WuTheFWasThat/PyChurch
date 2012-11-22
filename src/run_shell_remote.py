import socket
import time


if __name__ == "__main__":
  a = socket.create_connection(('localhost', 2222))
  print a.recv(1024)
  
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

    a.send(msg)
    if msg == 'exit':
      break
    print
    print a.recv(1024)
    print
  
  a.close()
