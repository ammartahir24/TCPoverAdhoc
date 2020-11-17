import routing
import packet
import sys
import queue
import threading
import hashlib


class ClientSocket:
	def __init__(self, sender_addr, sender_port, tcp_socket):
		self.sender_addr = sender_addr
		self.sender_port = sender_port
		self.tcp_socket = tcp_socket
		self.leftover = ""

	def send(self, data):
		# packetize data: make chunks and put them in packets DONE
		# make TCP packets using data chunks and addresses, add IP layer too DONE
		# send each packet using self.tcp_socket.put() function, get acks by calling function self.tcp_socket.get_acks(self.sender_addr)
		# manage sends and acks here
		
		# Intitialize window
		# Pointer for ACK'd packets in bytes
		snd_una = 1
		# Pointer for bytes of packets to be sent
		snd_next = 1
		
		# Split and packetize data
		pkt_buffer = self.packetize(data)
		
		# Total bytes of data to be sent (based on the last packet's ACK number)
		total_bytes = pkt_buffer[-1]['transport']['ack_num'] - 1
		
		# Start the send window
		while snd_una <= total_bytes:
			
			# Send the packets
			for pkt in pkt_buffer:
				
				# Send the packet in the buffer through the TCP Socket
				self.tcp_socket.put(pkt)
				
				# Update snd_next
				snd_next += pkt['transport']['ack_num'] - pkt['transport']['seq_num']
				print("snd_next", snd_next)
				
				if snd_next == total_bytes + 1:
					# self.close()
					print("Transmission complete!")
				
			# Get ACKs

	def recv(self, num_of_bytes):
		# call self.tcp_socket.get(self.sender_addr) to get any received data for this connection
		# fill up a local buffer with this data until data = num_of_bytes is not received
		# save leftover data in self.leftover to be used in following called to recv
		# for each packet you make call to get for, send back an ack to sender
		hi = 5
		
		
	def packetize(self, data):
			
		PACKET_LIMIT = packet.Packet().packet_size
		packet_size = 0
		# Initialize the sequence number
		seq_num = 1
		# Overflow start at element 0
		overflow_i = 0
		# Storage of packetized version of data
		pkt_buffer = []
		sender_port = self.sender_port
		sender_addr = self.sender_addr
		addr = self.tcp_socket.addr
		
		# packetize the data
		# TODO: Check the final packet for overflow??
		for i, e in enumerate(data):
			# Count up until a given packet size. If it hits the PACKET_LIMIT make a new packet
			if packet_size + sys.getsizeof(e) < PACKET_LIMIT and e is not data[-1]:
				packet_size += sys.getsizeof(e)
			else:
				# Create the packet object
				p = packet.Packet(size = packet_size)
				
				# Get a slice of the data from the whole
				# Preprocess the data by adding a separator for the strings and joining
				if e is data[-1]:
					data_segment = '\n'.join(data[overflow_i:i+1])
					# Increase the packet size for the final packet
					packet_size += sys.getsizeof(e)
				else:
					data_segment = '\n'.join(data[overflow_i:i])
				
				# Add data to the packet
				p.add_data(data_segment)
	
				# Add TCP layer information
				p.add_TCP_layer(addr[1],
								sender_port,
								hashlib.md5(data_segment.encode("utf-8")).hexdigest(),
								seq_num = seq_num,
								ack_num = seq_num + packet_size,
								)
				
				# Add IP information
				p.add_IP_layer(addr[0], addr[1], sender_addr, sender_port)
				
				# Update the sequence number
				seq_num += packet_size
				
				# Finalize the packet
				pkt = p.generate_packet()
				
				# Store the packets in the a list
				pkt_buffer.append(pkt)
				
				# This element exceeds the the PACKET_LIMIT, therefore remember the element and add a flag to remember to include it in the next packet
				overflow_i = i

				# Reset packet size
				packet_size = sys.getsizeof(data[overflow_i])
		
		# print("This is the buffer:", pkt_buffer)
		return pkt_buffer
	

	def close(self):
		# exchange fin packets here
		self.tcp_socket.delete(self.sender_addr)


class TCPSocket:
	def __init__(self, i):
		self.routing = routing.Routing(10, i)
		self.addr = self.routing.addr
		self.queues = {}
		self.ack_queues = {}
		threading.Thread(target = self.listener).start()


	def listener(self):
		while True:
			data, addr = self.routing.recv()
			if addr in self.queues:
				if data['ack'] == True:
					self.ack_queues[addr].put(data)
				self.queues[addr].put(data)
			else:
				self.queues[1].put((data, addr))

	def accept(self):
		syn_pkt, addr = self.queues[1].get()
		# do three way handshake here
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		conn = ClientSocket(addr, self)
		return conn, addr

	def connect(self, addr):
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		# send a syn packet, wait for syn-ack, then send an ack packet, if successful return conn object otherwise error
		conn = ClientSocket(addr, self)
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
		