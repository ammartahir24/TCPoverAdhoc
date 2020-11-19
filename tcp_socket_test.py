import tcp
import routing
import sys
import time

config = int(sys.argv[1])
# config = 0

s = tcp.TCPSocket(config)

if len(sys.argv) > 2:
	host, port = sys.argv[2], int(sys.argv[3])
#	host, port = '127.0.0.1', 6000
	conn = s.connect((host, port))
	data = "abcdefghijklmnopqrstuvwxyz"*385
	# alph = ["a", "b", "c", "d", "e", "f", 'g','h']
	# data = [a * 300 for a in alph]
	conn.send(data)
	# conn.close()

conn, addr = s.accept()
time.sleep(5)
data = conn.recv(1)
print("tcp_socket_test -", data)
data = conn.recv(3)
print("tcp_socket_test -", len(data)) 
data = conn.recv(1000) # should block
# conn.close()