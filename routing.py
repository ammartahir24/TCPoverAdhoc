import socket
import queue
import threading
import json

class Routing:
	def __init__(self, buffer_capacity, i, ecn=False):
		# static route
		self.route_configs = [
		{
			("127.0.0.1", 5000): 0,
			("127.0.0.1", 6000): ("127.0.0.1", 6000),
			("127.0.0.1", 7000): ("127.0.0.1", 6000),
			("127.0.0.1", 8000): ("127.0.0.1", 6000)
		},
		{
			("127.0.0.1", 5000): ("127.0.0.1", 5000),
			("127.0.0.1", 6000): 0,
			("127.0.0.1", 7000): ("127.0.0.1", 7000),
			("127.0.0.1", 8000): ("127.0.0.1", 7000)
		},
		{
			("127.0.0.1", 5000): ("127.0.0.1", 6000),
			("127.0.0.1", 6000): ("127.0.0.1", 6000),
			("127.0.0.1", 7000): 0,
			("127.0.0.1", 8000): ("127.0.0.1", 8000)
		},
		{
			("127.0.0.1", 5000): ("127.0.0.1", 7000),
			("127.0.0.1", 6000): ("127.0.0.1", 7000),
			("127.0.0.1", 7000): ("127.0.0.1", 7000),
			("127.0.0.1", 8000): 0
		},
	]
		self.addr_configs = [("127.0.0.1", 5000), ("127.0.0.1", 6000), ("127.0.0.1", 7000), ("127.0.0.1", 8000)]
		
		self.routes = self.route_configs[i]
		self.addr = self.addr_configs[i]
		print("routing - running on ", self.addr)
		# buffer to write data meant for this node, an unbounded queue
		self.pass_on_buffer = queue.SimpleQueue()
		# router queue: thread safe, use put_nowait() and get()
		self.router_queue = queue.Queue(maxsize = buffer_capacity)
		# buffer to snoop packets
		self.snoop_buffer = []
		# ECN on/off
		self.ecn = ecn
		threading.Thread(target = self.listener).start()
		threading.Thread(target = self.forwarding).start()

	def listener(self):
		soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		soc.bind(self.addr)
		while(True):
			msg, s_addr = soc.recvfrom(1024)
			packet = json.loads(msg.decode("utf-8")) # jsonify message here
			try:
				self.router_queue.put_nowait(packet)
			except:
				print("routing - listener: Unable to put packet into queue.")
				pass
			
	def forwarding(self):
		while True:
			packet = self.router_queue.get()
			
			# A normal packet
			self.process(packet)
		
	def process(self, packet):
		packet_dst = (packet["dst_IP"], packet["dst_port"])
		forward_to = self.routes[packet_dst]
		# print("routing - Forwarding to", forward_to)
		if forward_to == 0:
			recv_addr = packet["src_IP"], packet["src_port"]
			packet_transport = packet["transport"]
			self.pass_on_buffer.put((packet_transport, recv_addr))
		else:
			soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
			soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
			soc.close()
	
	def send(self, packet):
		try:
			self.router_queue.put_nowait(packet)
		except:
			pass
		
	def recv(self, timeout = None):
		data, addr = self.pass_on_buffer.get(timeout = timeout)
		return data, addr
	