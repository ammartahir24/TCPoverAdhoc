import sys
import json
import hashlib

class Packet:
	def __init__(self, size=1024):
		self.packet_size = size
		self.data = {}
		self.transport = {}
		self.ip = {}

	def add_data(self, data):
		self.data = data

	def add_IP_layer(self, src_IP, src_port, dst_IP, dst_port):
		self.ip = {
			"src_IP" : src_IP,
			"dst_IP" : dst_IP,
			"src_port" : src_port,
			"dst_port" : dst_port
		}

	def add_TCP_layer(self, src_port, dst_port, checksum, seq_num, ack_num, segment_len, window, syn=False, ack=False, ecn=False):
		self.transport = {
			"seq_num" : seq_num,
			"ack_num" : ack_num,
			"src_port" : src_port,
			"dst_port" : dst_port,
			"checksum" : checksum,
            "segment_length": segment_len,
			"window" : window,
			"syn" : syn,
			"ack" : ack,
			"ecn" : ecn
		}

	def add_UDP_layer(self, src_port, dst_port, checksum, ecn=False):
		self.transport = {
			"src_port" : src_port,
			"dst_port" : dst_port,
			"checksum" : checksum,
			"ecn" : ecn
		}

	def generate_packet(self):
		packet = self.ip
		packet["transport"] = self.transport
		packet["transport"]["data"] = self.data
		packet["transport"]["padding"] = ""
		size_temp = sys.getsizeof(json.dumps(packet).encode("utf-8"))
		packet["transport"]["padding"] = " " * (self.packet_size - size_temp)
		return packet

# p = Packet()
# data = ""
# p.add_data(data)
# p.add_UDP_layer(8000, 7000, hashlib.md5(data.encode("utf-8")).hexdigest())
# p.add_IP_layer("127.0.0.1", 8000, "127.0.0.1", 7000)
# packet = p.generate_packet()
# print(packet)