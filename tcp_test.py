
import routing
import packet
import sys
import queue
import threading
import hashlib

config = int(sys.argv[1])
#config = 1

def recv_and_ack():
	while True:
		packet = r.pass_on_buffer.get()
        # print the data received
		print(packet["transport"]["data"])
        
        # Check if the the source was 
        
        
# Initialize routing and threads
r = routing.Routing(10, config)
threading.Thread(target=recv_and_ack).start()

# Check for additional arguments: host and port
if len(sys.argv) > 2:
    dest_addr = sys.argv[2]
    dest_port = int(sys.argv[3])
    
    alph = ["a", "b", "c", "d", "e", "f"]
    alph = [a * 650 for a in alph]
    
    # Calculate the data and window size
    data_len = [sys.getsizeof(a) for a in alph]
    window_size = sum(data_len)
    
    # Initialize the packet sequence number in the window
    sequence_num = 1
    
    # Create and prepare the packets
    for data, data_size in zip(alph, data_len):

        # Create the packet object
        p = packet.Packet()
        
        # Add data to the packet
        p.add_data(data)
        
        # Add TCP layer information
        p.add_TCP_layer(r.addr[1], 
                        dest_port, 
                        hashlib.md5(data.encode("utf-8")).hexdigest(),
                        seq_num = sequence_num,
                        ack_num = data_size + 1,
                        segment_len = data_size,
                        window = window_size,
                        syn = True,
                        ack = True,
                        )
        
        # Update the sequence number
        sequence_num += data_size
        
        # Add IP protocol information        
        p.add_IP_layer(r.addr[0], r.addr[1], dest_addr, dest_port)
        
        # Create the packet and send across the router
        pkt = p.generate_packet()
        
        # Send the data through the TCP window (which is the for loop)
        print("Sending to:", dest_addr, dest_port)
        print(pkt)
        r.send(pkt)
        