import routing
import packet
import sys
import queue
import threading
import hashlib

config = int(sys.argv[1])
#config = 1

def receiver():
	while True:
		data, addr = r.recv()
		print(data, addr)

r = routing.Routing(10, config)
threading.Thread(target=receiver).start()

if len(sys.argv) > 2:
	host = sys.argv[2]
	port = int(sys.argv[3])
	alph = ["a", "b", "c", "d", "e", "f"]
	for a in alph:
		p = packet.Packet()
		data = a*650
		p.add_data(data)
		p.add_UDP_layer(r.addr[1], port, hashlib.md5(data.encode("utf-8")).hexdigest())
		p.add_IP_layer(r.addr[0], r.addr[1], host, port)
		pkt = p.generate_packet()
		print("Sending to:", host, port)
		print(pkt)
		r.send(pkt)
