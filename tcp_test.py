

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
        
        # Create an ACK and send back to the packet's source
        ack = generate_ack(packet)
        
        # Send the ACK
        r.send(ack)
        
def generate_ack(packet):
    
        # Make a new packet, with the ACK flag set to True
        p = routing.Packet()
        
        # Reverse the recieved destination and source ports.
        dest_addr = packet['src_IP']
        dest_port = packet['src_port']
        src_addr =  packet['dst_IP'] 
        src_port = packet['dst_port']
        
        # The ACK is the packet's sequence number + length
        ack_num = packet['transport']['seq_num'] + packet['transport']['segment_Length']
        
        p.add_TCP_layer(src_port, 
                        dest_port, 
                        ack_num = ack_num,
                        ack = True,
                        )
        
        # Add IP protocol information        
        p.add_IP_layer(src_addr, src_port, dest_addr, dest_port)
        
        # Create the packet
        ack = p.generate_packet()
        
        # Send the data through the TCP window (which is the for loop)
        print("Sending ACK to:", dest_addr, dest_port)
        #        print(ack)
        #        r.send(ack)
        
        return ack
        
def send_sack(sack):
    r.send(sack)
    
def adjust_ack_window():
    # Get the ACK from the queue
    ack = r.ack_buffer.get()
    
    # Check the ACK against the window, represent the window as a list?
    
    
# Initialize routing and threads
r = routing.Routing(10, config)

# Generate a thread that listens for packets and sends an ACK for that packet
threading.Thread(target=recv_and_ack).start()

# Generate a thread that listens to ACKs and SACKs and adjusts the window? 
threading.Thread(target=adjust_ack_window).start()

# Data
alph = ["a", "b", "c", "d", "e", "f"]
alph = [a * 650 for a in alph]

# Intialize the ACK buffer

# Construct the window from receievd packets

# Read the ACKs and compare against the window

# If there is missing data in the window, then add a SACK and send back


# Check for additional arguments: host and port
if len(sys.argv) > 2:
    dest_addr = sys.argv[2]
    dest_port = int(sys.argv[3])
    
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
#                        ack_num = data_size + 1,
                        segment_len = data_size,
                        window = window_size,
                        syn = False,
                        ack = False,
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
        
        