import socket
import queue
import threading
import json

class Routing:
	def __init__(self, buffer_capacity, i, ecn=False):
		# static route
#		self.route_configs = [
#			{
#				("127.0.0.1", 5000): 0,
#				("127.0.0.1", 6000): ("127.0.0.1", 6000),
#				("127.0.0.1", 7000): ("127.0.0.1", 6000),
#				("127.0.0.1", 8000): ("127.0.0.1", 6000)
#			},
#			{
#				("127.0.0.1", 5000): ("127.0.0.1", 5000),
#				("127.0.0.1", 6000): 0,
#				("127.0.0.1", 7000): ("127.0.0.1", 7000),
#				("127.0.0.1", 8000): ("127.0.0.1", 7000)
#			},
#			{
#				("127.0.0.1", 5000): ("127.0.0.1", 6000),
#				("127.0.0.1", 6000): ("127.0.0.1", 6000),
#				("127.0.0.1", 7000): 0,
#				("127.0.0.1", 8000): ("127.0.0.1", 8000)
#			},
#			{
#				("127.0.0.1", 5000): ("127.0.0.1", 7000),
#				("127.0.0.1", 6000): ("127.0.0.1", 7000),
#				("127.0.0.1", 7000): ("127.0.0.1", 7000),
#				("127.0.0.1", 8000): 0
#			},
#		]
#		self.addr_configs = [("127.0.0.1", 5000), ("127.0.0.1", 6000), ("127.0.0.1", 7000), ("127.0.0.1", 8000)]
        
		self.route_configs = [
			{
				("192.168.137.35", 5000): 0,
				("192.168.137.200", 6000): ("192.168.137.200", 6000),
			},
			{
				("192.168.137.35", 5000): ("192.168.137.35", 5000),
				("192.168.137.200", 6000): 0,
			},
		]
        
		self.addr_configs = [("192.168.137.35", 5000), ("192.168.137.200", 6000)]

		self.routes = self.route_configs[i]
		self.addr = self.addr_configs[i]
		print("running on ", self.addr)
		# buffer to write data meant for this node, an unbounded queue
		self.pass_on_buffer = queue.SimpleQueue()
        # buffer for ACK from the node ahead in the static routing
		self.ack_buffer = queue.SimpleQueue()
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
				# Probably an ACK. This is a sketchy way to do this LOL
				try:
					self.get_ack(packet)
				except:
					pass

	def forwarding(self):
		while True:
			packet = self.router_queue.get()
			
			# A normal packet
			self.process(packet)

	def get_ack(self, ack):
		self.ack_buffer.put(ack)

	def process(self, packet):
		packet_dst = (packet["dst_IP"], packet["dst_port"])
		forward_to = self.routes[packet_dst]
		print("Forwarding to", forward_to)
		if forward_to == 0:
			packet_transport = packet["transport"]
			self.pass_on_buffer.put(packet_transport)
		else:
			soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
			soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
			soc.close()

	def send(self, packet):
		try:
			self.router_queue.put_nowait(packet)
		except:
			pass
        