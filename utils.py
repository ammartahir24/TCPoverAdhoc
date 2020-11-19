# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 13:37:23 2020

"""

import subprocess

def getRSSI(interface = 'wlan0'):
	
	cmd = subprocess.Popen('iw {} link'.format(interface), 
						shell = True,
						stdout = subprocess.PIPE)
	
	for line in cmd.stdout:
		if 'signal' in line:
			query = line.split(' ')
			rssi = int(query[1])
			
	return rssi