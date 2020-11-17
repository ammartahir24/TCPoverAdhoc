import tcp
import routing
import sys

config = int(sys.argv[1])

s = tcp.TCPSocket(config)

if len(sys.argv) > 2:
	host, port = sys.argv[2], int(sys.argv[3])
	conn = s.connect((host, port))

conn, addr = s.accept()
print(addr)