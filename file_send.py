import socket
import sys
import os

ip = sys.argv[1]
port = int(sys.argv[2])

files = sys.argv[3:]

print (files)

if files[0] == '.':
	files = os.listdir()

s = socket.socket()
s.connect((ip, port))

s.send(str(len(files)).encode('utf-8'))
s.recv(1024)
print("Sending files:", files)

for f in files:
	s.send(f.encode('utf-8'))
	s.recv(1024)
	s.send(str(os.stat(f).st_size).encode('utf-8'))
	s.recv(1024)
	file = open(f, 'rb')
	data = file.read()
	s.send(data)
	s.recv(1024)
	file.close()

s.close()