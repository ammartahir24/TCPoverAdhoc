import tcp
import routing
import sys

config = int(sys.argv[1])

s = tcp.TCPSocket(config)

if len(sys.argv) > 2:
	host, port = sys.argv[2], int(sys.argv[3])
	conn = s.connect((host, port))
	# data = "abcdefghijklmnopqrstuvwxyz"*385
	# conn.send(data)

conn, addr = s.accept()
# data = conn.recv(26)
# print("tcp_socket_test -", data) # should print: abcdefghijklmnopqrstuvwxyz
# data = conn.recv(100000)
# print("tcp_socket_test -", len(data)) # should print: 384
# data = conn.recv(1000) # should block