import socket
import time

a = socket.create_connection(('localhost', 5000))
print a.recv(1024)

while True:
  var = raw_input(">>> ")
  a.send(var)
  if var == 'exit':
    break
  print a.recv(1024)

a.close()
