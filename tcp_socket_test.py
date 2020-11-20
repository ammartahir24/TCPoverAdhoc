import tcp
import routing
import sys
import time
import hashlib


config = int(sys.argv[1])
# config = 0

s = tcp.TCPSocket(config)

if len(sys.argv) > 2:
	host, port = sys.argv[2], int(sys.argv[3])
#	host, port = '127.0.0.1', 6000
	conn = s.connect((host, port))
	data = "abcdefghijklmnopqrstuvwxyz"*385000
	# alph = ["a", "b", "c", "d", "e", "f", 'g','h']
	# data = [a * 300 for a in alph]
	conn.send(data)
	print("tcp_socket_test -", len(data), hashlib.md5(data.encode("utf-8")).hexdigest()) 
	# conn.close()

conn, addr = s.accept()
data = conn.recv(1000000) # should block
print("tcp_socket_test -", len(data), hashlib.md5(data.encode("utf-8")).hexdigest()) 
# conn.close()