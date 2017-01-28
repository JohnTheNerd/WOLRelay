#!/usr/bin/python
import socket
import os
import sys
import random
import hashlib
import thread
import struct
 
# So, what we do here essentially is listen on the given port, generate a random number when a user connects, call md5(number+password+number) and expect user to send the same to us.
# If we get the same answer, we wake up the computer described in the global variables.

# Global variables go here:

HOST = ''   # Symbolic name, meaning all available interfaces
PORT = 5000 # Arbitrary non-privileged port
PASSWORD = "PASSWORDGOESHERE" # Password to be hashed
WAKEMAC = "00:00:00:00:00:00" # MAC address to wake up
BROADCASTADDR = "255.255.255.255" # Broadcast address

# Defined functions go here:
def md5(toHash):
    hash_md5 = hashlib.md5()
    hash_md5.update(toHash)
    return hash_md5.hexdigest()

def wakeComputer(macaddress):
# Thanks to https://github.com/remcohaszing/pywakeonlan for the magic packet generating code!
  
# Check macaddress format and try to compensate.
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 12 + 5:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')
 
    # Pad the synchronization stream.
    data = b'FFFFFFFFFFFF' + (macaddress * 20).encode()
    send_data = b'' 

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data += struct.pack(b'B', int(data[i: i + 2], 16))

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, (BROADCASTADDR, 9))

def connHandler(conn,addr):

    # So we got a connection coming in. We need to generate the random suffix, hash it, and wait for a response
    print ('DEBUG - Connected from: ' + addr[0])
    randNum = random.randint(0,9999999999)
    conn.send(str(randNum)) # Send challenge number to user after casting it to a string

    randStr = str(randNum) + PASSWORD + str(randNum)
    print("DEBUG - Randomly generated string: " + randStr)
    randStr = md5(randStr)
    print("DEBUG - Challenge result(expected hash): " + randStr)

    recvStr = conn.recv(1024)
    recvStr = recvStr[0:32] # Crop first 32 characters, because of MD5 length
    
    if (recvStr == randStr):
	print (addr[0] + " passed the challenge! Sending magic package...")
        wakeComputer(WAKEMAC)
	conn.send("no") # Let's send a simple "no" to trick other people trying to connect.
        conn.close()
    else:
	print (addr[0] + " failed the challenge! \n Received result: " + recvStr + "\n Expected result: " + randStr)
	conn.send("yes") # Let's send a simple "yes" to trick other people trying to connect.
        conn.close()
 
# Main program starts here. 
# Bind socket to port, and start listening.

ADDR = (HOST, PORT)
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversock.bind(ADDR)
serversock.listen(5)

# Main loop starts here. This is an infinite loop, it will continuously be listening for connections.
while 1:
        print 'Server started! Listening on port: ', PORT
        clientsock, addr = serversock.accept()
        thread.start_new_thread(connHandler, (clientsock, addr)) # Pass connection on to new thread, and run connHandler
