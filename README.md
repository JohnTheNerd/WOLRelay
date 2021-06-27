# WOLRelay

A Wake-on-LAN relaying software written in Python that is able to listen for ARP reply packets to track IP addresses without any agent process running on the target machine. It is currently only tested on Linux.

I don't like leaving my desktop on 24/7 because it's bad for the environment, could shorten the lifespan of my computer, and would have a big impact on my power bill. But I also _love_ streaming games to my hacked Nintendo Switch, and generally having access to it from virtually anywhere.

Special thanks to [HTML5 UP!](https://html5up.net) for the awesome template I have taken and modified to use as the front-end!

![Screenshot](screenshot.jpg?raw=true "Screenshot")

## ARP Scanning Support

WOLRelay can also tell you when the machine was last online, along with its last reported IP address. This does not require any agent process on the target machine, but is instead done via scanning the network for all ARP reply packets from MAC addresses that interest us.

In order to use this functionality, you should have the tcpdump package installed. Although this is not required, tcpdump is used by Scapy in order to utilize BPF which provides kernel-backed fast packet processing. Otherwise, every single packet sent through the network will be moved to userspace and processed by pure Python code, which causes lost packets and sluggish performance.

Please keep in mind that ARP scans can cause disruption in the network if done too frequently, and may show up as an attack in certain firewall solutions.

## Usage

- Clone this Git repository.

- Edit the configuration file (all fields required unless stated otherwise):

    - **APIPort**: The port WOLRelay's Flask API will run on.

    - **broadcastAddress**: The broadcast address to send magic packets to. In most cases, you can leave this as the default value.

    - **broadcastPort**: The port to send the magic packets through. In most cases, you can leave this as the default value.

    - **localIP**: The host IP address to be passed to Flask. Leave it as `0.0.0.0` to accept requests from all network interfaces, or change it to your IP address to restrict it to one.

    - **hosts**: This field is optional. If it exists, it is assumed to be an array of strings. If the "Host" header does not match one of the hosts provided here (don't include http:// or the port), the connection will be rejected. Localhost and `127.0.0.1` are always permitted regardless of this setting. Useful against DNS rebinding attacks.

    - **logLevel**: The logging level, to be passed into the logging standard library. It is set as an integer, [as defined here](https://docs.python.org/3/library/logging.html#levels)

    - **arp**: This entire field is optional, removing it will disable all ARP support. It is a dictionary with keys of:

        - **scanInterval**: How long should we wait between ARP scans (in seconds)? Remove entirely to disable ARP scanning and rely on ARP announcement packets, but keep in mind that this will have a cost in accuracy as not all devices will send ARP announcements unless specifically requested. ARP scanning currently only works on /24 networks (which is basically every home network).

        - **scanThreads**: How many threads should WOLRelay use to scan the network? This field is optional, with a default of 3.

        - **scanInterfaces**: This field is optional. A list of strings, indicating the names of network interfaces to sniff ARP packets from.

        - **devices**: Required if ARP is enabled. A list of objects with two keys, "name" defining the display name and "mac" defining the MAC address.

- If you have Docker Compose installed, simply run `docker-compose up` and everything should start running!

- Otherwise, install all dependencies by running `pip3 install -r requirements.txt`

- If you are running this in a production environment, it is recommended that you serve the files in the `static` folder inside an actual web server and just proxy the API endpoints mentioned below to this application. Although WOLRelay will happily serve the front-end, it will not be as performant.

- This application requires the "cap_net_raw" Linux capability to scan the network for ARP packets and to send the magic packet. To do this, you can do either of:

    - Run the application _as a superuser_. For obvious reasons this is not recommended.

    - Grant the "cap_net_raw" capability to the Python interpreter by running (change 3.6 to your exact Python version) `sudo setcap cap_net_raw=eip $(which python3.6)` _and_ grant the same capability to tcpdump by running `sudo setcap cap_net_raw=eip $(which tcpdump)`

## API Endpoints

- `/status` (GET)

    - For a given MAC address, returns the IP address and the timestamp for when we recorded it.

    - Returns HTTP 501 if ARP is disabled from the configuration file.

- `/status?mac=00:00:00:00:00:00` (GET)

    - For a given MAC address, returns the IP address and the timestamp for when we recorded it.

    - Returns HTTP 501 if ARP is disabled from the configuration file.

    - Returns HTTP 400 if the MAC address is invalid or does not exist in our ARP table.

    - Returns HTTP 204 if the MAC address does not have a corresponding IP address yet.

- `/wake` (POST)

    - For a given MAC address as `mac` in a JSON body, send a magic packet.
