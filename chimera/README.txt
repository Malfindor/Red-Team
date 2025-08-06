Chimera is a C2 implementation utilizing DNS queries/responses to transfer messages and data.

Legend:


Queries and their Meaning:

"supportcenter.net" - Client checkin (response A)
"freegames.net" - Client heartbeat (response A)
"securelogin.com" - Send reverse shell to address/port (response B)
"cloudlogin.com" - Send file contents to address/port (response B)
"fileshare.org" - Ready for filename (response C)


Responses and their Meaning:

x.x.x.100 - Standby / Sleep
x.x.x.232 - Prepare for reverse shell
x.x.x.85 - Collect file contents

Response Formats:

Response A - Single IP from standard responses
Response B - Responds with 2 addresses:
	IP address to send reverse shell to (ie. 10.10.10.10)
	IP address of format y1.y2.x.3, where the port to transmit on is defined as y1+y2 *Note: port capped at 510*
Response C - Responds with any number of addresses:
	Each quartet of the address is translated into it's ascii character until the value "3" is reached
	Designates a filename