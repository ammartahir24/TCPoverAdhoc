import sys
import json
import hashlib

class Packet:
	def __init__(self, size = 1024):
		self.packet_size = size
		self.data = {}
		self.transport = {}
		self.ip = {}

	def add_data(self, data):
		self.data = data

	def add_IP_layer(self, src_IP, src_port, dst_IP, dst_port, ecn=False):
		self.ip = {
			"src_IP" : src_IP,
			"dst_IP" : dst_IP,
			"src_port" : src_port,
			"dst_port" : dst_port,
			"ecn" : ecn
		}

	def add_TCP_layer(self, src_port, dst_port, checksum, seq_num, ack_num, window, syn=False, ack=False, fin=False, sack = [], snoop=False):
		self.transport = {
			"seq_num" : seq_num,
			"ack_num" : ack_num,
			"src_port" : src_port,
			"dst_port" : dst_port,
			"checksum" : checksum,
			"window" : window,
			"syn" : syn,
			"ack" : ack,
			"fin" : fin,
			"sack" : sack,
			"snoop" : snoop,
			"pkt_effort" : 1,
			"pkt_qos" : 1,
			"success_prob": 1,
			"snooped": False,
			"etx" : False,
			"reply" : False,
			"etx_num" : 0,
			"dupack" : True,
			"snoop_mode" : 0,
			"snoop_at" : -1
		}

	def add_UDP_layer(self, src_port, dst_port, checksum):
		self.transport = {
			"src_port" : src_port,
			"dst_port" : dst_port,
			"checksum" : checksum
		}

	def generate_packet(self):
		packet = self.ip
		packet["transport"] = self.transport
		packet["transport"]["data"] = self.data
		packet["transport"]["padding"] = ""
		size_temp = sys.getsizeof(json.dumps(packet).encode("utf-8"))
		packet["transport"]["padding"] = " " * (self.packet_size - size_temp)
        
		return packet

#	def generate_ack(packet):
#		ack = {}
#		ack['dst_IP'] = packet['src_IP']
#		ack['dst_port'] = packet['src_port']
#		ack['src_IP'] =  packet['dst_IP'] 
#		ack['src_IP'] = packet['dst_port']
#		
#		# The ACK is the packet's sequence number + length
#		ack['ack'] = packet['transport']['seq_num'] + packet['transport']['segment_Length']
#		ack['sack'] = False
#		
#		return ack
		
	@staticmethod
	def etx_packet(addr, recv_addr, etx_num, reply=False):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		# Add etx information
		packet["transport"]["etx"] = True
		packet["transport"]["reply"] = reply
		packet["transport"]["etx_num"] = etx_num
		return packet

	@staticmethod
	def syn_packet(addr, recv_addr, seq_num, window):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, 0, window, syn=True)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet

	@staticmethod
	def syn_ack_packet(addr, recv_addr, seq_num, ack_num, window):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, ack_num, window, syn=True, ack=True)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet

	@staticmethod
	def ack_packet(addr, recv_addr, seq_num, ack_num, window, sack=[], snoop=False):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, ack_num, window, ack=True, sack=sack, snoop=snoop)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet

	@staticmethod
	def data_packet(data, addr, recv_addr, seq_num, ack_num, window, snoop=False):
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, ack_num, window, snoop=snoop)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet

	@staticmethod
	def fin_packet(addr, recv_addr, seq_num, ack_num, window):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, ack_num, window, fin=True)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet

	@staticmethod
	def fin_ack_packet(addr, recv_addr, seq_num, ack_num, window):
		data = ""
		p = Packet()
		p.add_data(data)
		p.add_TCP_layer(addr[1], recv_addr[1], hashlib.md5(data.encode("utf-8")).hexdigest(), seq_num, ack_num, window, fin=True, ack=True)
		p.add_IP_layer(addr[0], addr[1], recv_addr[0], recv_addr[1])
		packet = p.generate_packet()
		return packet
	
# p = Packet()
# data = ""
# p.add_data(data)
# p.add_UDP_layer(8000, 7000, hashlib.md5(data.encode("utf-8")).hexdigest())
# p.add_IP_layer("127.0.0.1", 8000, "127.0.0.1", 7000)
# packet = p.generate_packet()
# print(packet)