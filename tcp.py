import routing
import packet
import sys
import queue
import threading
import hashlib


class ClientSocket:
	def __init__(self, sender_addr, tcp_socket):
		self.sender_addr = sender_addr
		self.tcp_socket = tcp_socket
		self.leftover = ""

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

	def put(self, addr, data):
		self.routing.send(data)

	def get_acks(self, addr):
		return self.ack_queues[addr].get()

	def delete(self, addr):
		del self.queues[addr]
		del self.ack_queues[addr]