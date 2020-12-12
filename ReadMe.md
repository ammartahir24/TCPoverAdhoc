## Setup Details

On each of the raspberry pi, do this:

- Connect your pi to the internet

- Download any good text editor of your choice

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

`sudo python3 tcp_socket_test.py [Pi ID]`

- On sending side:

`sudo python3 tcp_socket_test.py [Pi ID] [receiving IP] [port=1000]`

