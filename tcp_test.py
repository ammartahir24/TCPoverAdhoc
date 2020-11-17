

import routing
import packet
import sys
import queue
import threading
import hashlib

config = int(sys.argv[1])
#config = 1

def recv_window():
    
    recv_next = 1
    
    # Save the received packets, which are fully acknowledged, in a list
    window = []
    
    # Save all other packets
    buffer = []
    
    while True:
        # This is a simple queue, for it will wait until something gets put into the queue
        packet = r.pass_on_buffer.get()
        
        # print the data received (guaranteed)
        print(packet["transport"]["data"])
        
        # get the packet's sequence number
        seq_num = packet['transport']['seq_num'] 
        seg_length = packet['transport']['segment_Length']
        
        # Acknowledge the packet if this is the next one needed in the window
        if seq_num == recv_next:
            
            # Create an ACK and send back to the packet's source
            ack = generate_ack(packet)
            
            # Update the recv_next pointer
            recv_next += seg_length
            
            # Save the packet in sequence
            window.append(packet)
            
        # The ACK is somewhere ahead of recv_next and needs a SACK to be sent
        elif seq_num > recv_next: 
           
            # Generate a SACK
            ack = generate_ack(packet, sack = True)
        
            # Save this packet
            buffer.append(packet)
            
        # Send the acknowledgement packet
        r.send(ack)
            
        # Check the buffer
        # Check if the buffer is empty
        if not buffer:
            pass
        else:
            # Sort and loop over the buffer packets
            buffer.sort(key = lambda x: x['transport']['seq_num'], reverse = False)
            
            while buffer:
                
                x = buffer.pop(0)
                
                buff_num = x['transport']['seq_num'] 
                buff_length = x['transport']['segment_Length']
                
                if buff_num == recv_next:
                    
                    # Update the recv_next pointer
                    recv_next += buff_length
                    
                    # Save the packet in sequence
                    window.append(x)
        
        # Is the window complete?
        # Write something?
        
        
def generate_ack(packet, sack=False):
    
        # Make a new packet
        p = routing.Packet()
        
        # Reverse the recieved destination and source ports.
        dest_addr = packet['src_IP']
        dest_port = packet['src_port']
        src_addr =  packet['dst_IP'] 
        src_port = packet['dst_port']
        
        # Retrieve relevant ACK data
        seq_num = packet['transport']['seq_num'] 
        seg_length = packet['transport']['segment_Length']
        
        # this is an ACK packet
        if sack == False:
            # The ACK is the packet's sequence number + length
            ack_num = seq_num + seg_length
            
            p.add_TCP_layer(src_port, 
                            dest_port, 
                            ack_num = ack_num,
                            ack = True,
                            syn = sack,
                            )
        # this is a SACK packet
        else:
            p.add_TCP_layer(src_port, 
                            dest_port, 
                            ack_num = seq_num,
                            segment_len = seg_length,
                            ack = False,
                            syn = sack,
                            )
            
        # Add IP protocol information        
        p.add_IP_layer(src_addr, src_port, dest_addr, dest_port)
        
        # Create the packet
        ack = p.generate_packet()
        
        return ack
        
def send_sack(sack):
    r.send(sack)
    
def snd_window(data):
    
    # Get the ACK from the queue
    ack = r.ack_buffer.get()
    
    # Check the ACK against the window, represent the window as a list?
    
    
# Initialize routing and threads
r = routing.Routing(10, config)

# Generate a thread that listens for packets and sends an ACK for that packet
threading.Thread(target=recv_window).start()

# Generate a thread that listens to ACKs and SACKs and adjusts the window? 
threading.Thread(target=snd_window).start()

# Data
alph = ["a", "b", "c", "d", "e", "f"]
alph = [a * 650 for a in alph]

# Intialize the ACK buffer

# Construct the window from receievd packets

# Read the ACKs and compare against the window

# If there is missing data in the window, then add a SACK and send back

packets = []

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
        
        # Store the packets for this window, so it can be looked up in the window
        packets.append(pkt)
        
        # Send the data through the TCP window (which is the for loop)
        print("Sending to:", dest_addr, dest_port)
        print(pkt)
        r.send(pkt)
        
        