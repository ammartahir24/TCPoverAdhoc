
import socket
import queue
import threading
import json
import time
import packet

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
		
		# self.etxs = {}
		# self.etx_queues = {}
		
		# if i == 0:
		# 	self.etxs[self.addr_configs[1]] = 1
		# 	self.etx_queues[self.addr_configs[1]] = queue.SimpleQueue()
		# 	threading.Thread(target = self.etx_probing, args=(self.addr_configs[1],)).start()
			
		# elif i == (len(self.addr_configs) - 1):
		# 	self.etxs[self.addr_configs[-2]] = 1
		# 	self.etx_queues[self.addr_configs[-2]] = queue.SimpleQueue()
		# 	threading.Thread(target = self.etx_probing, args=(self.addr_configs[-2],)).start()
			
		# else:
		# 	self.etxs[self.addr_configs[i-1]] = 1
		# 	self.etx_queues[self.addr_configs[i-1]] = queue.SimpleQueue()
		# 	threading.Thread(target = self.etx_probing, args=(self.addr_configs[i-1],)).start()
		# 	self.etxs[self.addr_configs[i+1]] = 1
		# 	self.etx_queues[self.addr_configs[i+1]] = queue.SimpleQueue()
		# 	threading.Thread(target = self.etx_probing, args=(self.addr_configs[i+1],)).start()
			
		# buffer to write data meant for this node, an unbounded queue
		self.pass_on_buffer = queue.SimpleQueue()
		# router queue: thread safe, use put_nowait() and get()
		self.router_queue = queue.Queue(maxsize = buffer_capacity)
		# buffer to snoop packets
		self.snoop_buffer = []
		# Buffer for probe packets (ETX)
		self.probe_buffer = queue.SimpleQueue()
		# ECN on/off
		self.ecn = ecn
		threading.Thread(target = self.listener).start()
		threading.Thread(target = self.forwarding).start()
		# Start listener for probe
		# threading.Thread(target = self.listener_probe).start()
		

	def listener(self):
		soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		soc.bind(self.addr)
		while(True):
			msg, s_addr = soc.recvfrom(1024)
			packet = json.loads(msg.decode("utf-8")) # jsonify message here
			# Check for probe packet
			# if packet['transport']['etx'] == True:
			# 	self.probe_buffer.put_nowait(packet)
			# else:
			try:
				self.router_queue.put_nowait(packet)
			except:
				pass
				# print("routing - listener: Unable to put packet into queue.")
			
	def forwarding(self):
		while True:
			packet = self.router_queue.get()
			time.sleep(0.00005)
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
	
	def listener_probe(self):
		# For listening to incoming probe packets from neighboring nodes.
		# Based on the address, create a new dictionary SimpleQueue for the respective ETX packets
		
		while True:
			packet = self.probe_buffer.get()
			
			# Put the probe packet in the appropriate queue address
			recv_addr = packet["src_IP"], packet["src_port"]
			etx_num = packet["transport"]['etx_num']
			self.etx_queues[recv_addr].put(etx_num)
			
	
	def etx_probing(self, addr):
		# implement probing algorithm here, feel free to make any additional class functions as needed
		# you will need a separate thread to listen to probe packets, span it from init as you need it
		# this function runs in separate thread for each neighbour, in each thread you are probing node with (host, port)=addr
		# you will update the etx for this addr by updating self.etxs[addr], which is initialy set to 1 (see init)

		# Get system clock to sync the while loop
		starttime = time.time()
		
		# Initial ETX
		probe_etx = self.etxs[addr]
		
		# Represent the last 10 packets in a list. 1 means a packet received in that one second period. A 0 means no packet.
		pkt_list = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
		
		# Send and receive probe packets every second 
		while True:
			# Create the probe packet
			probe_pkt = packet.Packet.etx_packet(self.addr,	 # Source address
										addr,				 # Destination address
										etx_num = self.etxs[addr] # ETX value
										)
			
			# Send the ETX probe packet
			self.send(probe_pkt)			
			#print('pkt sent')
			
			# Receive a probe packet from the queue
			if not self.etx_queues[addr].empty():
				probe_etx = self.etx_queues[addr].get()
				# Say that this is a received packet
				pkt_list.append(1)
				#print('pkt rcv')
			else: 
				# A packet was not received
				pkt_list.append(0)
				
			# Remove the first packet in the list
			pkt_list.pop(0)
			
			# Update the ETX between the current node (here) to the neighbor node
			# TODO: divide by zero?
			pkt_probability = (1 - sum(pkt_list) / len(pkt_list)) * (1 - (probe_etx / len(pkt_list)))
			self.etxs[addr] = 1 / pkt_probability
			
			#print(self.addr, self.etxs[addr])
			
			# Lock the packet sending to the system clock and run every second
			time.sleep(1.0 - ((time.time() - starttime) % 1.0))
			
		