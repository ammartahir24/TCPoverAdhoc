import routing
import packet
import sys
import queue
import random
import threading
import hashlib
import time


class ClientSocket:
	def __init__(self, addr, sender_addr, tcp_socket, seq_num, ack_num, rwnd_size, rtt):
		self.SACK = True
		self.sender_addr = sender_addr[0]
		self.sender_port = sender_addr[1]
		self.addr = addr
		self.tcp_socket = tcp_socket
		self.seq_num = seq_num
		self.base_seq_num = seq_num
		self.curr_ack = seq_num
		self.ack_num = ack_num
		self.shift_back = False
		self.make_update = False
		self.packets_in_trst = 0
		self.ack_to_update = self.seq_num
		self.i = 0
		self.sacked = []
		self.rwnd_size = 100
		self.cwnd_size = 1
		self.ssthresh = rwnd_size
		self.rwnd_recv = rwnd_size
		self.MTU = 600
		self.rtt = 0.1
		if rtt < 0.01:
			self.rtt = 0.01
		self.rto = self.rtt * 40
		# Receive window
		self.rwnd = queue.SimpleQueue()
		# Receieve packets and respond with ACKs
		threading.Thread(target = self.poll).start()


	def handle_acks(self, num_of_chunks):
		# self.ack_to_update
		# self.last_wnd
		# self.packets_in_trst
		# self.curr_ack = self.seq_num
		# self.i = 0
		dup_acks = 0
		# print("handle_acks")
		while self.curr_ack < self.seq_num + num_of_chunks:
			time.sleep(0.0001)
			if self.packets_in_trst > 0:
				try:
					ack_packet = self.tcp_socket.get_acks((self.sender_addr, self.sender_port), timeout=self.rto)
					# print(self.ack_to_update, ack_packet['ack_num'], self.curr_ack, self.packets_in_trst)
					if ack_packet['ack_num'] >= self.ack_to_update:
						# self.seq_num = self.ack_to_update
						self.packets_in_trst -= (ack_packet['ack_num'] - self.curr_ack)
						self.curr_ack = ack_packet['ack_num']
						self.rwnd_recv = ack_packet['window']
						if self.cwnd_size < self.ssthresh:
							self.cwnd_size *= 2
						else:
							self.cwnd_size += 1
						print("Successful delivery.")
						print(self.ssthresh, self.cwnd_size)
						self.make_update = True
						self.ack_to_update += self.cwnd_size
						dup_acks = 0
						if self.SACK:
							self.sacked = self.decompress(ack_packet['sack'])
						# break
					elif ack_packet['ack_num'] > self.curr_ack:
						self.packets_in_trst -= (ack_packet['ack_num'] - self.curr_ack)
						self.curr_ack = ack_packet['ack_num']
						self.rwnd_recv = ack_packet['window']
						dup_acks = 0
						if self.SACK:
							self.sacked = self.decompress(ack_packet['sack'])
					elif ack_packet['ack_num'] == self.curr_ack:
						dup_acks += 1
						self.rwnd_recv = ack_packet['window']
						if self.SACK:
							self.sacked = self.decompress(ack_packet['sack'])
						if dup_acks == 3:
							self.shift_back = True
							self.i = (self.curr_ack - self.seq_num)
							self.ssthresh = int(1 + self.cwnd_size/2)
							self.cwnd_size = self.ssthresh
							self.packets_in_trst = 0
							self.ack_to_update = self.i + self.seq_num + self.cwnd_size
							print("dupacks.")
							print(self.ssthresh, self.cwnd_size)
						# break
				except:
					self.shift_back = True
					self.i = (self.curr_ack - self.seq_num)
					# self.seq_num = curr_ack
					self.ssthresh = int(1 + self.cwnd_size/2)
					self.cwnd_size = 1
					self.packets_in_trst = 0
					self.ack_to_update = self.i + self.seq_num + self.cwnd_size
					print("packet loss due to timeout", self.i, (self.curr_ack - self.seq_num))
					print(self.ssthresh, self.cwnd_size)
					# break

	def send(self, data):
		# packetize data: make chunks and put them in packets DONE
		# make TCP packets using data chunks and addresses, add IP layer too DONE
		# send each packet using self.tcp_socket.put() function, get acks by calling function self.tcp_socket.get_acks(self.sender_addr)
		# manage sends and acks here
		
		chunks = self.make_chunks(data)
		self.ack_to_update = self.seq_num + self.cwnd_size
		threading.Thread(target = self.handle_acks, args=(len(chunks),)).start()
		i = 0
		self.seq_num = self.curr_ack
		while self.curr_ack < self.seq_num + len(chunks):
			if self.SACK and (self.seq_num + i) in self.sacked:
				i += 1
				continue
			time.sleep(0.0001)
			pkts_to_send = min(self.rwnd_recv, (self.cwnd_size - self.packets_in_trst))
			# print(pkts_to_send, "to send")
			if pkts_to_send > 0:
				# for j in range(pkts_to_send):
				if self.make_update:
					# self.last_wnd = pkts_to_send
					# self.ack_to_update = self.seq_num + i + self.cwnd_size
					self.make_update = False

				if self.shift_back:
					i = self.i
					self.ack_to_update = self.seq_num + i + self.cwnd_size
					self.make_update = False
					self.shift_back = False

				if i < len(chunks):
					data_pkt = packet.Packet.data_packet(chunks[i], self.addr, (self.sender_addr, self.sender_port), self.seq_num+i, self.ack_num, self.rwnd_size)
					self.tcp_socket.put(data_pkt)
					self.packets_in_trst += 1
					i += 1
				# curr_ack = self.seq_num
				# dup_acks = 0
				# while True:
				# 	try:
				# 		ack_packet = self.tcp_socket.get_acks((self.sender_addr, self.sender_port), timeout=self.rto)
				# 		if ack_packet['ack_num'] == (self.seq_num + pkts_to_send):
				# 			self.seq_num += pkts_to_send
				# 			self.rwnd_recv = ack_packet['window']
				# 			i += pkts_to_send
				# 			if pkts_to_send == self.cwnd_size and self.cwnd_size < self.ssthresh:
				# 				self.cwnd_size *= 2
				# 			elif pkts_to_send == self.cwnd_size:
				# 				self.cwnd_size += 1
				# 			print("Successful delivery.")
				# 			print(self.ssthresh, self.cwnd_size)
				# 			break
				# 		if ack_packet['ack_num'] > curr_ack:
				# 			# print("larger ack", curr_ack, ack_packet['ack_num'])
				# 			curr_ack = ack_packet['ack_num']
				# 			dup_acks = 0
				# 		elif ack_packet['ack_num'] == curr_ack:
				# 			dup_acks += 1
				# 			if dup_acks >= 3:
				# 				i = (curr_ack - self.base_seq_num)
				# 				self.ssthresh = int(self.cwnd_size/2)
				# 				self.cwnd_size = self.ssthresh
				# 				print("3 dupacks.")
				# 				print(self.ssthresh, self.cwnd_size)
				# 				break
				# 	except:
				# 		print("packet loss due to timeout", i, (curr_ack - self.base_seq_num))
				# 		i = (curr_ack - self.base_seq_num)
				# 		self.seq_num = curr_ack
				# 		self.ssthresh = int(self.cwnd_size/2)
				# 		self.cwnd_size = 1
				# 		print(self.ssthresh, self.cwnd_size)
				# 		break
			# else:
			# 	ack_packet = self.tcp_socket.get_acks((self.sender_addr, self.sender_port))
			# 	self.rwnd_recv = ack_packet['window']
			# i += 1
		

	def compress(self, sacks):
		if sacks == []: 
			return []
		nums = []
		sacks = sorted(sacks)
		prev = sacks[0]
		nums.append(prev)
		for i in sacks[1:]:
			if i != prev+1:
				nums.append(prev)
				nums.append(i)
				prev = i
			else:
				prev += 1
		nums += [prev]
		if len(nums) > 10:
			return nums[:10]
		return nums

	def decompress(self, nums):
		if nums == []:
			return []
		sacks = []
		for i in range(int(len(nums)/2)):
			sacks += [nums[2*i]+k for k in range(nums[2*i+1] - nums[2*i] + 1)]
		return sacks

	def recv(self, num_of_chunks):
		data = self.rwnd.get()
		num_of_chunks -= 1
		self.rwnd_size += 1
		# print("tcp -> recv")
		# if self.rwnd.empty():
		# 	while num_of_chunks > 0:
		# 		print("tcp -> recv -> empty queue wait")
		# 		d = self.rwnd.get()
		# 		data += d
		# 		num_of_chunks -= 1
		# 		self.rwnd_size += 1
		# 	return data
		while num_of_chunks > 0:
			try:
				d = self.rwnd.get(block=True, timeout=self.rto*4)
				data += d
				num_of_chunks -= 1
				self.rwnd_size += 1
			except:
				return data
		return data
		

	def poll(self):
		sender_addr_port = (self.sender_addr, self.sender_port)
		addr = self.tcp_socket.addr
		out_of_order = queue.PriorityQueue()
		sack = []
		while True:
			# Retrieve the packet from the queue
			pkt = self.tcp_socket.get((self.sender_addr, self.sender_port))
			seq_num = pkt['seq_num']
			
			# If the packet is the next one needed in the sequence, update the pointer and insert into the window
			if seq_num == self.ack_num:
				print(seq_num, "received")
				self.ack_num = seq_num + 1 
				# buffer_t += pkt['data']
				self.rwnd.put(pkt['data'])
				self.rwnd_size -= 1

				# SACK
				if self.SACK and not out_of_order.empty():
					print("Came here")
					pn, pkt2 = out_of_order.get()
					while pkt2['seq_num'] == self.ack_num:
						self.ack_num = pkt2['seq_num'] + 1
						self.rwnd.put(pkt2['data'])
						self.rwnd_size -= 1
						sack.remove(pkt2['seq_num'])
						if out_of_order.empty():
							break
						else:
							pn, pkt2 = out_of_order.get()
					if pkt2['seq_num'] != self.ack_num - 1:
						out_of_order.put((pn, pkt2))

				# Create the ACK
				window = self.rwnd_size
				ack = packet.Packet().ack_packet(self.addr, 
					   sender_addr_port,
					   self.seq_num,
					   self.ack_num,
					   window = window)
				
				# Send the ACK
				self.tcp_socket.put(ack)
				
				if window <= 0:
					while self.rwnd_size <= 0:
						continue
					window = self.rwnd_size
					ack = packet.Packet().ack_packet(self.addr, 
						   sender_addr_port,
						   self.seq_num,
						   self.ack_num,
						   window = window,
						   sack = self.compress(sack))
					self.tcp_socket.put(ack)


			elif seq_num > self.ack_num:
				# Probably a duplicate packet or a SACK packet
				print("Out of order packet", seq_num, self.ack_num)
				window = self.rwnd_size
				sack.append(seq_num)
				ack = packet.Packet().ack_packet(self.addr, 
					   sender_addr_port,
					   self.seq_num,
					   self.ack_num,
					   window = window,
					   sack = self.compress(sack))
				# Send the ACK
				self.tcp_socket.put(ack)
				# SACK
				if self.SACK and not any(pkt['seq_num'] in item for item in out_of_order.queue):
					out_of_order.put((pkt['seq_num'], pkt))
			else:
				print(seq_num, "received. Expected:", self.ack_num)
				# ack = packet.Packet().ack_packet(self.addr, 
				# 	   sender_addr_port,
				# 	   self.seq_num,
				# 	   self.ack_num,
				# 	   window = window,
				# 	   sack = self.compress(sack))
				
				# # Send the ACK
				# self.tcp_socket.put(ack)
				# # Check buffer for next packet
				# # discard
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
	

	def close(self):
		# exchange fin packets here
		self.tcp_socket.delete((self.sender_addr, self.sender_port))
		self.poll.join()


class TCPSocket:
	def __init__(self, i):
		self.routing = routing.Routing(50, i)
		self.addr = self.routing.addr
		self.queues = {}
		self.queues[1] = queue.SimpleQueue()
		self.ack_queues = {}
		self.default_rwnd = 50
		threading.Thread(target = self.listener).start()


	def listener(self):
		while True:
			data, addr = self.routing.recv()
			# print("tcp.TCPSocket: ", data, addr)
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
		start_time = time.time_ns()
		self.put(syn_ack_packet)
		ack_packet = self.get_acks(addr)
		end_time = time.time_ns()
		rtt = (end_time - start_time) / (10**9)
		seq_num = seq_num + 1
		conn = ClientSocket(self.addr, addr, self, seq_num, ack_num, self.default_rwnd, rtt)
		return conn, addr

	def connect(self, addr):
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		# done: send a syn packet, wait for syn-ack, then send an ack packet, if successful return conn object otherwise error
		seq_num = random.randrange(100000)
		syn_packet = packet.Packet.syn_packet(self.addr, addr, seq_num, self.default_rwnd)
		start_time = time.time_ns()
		self.put(syn_packet)
		syn_ack_packet = self.get_acks(addr)
		end_time = time.time_ns()
		rtt = (end_time - start_time) / (10**9)
		ack_num = syn_ack_packet['seq_num'] + 1
		seq_num = seq_num + 1
		ack_packet = packet.Packet.ack_packet(self.addr, addr, seq_num, ack_num, self.default_rwnd)
		self.put(ack_packet)
		conn = ClientSocket(self.addr, addr, self, seq_num, ack_num, self.default_rwnd, rtt)
		return conn
		

	def get(self, addr):
		return self.queues[addr].get()

	def put(self, data):
		# print("Sending", data)
		self.routing.send(data)

	def get_acks(self, addr, timeout=None):
		return self.ack_queues[addr].get(timeout=timeout)

	def delete(self, addr):
		del self.queues[addr]
		del self.ack_queues[addr]
		