import socket
import sys

s = socket.socket()
ip = sys.argv[1]
port = int(sys.argv[2])
s.bind((ip, port))
s.listen(1)

c,a = s.accept()
num_files = int(c.recv(1024).decode('utf-8'))
print(num_files, " files ready to be received.")
c.send("ack".encode('utf-8'))

for f in range(num_files):
	file_name = c.recv(1024).decode('utf-8')
	c.send("ack".encode('utf-8'))
	print("Starting receiving: ", file_name)
	file_length = int(c.recv(1024).decode('utf-8'))
	c.send("ack".encode('utf-8'))
	print("File size: ", file_length)
	f = open(file_name, "wb")
	file_s = 0
	while file_s < file_length:
		data = c.recv(file_length)
		f.write(data)
		file_s += len(data)
	c.send("ack".encode('utf-8'))
	f.close()

c.close()