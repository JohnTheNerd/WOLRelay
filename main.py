#!/usr/bin/env python3

import datetime
import multiprocessing
import os
import json
import re
import traceback
import functools
import logging
import time

from scapy.all import sniff
from wakeonlan import send_magic_packet
from flask import Flask, request, abort

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

# TODO make sure logger works
# TODO test API endpoints
# TODO make a front-end
# TODO ensure config options are actually used
# TODO update README with all config options and how one can use them. also document that the interfaces option in arp, if left blank, will pick the default interface. arp only works on /24 as of now
# TODO actually scan the network
# TODO use all interfaces given in the arp config, if present

@app.before_request
def beforeRequest():
  # optionally mitigate against DNS rebinding
  if 'hosts' in config.keys():
    splitHost = request.host
    if ':' in splitHost:
      splitHost = request.host.split(':')[0]
    if splitHost != "localhost" and splitHost != "127.0.0.1": # whitelist localhost because of Docker health checks
      if splitHost not in config['hosts']:
        abort(403)

def processARP(packets):
  for packet in packets:
    if packet.type == 2054:   # only process ARP packets
        if packet.op == 2:    # only process ARP *reply* packets
          if packet.hwsrc.upper() in ARPTable.keys():   # only process packets from MAC addresses we care about
            mac = packet.hwsrc
            ip = packet.psrc
            logging.debug('IP ' + ip + ' is assigned to ' + mac + ' as of ' + datetime.datetime.now().isoformat())
            ARPTable[mac] = (ip, datetime.datetime.now())

def sniffARPPackets(interface = None):
  try:
    sniff(prn=processARP, filter="(arp[6:2] = 2)")  # run scapy with BPF for ARP packets with opcode 2
  except Exception:
    logger.warning("Running scapy in filtered mode failed, filtering without the help of Berkeley Packet Filtering. This is going to be VERY slow and unreliable. You should try installing tcpdump if you're on Linux, and Npcap if you're on Windows.")
    sniff(prn=processARP)     # filtering failed, fall back to inspecting every packet

def sendARPRequest(interface, destination):
    logger.debug('sending ARP request to ' + destination)
    scapy.layers.l2.arping(destination, iface=interface, timeout=0, cache=True, verbose=False)

def scanNetwork():
  while True:
    try:
      pool = multiprocessing.Pool(processes=10)
      processes = []

      for network, netmask, _, interface, address, _ in scapy.config.conf.route.routes:
        # skip loopback network and default gw
        if network == 0 or interface == 'lo' or address == '127.0.0.1' or address == '0.0.0.0':
          continue

        if netmask <= 0 or netmask == 0xFFFFFFFF:
          continue

        # skip docker interface
        if interface.startswith('docker') or interface.startswith('br-'):
          continue

        subnet = '.'.join(address.split('.')[:-1])
        IPRange = [subnet + '.' + str(i) for i in range(1, 254)]
        boundARPRequest = functools.partial(sendARPRequest, interface)
        processes.append(pool.map_async(boundARPRequest, IPRange))

      for process in processes:
        process.get()
      pool.close()
      pool.join()
    except:
      logger.warning('scanning the network failed! exception details: ' + traceback.format_exc())
    finally:
      time.sleep(config['arp']['scanInterval'])

"""
For a given MAC address, returns the IP address and the timestamp for when we recorded it.

Returns HTTP501 if ARP is disabled from the configuration file.
Returns HTTP400 if the MAC address is invalid or does not exist in our ARP table.
Returns HTTP204 if the MAC address does not have a corresponding IP address yet.

@mac MAC address to scan ARP table for.
"""
@app.route('/getIP')
def getIP():
  mac = request.args.get('mac')

  if 'arp' not in config.keys():
    abort(501)
    return {"successful": False, "error": "ARP is disabled in the configuration file"}
  if mac not in ARPTable.keys():
    abort(400)
    return {"successful": False, "error": "MAC is not defined in the configuration file"}
  if not ARPTable[mac]:
    abort(204)
    return {"successful": False, "error": "The server does not have any information about this MAC address yet"}

  return json.dumps({
    "successful": True,
    "IP": ARPTable[mac][0],
    "lastActive": ARPTable[mac][1].isoformat()
  })


"""
Sends a Wake-on-LAN "magic packet" to the specified MAC address.

Returns HTTP400 if the MAC address appears to be invalid.

@mac MAC address to send packet to.
"""
@app.route('/wakeComputer', methods=['POST'])
def wakeComputer():
  mac = request.json['mac']

  mac = mac.upper()
  if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
    abort(400)
    return json.dumps({"successful": False, "error": "MAC address verification failed"})

  try:
    send_magic_packet(mac, ip_address=config['broadcastAddress'], port=config['broadcastPort'])
    return json.dumps({"successful": True})
  except Exception:
    abort(500)
    return json.dumps({"successful": False, "error": traceback.format_exc()})


if __name__ == '__main__':
  if 'arp' in config.keys():
    sniffingProcess = multiprocessing.Process(target=sniffARPPackets)
    sniffingProcess.start()

    for mac in config['arp']['macAddresses']:
      ARPTable[mac.upper()] = None

    if 'scanInterval' in config['arp'].keys():
      scanningProcess = multiprocessing.Process(target=scanNetwork)
      scanningProcess.start()

  app.run(config['localIP'], port=config['APIPort'], threaded=True)