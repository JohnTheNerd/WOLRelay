#!/usr/bin/env python3

import datetime
import ipaddress
import json
import logging
import multiprocessing
import multiprocessing.dummy
import os
import time
import traceback

import scapy
import scapy.config
import scapy.layers.l2
import scapy.sendrecv
from wakeonlan import send_magic_packet
from flask import Flask, request, abort, send_from_directory
from werkzeug.exceptions import NotFound

app = Flask(__name__)

scriptPath = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(scriptPath, 'config.json')
config = open(configPath).read()
config = json.loads(config)

logging.basicConfig()
logger = logging.getLogger("WOLRelay")
logger.setLevel(config['logLevel'])

multiprocessingManager = multiprocessing.Manager()
ARPTable = multiprocessingManager.dict()
cidr = None

@app.before_request
def beforeRequest():
  # optionally mitigate against DNS rebinding
  if 'hosts' in config.keys():
    splitHost = request.host
    if ':' in splitHost:
      splitHost = request.host.split(':')[0]
    if splitHost != "localhost" and splitHost != "127.0.0.1": # whitelist localhost
      if splitHost not in config['hosts']:
        abort(403)

def processPackets(packets):
  for packet in packets:
    if packet.type == 2054:   # only process ARP packets
        if packet.op == 2:    # only process ARP *reply* packets
          if packet.hwsrc.upper() in ARPTable.keys():   # only process packets from MAC addresses we care about
            mac = packet.hwsrc
            ip = packet.psrc
            logging.debug('IP ' + ip + ' is assigned to ' + mac + ' as of ' + datetime.datetime.now().isoformat() + "Z")
            name = ARPTable[mac.upper()]['name']
            ARPTable[mac.upper()] = {
              "name": name,
              "mac": mac.upper(),
              "ip": ip,
              "lastSeen": datetime.datetime.now().isoformat() + "Z"
            }

def sniffPackets(interface):
  if interface:
    try:
      scapy.sendrecv.sniff(prn=processPackets, iface=interface, filter="(arp[6:2] = 2)")  # run scapy with BPF for ARP packets with opcode 2
    except Exception:
      logger.warning("Running scapy in filtered mode failed, filtering without the help of Berkeley Packet Filtering. This is going to be VERY slow and unreliable. You should try installing tcpdump if you're on Linux, and Npcap if you're on Windows.")
      traceback.print_exc()
      scapy.sendrecv.sniff(prn=processPackets)     # filtering failed, fall back to inspecting every packet
  else:
    try:
      scapy.sendrecv.sniff(prn=processPackets, filter="(arp[6:2] = 2)")  # run scapy with BPF for ARP packets with opcode 2
    except Exception:
      logger.warning("Running scapy in filtered mode failed, filtering without the help of Berkeley Packet Filtering. This is going to be VERY slow and unreliable. You should try installing tcpdump if you're on Linux, and Npcap if you're on Windows.")
      traceback.print_exc()
      scapy.sendrecv.sniff(prn=processPackets)     # filtering failed, fall back to inspecting every packet

def updateLoop(interface, name, mac, cidr, interval):
  while True:
    try:
      updateDevice(interface, name, mac, cidr)
      time.sleep(interval)
    except Exception:
      logger.error(f"An exception has occurred while trying to update device {name}! Exception details: \n" + traceback.format_exc())
      time.sleep(interval)

def updateDevice(interface, name, mac, cidr):
  # craft the ARP ping packets for the entire CIDR range, to the given MAC address
  arp = scapy.layers.l2.ARP()
  arp.pdst = cidr
  ether = scapy.layers.l2.Ether()
  ether.dst = mac
  packet = ether / arp
  # send ARP ping packets and get the first response
  # if the target does not respond in 2 seconds, it's probably dead
  answer = scapy.sendrecv.srp1(packet, iface = interface, timeout = 2)
  if answer:
    mac = answer.hwsrc
    ip = answer.psrc
    logging.debug('IP ' + ip + ' is assigned to ' + mac + ' as of ' + datetime.datetime.now().isoformat() + "Z")
    name = ARPTable[mac.upper()]['name']
    ARPTable[mac.upper()] = {
      "name": name,
      "mac": mac.upper(),
      "ip": ip,
      "lastSeen": datetime.datetime.now().isoformat() + "Z"
    }

"""
For a given MAC address, returns the IP address and the timestamp for when we recorded it.

Returns HTTP 501 if ARP is disabled from the configuration file.
Returns HTTP 400 if the MAC address does not exist in our ARP table.
Returns HTTP 204 if the MAC address does not have a corresponding IP address yet.

@mac MAC address to scan ARP table for. If not defined, data for all MAC addresses will be returned.
"""
@app.route('/status')
def status():
  mac = None
  if 'mac' in request.args:
    mac = request.args.get('mac')
    mac = mac.upper()
  if 'arp' not in config.keys():
    return (json.dumps({"error": "ARP is disabled in the configuration file!"}), 501)
  if mac:
    if mac not in ARPTable.keys():
      return (json.dumps({"error": "The given MAC address is not defined in the configuration file!"}), 400)
    if not ARPTable[mac]:
      return (json.dumps({"error": "We don't have any information about this MAC address yet!"}), 204)
    return json.dumps(ARPTable[mac])
  else:
    result = []
    for mac in ARPTable.keys():
      result.append(ARPTable[mac])
    return json.dumps(result)

"""
Sends a Wake-on-LAN "magic packet" to the specified MAC address.

@mac MAC address to send packet to.
"""
@app.route('/wake', methods=['POST'])
def wakeDevice():
  mac = request.json['mac']
  mac = mac.upper()
  try:
    send_magic_packet(mac, ip_address=config['broadcastAddress'], port=config['broadcastPort'])
    return json.dumps({"error": None})
  except Exception:
    return (json.dumps({"error": traceback.format_exc()}), 500)

"""
If `mac` is defined in the JSON body, updates the ARP table for that entry. If not, updates the entire ARP table. Afterwards, returns the entire ARP table.

Returns HTTP 501 if ARP scanning is disabled in the configuration file.
Returns HTTP 400 if the MAC address provided does not exist in our ARP table.

@mac MAC address to update. If omitted, updates the entire table.
"""
@app.route('/update', methods=['POST'])
def update():
  if 'arp' not in config.keys():
    return (json.dumps({"error": "ARP is disabled in the configuration file!"}), 501)
  mac = None
  if request.is_json:
    if 'mac' in request.json:
      mac = request.json['mac']
      mac = mac.upper()
  if mac:
    if not config['arp']['scan']:
      return (json.dumps({"error": "ARP scanning is disabled in the configuration file!"}), 501)
    if mac not in ARPTable.keys():
      return (json.dumps({"error": "The given MAC address is not defined in the configuration file!"}), 400)
    name = ARPTable[mac]['name']
    interface = config['arp']['interface']
    updateDevice(interface, name, mac, cidr)
    return json.dumps(ARPTable[mac])
  else:
    result = []
    for mac in ARPTable.keys():
      name = ARPTable[mac]['name']
      interface = config['arp']['interface']
      updateDevice(interface, name, mac, cidr)
      result.append(ARPTable[mac])
    return json.dumps(result)

# hackity hack
# serve static files from the static directory
# this is so that the user doesn't need to configure a webserver to run and/or debug
# but it's encouraged to do so anyway for performance reasons
@app.route('/<path:path>')
def staticHost(path):
  try:
    return send_from_directory(os.path.join(scriptPath, 'static'), path)
  except NotFound as e:
    if path.endswith("/"):
      return send_from_directory(os.path.join(scriptPath, 'static'), path + "index.html")
    raise e

@app.route('/')
def staticIndex():
  return send_from_directory(os.path.join(scriptPath, 'static'), "index.html")

if __name__ == '__main__':
  if 'arp' in config:
    interface = config['arp']['interface']
    sniffingProcess = multiprocessing.Process(target=sniffPackets, args=[interface])
    sniffingProcess.start()

    for device in config['arp']['devices']:
      name = device['name']
      mac = device['mac']
      ARPTable[mac.upper()] = {
        "name": name,
        "mac": mac.upper(),
        "ip": None,
        "lastSeen": None
      }

    if config['arp']['scan']:
      scanInterface = config['arp']['interface']
      interval = config['arp']['interval']

      # find the network CIDR by searching through the routing table for the interface we want to scan on
      for network, netmask, _, interface, address, _ in scapy.config.conf.route.routes:
        if scanInterface != interface:
          continue

        # convert netmask from an integer format to a string
        # otherwise ipaddress.IPv4Network will reject it
        netmaskString = str(ipaddress.IPv4Address(netmask))
        network = ipaddress.IPv4Network(f'{address}/{netmaskString}', strict=False)
        # convert the IPv4Network object to a string to get the network in CIDR notation
        cidr = str(network)

      if not cidr:
        raise Exception(f'Failed to calculate CIDR from the provided network interface name {scanInterface}')

      for device in config['arp']['devices']:
        name = device['name']
        mac = device['mac']
        scanningProcess = multiprocessing.Process(target=updateLoop, args=[scanInterface, name, mac, cidr, interval])
        scanningProcess.start()

  app.run(config['localIP'], port=config['APIPort'], threaded=True)