import socket
import struct

# List of IPs to return for every A query
RESPONSE_IPS = [
    "192.168.56.200",
    "192.168.56.201",
    "192.168.56.202"
]

def parse_qname(data, offset):
    qname = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        qname.append(data[offset + 1: offset + 1 + length].decode())
        offset += 1 + length
    return ".".join(qname), offset

def build_response(query, response_ips):
    # Extract transaction ID
    txid = query[0:2]

    # Flags: standard query response, recursion available, no error
    flags = b'\x81\x80'

    # QDCOUNT and ANCOUNT
    qdcount = query[4:6]
    ancount = struct.pack('!H', len(response_ips))
    nscount = arcount = b'\x00\x00'

    header = txid + flags + qdcount + ancount + nscount + arcount

    # Extract question section
    qname, q_end = parse_qname(query, 12)
    question = query[12:q_end + 4]  # includes QTYPE and QCLASS

    # Build all answer sections
    answers = b''
    for ip in response_ips:
        name_pointer = b'\xc0\x0c'  # pointer to domain name
        type_a = struct.pack('!H', 1)        # Type A
        class_in = struct.pack('!H', 1)      # Class IN
        ttl = struct.pack('!I', 60)          # TTL = 60 seconds
        rdlength = struct.pack('!H', 4)      # IPv4 is 4 bytes
        rdata = socket.inet_aton(ip)         # Convert IP string to bytes

        answer = name_pointer + type_a + class_in + ttl + rdlength + rdata
        answers += answer

    return header + question + answers, qname

def run_dns_server(bind_ip="127.0.0.1", port=53):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    print(f"[+] DNS server listening on {bind_ip}:{port}")

    while True:
        data, addr = sock.recvfrom(512)
        response, domain = build_response(data, RESPONSE_IPS)
        print(f"[>] Received query from {addr[0]}:{addr[1]} for domain: {domain}")
        sock.sendto(response, addr)

if __name__ == "__main__":
    run_dns_server()
