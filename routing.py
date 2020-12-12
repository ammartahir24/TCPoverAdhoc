import socket
import queue
import threading
import json
import time
import packet
import random

class Routing:
	def __init__(self, buffer_capacity, i, exp_name, ecn=False):
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
		
		self.exp_name = exp_name
		self.etx_timeout = 0.0005
		self.etxs = {}
		self.etx_queues = {}
		self.snoop_buffer = {}

		if i == 0:
			self.etxs[self.addr_configs[1]] = 1
			self.etx_queues[self.addr_configs[1]] = queue.Queue()
			threading.Thread(target = self.etx_probing, args=(self.addr_configs[1],)).start()
			
		elif i == (len(self.addr_configs) - 1):
			self.etxs[self.addr_configs[-2]] = 1
			self.etx_queues[self.addr_configs[-2]] = queue.Queue()
			threading.Thread(target = self.etx_probing, args=(self.addr_configs[-2],)).start()
			
		else:
			self.etxs[self.addr_configs[i-1]] = 1
			self.etx_queues[self.addr_configs[i-1]] = queue.Queue()
			threading.Thread(target = self.etx_probing, args=(self.addr_configs[i-1],)).start()
			self.etxs[self.addr_configs[i+1]] = 1
			self.etx_queues[self.addr_configs[i+1]] = queue.Queue()
			threading.Thread(target = self.etx_probing, args=(self.addr_configs[i+1],)).start()
			
		# buffer to write data meant for this node, an unbounded queue
		self.pass_on_buffer = queue.SimpleQueue()
		# router queue: thread safe, use put_nowait() and get()
		self.router_queue = queue.Queue(maxsize = buffer_capacity)
		# buffer to snoop packets
		# self.snoop_buffer = {}
		# Buffer for probe packets (ETX)
		self.probe_buffer = queue.SimpleQueue()
		# ECN on/off
		self.ecn = ecn
		self.transmission_log = {}
		threading.Thread(target = self.listener).start()
		threading.Thread(target = self.forwarding).start()
		# Start listener for probe
		threading.Thread(target = self.listener_probe).start()
		

	def listener(self):
		soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		soc.bind(self.addr)
		while(True):
			try:
				msg, s_addr = soc.recvfrom(1224)
				packet = json.loads(msg.decode("utf-8")) # jsonify message here
				# artificial packet dropping with probability 0.1
				# if random.randrange(1000) < 1:
				# 	continue
			# Check for probe packet
				if packet['transport']['etx'] and packet['transport']['reply']:
					r_addr = (packet["src_IP"], packet["src_port"])
					# print(r_addr)
					self.etx_queues[r_addr].put(packet)
				elif packet['transport']['etx']:
					self.probe_buffer.put(packet)
				else:
					self.router_queue.put_nowait(packet)
			except:
				pass
				# print("routing - listener: Unable to put packet into queue.")
			
	def forwarding(self):
		while True:
			packet = self.router_queue.get()
			if packet['transport']['data'] == 'transmission_log':
				with open(self.exp_name+"_"+self.addr[0]+'_'+str(self.addr[1])+'_transmission_log.txt', 'w') as outfile:
				    json.dump(self.transmission_log, outfile)
			# time.sleep(0.00005)
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
		elif not packet['transport']['syn'] and packet['transport']['snoop']:
			addr_tup = (packet['src_IP'], packet['src_port'], packet['dst_IP'], packet['dst_port'])
			addr_tup_rev = (packet['dst_IP'], packet['dst_port'], packet['src_IP'], packet['src_port'])
			if not packet['transport']['ack']:
				pkt_effort = packet['transport']['pkt_effort'] * self.etxs[forward_to]
				packet['transport']['success_prob'] *= self.etxs[forward_to]
				pkt_qos = packet['transport']['pkt_qos']
				if pkt_effort < pkt_qos:
					# print(packet['transport']['seq_num'], pkt_effort, pkt_qos, "hit")
					packet['transport']['pkt_effort'] = 1
					if addr_tup not in self.snoop_buffer:
						self.snoop_buffer[addr_tup] = {}
						self.snoop_buffer[addr_tup]['last_ack'] = 0
					self.snoop_buffer[addr_tup][packet['transport']['seq_num']] = packet
				else:
					packet['transport']['pkt_effort'] = pkt_effort
				soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
				soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
				soc.close()
				if packet['transport']['seq_num'] in self.transmission_log:
					self.transmission_log[packet['transport']['seq_num']] += 1
				else:
					self.transmission_log[packet['transport']['seq_num']] = 1
			elif packet['transport']['ack']:
				if addr_tup_rev not in self.snoop_buffer:
					self.snoop_buffer[addr_tup_rev] = {}
					self.snoop_buffer[addr_tup_rev]['last_ack'] = packet['transport']['ack_num']
				if packet['transport']['ack_num'] > self.snoop_buffer[addr_tup_rev]['last_ack']:
					for i in range(self.snoop_buffer[addr_tup_rev]['last_ack'], packet['transport']['ack_num']):
						if i in self.snoop_buffer[addr_tup_rev]:
							del self.snoop_buffer[addr_tup_rev][i]
					self.snoop_buffer[addr_tup_rev]['last_ack'] = packet['transport']['ack_num']
					soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
					soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
					soc.close()
					if packet['transport']['seq_num'] in self.transmission_log:
						self.transmission_log[packet['transport']['seq_num']] += 1
					else:
						self.transmission_log[packet['transport']['seq_num']] = 1
				elif packet['transport']['ack_num'] == self.snoop_buffer[addr_tup_rev]['last_ack'] and packet['transport']['ack_num'] in self.snoop_buffer[addr_tup_rev]:
					print(packet['transport']['ack_num'], "hit")
					snooped_pkt = self.snoop_buffer[addr_tup_rev][packet['transport']['ack_num']]
					snooped_pkt['transport']['snooped'] = True
					soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
					fwd_to = self.routes[(snooped_pkt['dst_IP'], snooped_pkt['dst_port'])]
					soc.sendto(json.dumps(snooped_pkt).encode("utf-8"), fwd_to)
					soc.close()
					if snooped_pkt['transport']['seq_num'] in self.transmission_log:
						self.transmission_log[snooped_pkt['transport']['seq_num']] += 1
					else:
						self.transmission_log[snooped_pkt['transport']['seq_num']] = 1
				else:
					soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
					soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
					soc.close()	
					if packet['transport']['seq_num'] in self.transmission_log:
						self.transmission_log[packet['transport']['seq_num']] += 1
					else:
						self.transmission_log[packet['transport']['seq_num']] = 1
		else:
			soc = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
			soc.sendto(json.dumps(packet).encode("utf-8"), forward_to)
			soc.close()
			if packet['transport']['seq_num'] in self.transmission_log:
				self.transmission_log[packet['transport']['seq_num']] += 1
			else:
				self.transmission_log[packet['transport']['seq_num']] = 1

	
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
		soc_etx = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
		
		while True:
			probe_pkt = self.probe_buffer.get()
			# print(probe_pkt)
			# Put the probe packet in the appropriate queue address
			recv_addr = probe_pkt["src_IP"], probe_pkt["src_port"]
			etx_num = probe_pkt["transport"]['etx_num']
			reply_pkt = packet.Packet.etx_packet(self.addr,	 # Source address
										recv_addr,				 # Destination address
										etx_num = etx_num, # ETX value
										reply = True
										)
			soc_etx.sendto(json.dumps(reply_pkt).encode("utf-8"), recv_addr)

			# self.etx_queues[recv_addr].put(etx_num)
			
	
	def etx_probing(self, addr):
		# implement probing algorithm here, feel free to make any additional class functions as needed
		# you will need a separate thread to listen to probe packets, span it from init as you need it
		# this function runs in separate thread for each neighbour, in each thread you are probing node with (host, port)=addr
		# you will update the etx for this addr by updating self.etxs[addr], which is initialy set to 1 (see init)

		# Get system clock to sync the while loop
		starttime = time.time()
		
		# Initial ETX
		probe_etx = self.etxs[addr]
		
		# Represent the last 100 packets in a list. 1 means a packet received in that one second period. A 0 means no packet.
		pkt_list = [1] * 100
		soc_etx = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

		# check if the neighbouring node is up yet 
		while True:
			check_pkt = packet.Packet.etx_packet(self.addr,
												addr,
												etx_num = 0)
			soc_etx.sendto(json.dumps(check_pkt).encode("utf-8"), addr)
			try:
				reply = self.etx_queues[addr].get(timeout=self.etx_timeout)
			# reply = self.etx_queues[addr].get()
				break
			except:
				pass

		with self.etx_queues[addr].mutex:
			self.etx_queues[addr].queue.clear()
		print("Starting etx probing on", addr)
		# Send and receive probe packets 
		while True:
			# Create the probe packet
			etx_num = random.randrange(100000)
			probe_pkt = packet.Packet.etx_packet(self.addr,	 # Source address
										addr,				 # Destination address
										etx_num = etx_num # ETX value
										)
			
			# Send the ETX probe packet
			soc_etx.sendto(json.dumps(probe_pkt).encode("utf-8"), addr)
			#print('pkt sent')
			
			# Receive a probe packet from the queue
			success = False
			try:
				reply = self.etx_queues[addr].get(timeout=self.etx_timeout)
				if reply["transport"]["etx_num"] == etx_num:
					success = True
				else:
					while not self.etx_queues[addr].empty():
						reply = self.etx_queues[addr].get()
						if reply["transport"]['etx_num'] == etx_num:
							success = True
			except:
				success = False

			if success:
				pkt_list.append(1)
			else:
				pkt_list.append(0)
			if len(pkt_list) >= 100:
				pkt_list.pop(0)
			# if not self.etx_queues[addr].empty():
			# 	probe_etx = self.etx_queues[addr].get()
			# 	# Say that this is a received packet
			# 	#print('pkt rcv')
			# else: 
			# 	# A packet was not received
			# 	pkt_list.append(0)
				
			# # Remove the first packet in the list
			# pkt_list.pop(0)
			
			# Update the ETX between the current node (here) to the neighbor node
			# TODO: divide by zero?
			pkt_probability = (1 - sum(pkt_list) / len(pkt_list)) # * (1 - (probe_etx / len(pkt_list)))
			self.etxs[addr] = pkt_probability #1 / pkt_probability
			# print(addr, self.etxs[addr])
			#print(self.addr, self.etxs[addr])
			
			# Lock the packet sending to the system clock and run every second
			time.sleep(0.1)
			
		