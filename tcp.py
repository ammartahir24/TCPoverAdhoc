import routing
import packet
import sys
import queue
import random
import threading
import hashlib
import time


class ClientSocket:
	def __init__(self, addr, sender_addr, tcp_socket, seq_num, ack_num, rwnd_size):
		self.sender_addr = sender_addr[0]
		self.sender_port = sender_addr[1]
		self.addr = addr
		self.tcp_socket = tcp_socket
		self.seq_num = seq_num
		self.ack_num = ack_num
		self.rwnd_size = rwnd_size
		self.cwnd_size = 1
		self.ssthresh = rwnd_size
		self.MTU = 600
		self.rto = 0.05
		# Receive window
		self.rwnd = queue.SimpleQueue()
		# Receieve packets and respond with ACKs
		threading.Thread(target = self.poll).start()

	def send(self, data):
		# packetize data: make chunks and put them in packets DONE
		# make TCP packets using data chunks and addresses, add IP layer too DONE
		# send each packet using self.tcp_socket.put() function, get acks by calling function self.tcp_socket.get_acks(self.sender_addr)
		# manage sends and acks here
		
		# Intitialize window buffer
		# Pointer for ACK'd packets in bytes
		snd_una = 1
		# Pointer for bytes of packets to be sent
		snd_next = 1
		# Send next index of the packet buffer
		snd_next_i = 0
		
		# Split and packetize data
		chunks = self.make_chunks(data)
		
		print(chunks)
		
		for chunk in chunks:
			data_pkt = packet.Packet.data_packet(chunk, self.addr, (self.sender_addr, self.sender_port), self.seq_num, self.ack_num, self.rwnd_size)
			self.tcp_socket.put(data_pkt)
			ack_packet = self.tcp_socket.get_acks((self.sender_addr, self.sender_port))
			self.seq_num += 1
		# # Total bytes of data to be sent (based on the last packet's ACK number)
		# total_bytes = pkt_buffer[-1]['transport']['ack_num'] # - 1
		
		# # Window start
		# # window_size = pkt_buffer[-1]['transport']['window']
		# window_size = self.rwnd_size
		
		# # Start the send progress
		# while snd_una <= total_bytes:
						
		# 	# Start the send window
		# 	while window_size >= snd_next - snd_una:
		# 		print(snd_next, snd_next_i, snd_una)
		# 		# Select the packet based on snd_next pointer index
		# 		pkt = pkt_buffer[snd_next_i]
				
		# 		# Send the packet in the buffer through the TCP Socket
		# 		self.tcp_socket.put(pkt)
				
		# 		print(pkt)
				
		# 		# Update the snd_next points
		# 		snd_next += pkt['transport']['ack_num'] - pkt['transport']['seq_num']
		# 		snd_next_i += 1
			
		# 	# Get ACKs after sending the packets
		# 	ack = self.tcp_socket.get_acks(self.sender_addr)
		# 	ack_num = ack['transport']['ack_num']
			
		# 	# Update snd_una if ACK is greater
		# 	if ack['transport']['ack_num'] > snd_una:
		# 		snd_una = ack_num
		
		# print("Data sending complete!")


	def recv(self, num_of_chunks):
		print("In recv")
		data = ""
		if self.rwnd.empty():
			print("empty queue")
			while num_of_chunks > 0:
				d = self.rwnd.get()
				data += d
				num_of_chunks -= 1
			return data
		while num_of_chunks > 0:
			try:
				d = self.rwnd.get_nowait()
				data += d
				num_of_chunks -= 1
			except:
				return data
		return data
		
	def poll(self):
		sender_addr_port = (self.sender_addr, self.sender_port)
		addr = self.tcp_socket.addr
		# Receieve window pointer
		# rcv_next = 1
		# Receive window
		#rwnd = self.rwnd
		# Packet buffer
		# buffer_t = ""
		
		# If the seq_num is last ACK + 1, accept. Otherwise, discard out of order
		while True:
			# Retrieve the packet from the queue
			pkt = self.tcp_socket.get((self.sender_addr, self.sender_port))
			seq_num = pkt['seq_num']
			
			# If the packet is the next one needed in the sequence, update the pointer and insert into the window
			if seq_num == self.ack_num:
				self.ack_num = seq_num + 1 
				# buffer_t += pkt['data']
				self.rwnd.put(pkt['data'])
				self.rwnd_size -= len(pkt['data'])
				
				# Create the ACK
				ack = packet.Packet().ack_packet(self.addr, 
					   sender_addr_port,
					   self.seq_num,
					   self.ack_num,
					   window = self.rwnd_size)
				
				# Send the ACK
				self.tcp_socket.put(ack)
				
			elif seq_num > rcv_next:
				# Probably a duplicate packet or a SACK packet
				print(seq_num, ' > ', rcv_next)
				pass
			else:
				# Check buffer for next packet
				# discard
				pass
			
		
	def make_chunks(self, data):
			
		PACKET_LIMIT = self.MTU
		packet_size = 0
		# Initialize the sequence number
		seq_num = 1
		# Overflow start at element 0
		overflow_i = 0
		# Storage of packetized version of data
		chunks = []
		pkt_buffer = []
		sender_port = self.sender_port
		sender_addr = self.sender_addr
		addr = self.tcp_socket.addr
		
		# packetize the data
		num_chunks = int(len(data) / PACKET_LIMIT)
		for i in range(num_chunks):
			chunks.append(data[i*PACKET_LIMIT:i*PACKET_LIMIT+PACKET_LIMIT])
		chunks.append(data[num_chunks*PACKET_LIMIT:])

		return chunks
		# TODO: Check the final packet for overflow??
		# for i, e in enumerate(data):
		# 	# Count up until a given packet size. If it hits the PACKET_LIMIT make a new packet
		# 	if packet_size + sys.getsizeof(e) < PACKET_LIMIT and e is not data[-1]:
		# 		packet_size += sys.getsizeof(e)
		# 	else:
		# 		# Create the packet object
		# 		p = packet.Packet()
				
		# 		# Get a slice of the data from the whole
		# 		# Preprocess the data by adding a separator for the strings and joining
		# 		if e is data[-1]:
		# 			data_segment = '\n'.join(data[overflow_i:i+1])
		# 			# Increase the packet size for the final packet
		# 			packet_size += sys.getsizeof(e)
		# 		else:
		# 			data_segment = '\n'.join(data[overflow_i:i])
				
		# 		# Add data to the packet
		# 		p.add_data(data_segment)
	
		# 		# Add TCP layer information
		# 		p.add_TCP_layer(addr[1],
		# 			sender_port,
		# 			hashlib.md5(data_segment.encode("utf-8")).hexdigest(),
		# 			seq_num = seq_num,
		# 			ack_num = seq_num + packet_size,
		# 			window = self.rwnd_size
		# 			)
				
		# 		# Add IP information
		# 		p.add_IP_layer(addr[0], addr[1], sender_addr, sender_port)
				
		# 		# Update the sequence number
		# 		seq_num += packet_size
				
		# 		# Finalize the packet
		# 		pkt = p.generate_packet()
				
		# 		# Store the packets in the a list
		# 		pkt_buffer.append(pkt)
				
		# 		# This element exceeds the the PACKET_LIMIT, therefore remember the element and add a flag to remember to include it in the next packet
		# 		overflow_i = i

		# 		# Reset packet size
		# 		packet_size = sys.getsizeof(data[overflow_i])
		
		# print("This is the buffer:", pkt_buffer)
		# return pkt_buffer
	

	def close(self):
		# exchange fin packets here
		self.tcp_socket.delete((self.sender_addr, self.sender_port))
		self.poll.join()


class TCPSocket:
	def __init__(self, i):
		self.routing = routing.Routing(10, i)
		self.addr = self.routing.addr
		self.queues = {}
		self.queues[1] = queue.SimpleQueue()
		self.ack_queues = {}
		self.default_rwnd = 5000
		threading.Thread(target = self.listener).start()


	def listener(self):
		while True:
			data, addr = self.routing.recv()
			print("tcp.TCPSocket: ", data, addr)
			if addr in self.queues:
				if data['ack'] == True:
					self.ack_queues[addr].put(data)
				else:
					self.queues[addr].put(data)
			else:
				self.queues[1].put((data, addr))

	def accept(self):
		syn_pkt, addr = self.queues[1].get()
		# done: do three way handshake here
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		seq_num = random.randrange(100000)
		ack_num = syn_pkt['seq_num'] + 1
		syn_ack_packet = packet.Packet.syn_ack_packet(self.addr, addr, seq_num, ack_num, self.default_rwnd)
		self.put(syn_ack_packet)
		ack_packet = self.get_acks(addr)
		seq_num = seq_num + 1
		conn = ClientSocket(self.addr, addr, self, seq_num, ack_num, self.default_rwnd)
		return conn, addr

	def connect(self, addr):
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		# done: send a syn packet, wait for syn-ack, then send an ack packet, if successful return conn object otherwise error
		seq_num = random.randrange(100000)
		syn_packet = packet.Packet.syn_packet(self.addr, addr, seq_num, self.default_rwnd)
		self.put(syn_packet)
		syn_ack_packet = self.get_acks(addr)
		ack_num = syn_ack_packet['seq_num'] + 1
		seq_num = seq_num + 1
		ack_packet = packet.Packet.ack_packet(self.addr, addr, seq_num, ack_num, self.default_rwnd)
		self.put(ack_packet)
		conn = ClientSocket(self.addr, addr, self, seq_num, ack_num, self.default_rwnd)
		return conn
		

	def get(self, addr):
		return self.queues[addr].get()

	def put(self, data):
		self.routing.send(data)

	def get_acks(self, addr):
		return self.ack_queues[addr].get()

	def delete(self, addr):
		del self.queues[addr]
		del self.ack_queues[addr]
		