import routing
import packet
import sys
import queue
import random
import threading
import hashlib


class ClientSocket:
	def __init__(self, sender_addr, tcp_socket, seq_num, ack_num, rwnd):
		self.sender_addr = sender_addr
		self.tcp_socket = tcp_socket
		self.leftover = ""
		self.seq_num = seq_num
		self.ack_num = ack_num
		self.rwnd = rwnd

	def send(self, data):
		# packetize data: make chunks and put them in packets
		# make TCP packets using data chunks and addresses, add IP layer too
		# send each packet using self.tcp_socket.put() function, get acks by calling function self.tcp_socket.get_acks(self.sender_addr)
		# manage sends and acks here

	def recv(self, num_of_bytes):
		# call self.tcp_socket.get(self.sender_addr) to get any received data for this connection
		# fill up a local buffer with this data until data = num_of_bytes is not received
		# save leftover data in self.leftover to be used in following called to recv
		# for each packet you make call to get for, send back an ack to sender

	def close(self):
		# exchange fin packets here
		self.tcp_socket.delete(self.sender_addr)


class TCPSocket:
	def __init__(self, i):
		self.routing = routing.Routing(10, i)
		self.addr = self.routing.addr
		self.queues = {}
		self.ack_queues = {}
		self.fin_queues = {}
		self.default_rwnd = 5000
		threading.Thread(target = self.listener).start()


	def listener(self):
		while True:
			data, addr = self.routing.recv()
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
		self.put(addr, syn_ack_packet)
		ack_packet = self.get_acks(addr)
		seq_num = seq_num + 1
		conn = ClientSocket(addr, self, seq_num, ack_num, self.default_rwnd)
		return conn, addr

	def connect(self, addr):
		self.queues[addr] = queue.SimpleQueue()
		self.ack_queues[addr] = queue.SimpleQueue()
		# done: send a syn packet, wait for syn-ack, then send an ack packet, if successful return conn object otherwise error
		seq_num = random.randrange(100000)
		syn_packet = packet.Packet.syn_packet(self.addr, addr, seq_num, self.default_rwnd)
		self.put(addr, syn_packet)
		syn_ack_packet = self.get_acks(addr)
		ack_num = syn_ack_packet['seq_num'] + 1
		seq_num = seq_num + 1
		ack_packet = packet.Packet.ack_packet(self.addr, addr, seq_num, ack_num, self.default_rwnd)
		self.put(addr, ack_packet)
		conn = ClientSocket(addr, self, seq_num, ack_num, self.default_rwnd)
		return conn
		

	def get(self, addr):
		return self.queues[addr].get()

	def put(self, addr, data):
		self.routing.send(data)

	def get_acks(self, addr):
		return self.ack_queues[addr].get()

	def delete(self, addr):
		del self.queues[addr]
		del self.ack_queues[addr]