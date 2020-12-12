import matplotlib.pyplot as plt
import numpy as np
import json
import sys
import config


exps = sys.argv[1:]
MTU = 600
addrs = config.addrs
sender = config.sender
recvr = config.recvr

def throughput(timestamps):
	# print(timestamps[0], timestamps[-1])
	start = int(timestamps[0])
	end = int(timestamps[-1])
	thrpts = [0 for i in range(start, end + 1)]
	for t in timestamps:
		# print(start, int(t), end, t)
		thrpts[int(t) - start] += MTU
	return thrpts


def cwnd_ssthresh(cwst):
	return [c[0] for c in cwst], [c[1] for c in cwst]

def merge_and_count(dicts):
	d = {}
	for e in dicts:
		for i in e.keys():
			if i in d:
				d[i] += e[i]
			else:
				d[i] = e[i]
	tx = []
	for i in d.keys():
		tx.append(d[i])
	print(sorted(tx)[-250:])
	return sorted(tx)[:-1]

def cdf(x):
    x, y = sorted(x), np.arange(len(x)) / len(x)
    return (x, y)

def plot_throughputs(exps):
	plt.figure()
	for exp in exps:
		filename = exp+"_"+recvr[0]+"_"+str(recvr[1])+"_thrpt.txt"
		timestamps = np.loadtxt(filename)
		thrpt = throughput(timestamps)
		plt.plot(thrpt, label = exp)
	plt.xlabel("Time (s)")
	plt.ylabel("Throughput (Bytes)")
	plt.title("Throughput")
	plt.legend()
	plt.savefig("throughput.png")

def plot_cwnd_ssthresh(exps):
	plt.figure()
	for exp in exps:
		filename = exp+"_"+sender[0]+"_"+str(sender[1])+"_cwnd.txt"
		cwst = np.loadtxt(filename)
		cwnd, ssthresh = cwnd_ssthresh(cwst)
		plt.plot(cwnd, label = exp+" cwnd")
		plt.plot(ssthresh, "-.", label = exp+" ssthresh")
	plt.xlabel("Time (s)")
	plt.ylabel("Number of packets")
	plt.title("cwnd and ssthresh")
	plt.legend()
	plt.savefig("cwnd_ssthresh.png")

def plot_tranmissions(exps):
	plt.figure()
	for exp in exps:
		dicts = []
		for node in addrs:
			filename = exp+"_"+node[0]+"_"+str(node[1])+"_transmission_log.txt"
			with open(filename, 'r') as j:
				d = json.loads(j.read())
				dicts.append(d)
		transmissions = merge_and_count(dicts)
		cdfx, cdfy = cdf(transmissions)
		plt.plot(cdfx, cdfy, label = exp)
		# plt.plot(ssthresh, "-.", label = exp+" ssthresh")
	plt.xlabel("# transmissions")
	plt.ylabel("CDF")
	plt.title("Number of transmissions per packet")
	plt.legend()
	plt.savefig("transmissions.png")


plot_throughputs(exps)
plot_cwnd_ssthresh(exps)
plot_tranmissions(exps)