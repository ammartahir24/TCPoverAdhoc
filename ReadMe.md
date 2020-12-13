## Setup Details

On each of the raspberry pi, do this:

- Connect your pi to the internet

- Download any good text editor of your choice

- Install numpy and matplotlib

`pip install numpy matplotlib`

- Clone this repository, and run the code locally yo see if there are any dependencies you need to install

- Follow procedure on this [link](https://raspberrypi.stackexchange.com/questions/49660/ad-hoc-setup-in-rpi-3) to setup ad hoc network on each pi. Make sure to assign different IP address to each Pi and note these addresses.

- Reboot the raspberry Pi's

- Enable and start SSH on your Pi's:

`sudo systemctl enable ssh`

`sudo systemctl start ssh`

## Running Code on Ad Hoc network

- From one of your Pi's, you can SSH into other Pi's:

`ssh pi@[IP of Pi]`

- Enter username/password

- In the `routing.py` file, change `route_configs` and `addr_configs`.

- To apply changes to other Pi's, on receiving Pi's ssh terminal, run:

`sudo python3 file_recv.py [IP] [port=1000]`

- From main Pi, run:

`sudo python3 file_send.py [receiving IP] [port=1000] routing.py`

- Now, you're ready to run code on your Ad Hoc network. To put Pi's in listening and routing mode, on their terminal:

`sudo python3 tcp_socket_test.py [Experiment Name] [Pi ID] [sack] [snoop]`

- On sending side:

`sudo python3 tcp_socket_test.py [Experiment Name] [Pi ID] [sack] [snoop] [receiving IP] [port=1000]`


## Experiments

Change the confif.py file according to your pi setup

### Base experiments

Simple TCP:

- receivers: `sudo python3 tcp_socket_test.py simple_tcp [Pi ID: 1,2,3] 0 0`

- sender: `sudo python3 tcp_socket_test.py simple_tcp [Pi ID: 0] 0 0 [Pi 3's IP] [Pi 3's port]`

Sack:

- receivers: `sudo python3 tcp_socket_test.py sack [Pi ID: 1,2,3] 1 0`

- sender: `sudo python3 tcp_socket_test.py sack [Pi ID: 0] 1 0 [Pi 3's IP] [Pi 3's port]`

Sack + Snoop:

- receivers: `sudo python3 tcp_socket_test.py sack_snoop [Pi ID: 1,2,3] 1 1`

- sender: `sudo python3 tcp_socket_test.py sack_snoop [Pi ID: 0] 1 1 [Pi 3's IP] [Pi 3's port]`

You can make plots by:

`python3 plot.py simple_tcp sack sack_snoop`

### Lossy link experiments

Uncomment line 92-93 in `routing.py`

Repeat above experiments with slightly different experiment names e.g. lossy_simple_tcp

### Varying value of `pkt_qos`

Repeat Sack+Snoop experiment with following values of pkt_qos: 0.9, 0.95, 0.97, 0.99, 1

You can change value of pkt_qos in line 38 of `packet.py`

### Non-adaptive Snooping

Uncomment line 177-178 in `tcp.py`

Run one experiment with snoop_at set to 1 and another with snoop_at set to 2 (Use Sack+Snoop setting)