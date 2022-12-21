import socket
import struct
import time
from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService
import upcn

PERIOD = 1
DESTINATION_V4 = "224.0.0.26"
DESTINATION_V6 = "FF02::1"
DESTINATION_PORT = 3003

with upcn.upcn_sock() as aap:

    message = IPNDMessage()
    message.eid = aap.eid
    message.period = PERIOD
    message.sequence_number = 0

    print("Connected to upcn {}".format(aap.eid))

    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as sock:

            sock.settimeout(PERIOD)

            ttl = struct.pack('b', 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

            sock.bind(('', DESTINATION_PORT))

            if socket.has_ipv6:
                group = socket.inet_pton(socket.AF_INET6, DESTINATION_V6)
                sock.setsockopt(socket.IPPROTO_IP, socket.IPV6_JOIN_GROUP, group)
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)
                print("Starting on IPv6 {}:{}".format(DESTINATION_V6, DESTINATION_PORT))
            else:
                group = socket.inet_pton(socket.AF_INET, DESTINATION_V4)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)
                print("Starting on IPv4 {}:{}".format(DESTINATION_V4, DESTINATION_PORT))

            while True:

                encoded_message = message.encode()
                if socket.has_ipv6:
                    sock.sendto(encoded_message, (DESTINATION_V6, DESTINATION_PORT))
                else:
                    sock.sendto(encoded_message, (DESTINATION_V4, DESTINATION_PORT))

                message.sequence_number += 1

                while True:
                    try:
                        mess = sock.recv(1024)
                    except TimeoutError:
                        break

                    try:
                        ipnd_mess = IPNDMessage.decode(mess)
                        print(ipnd_mess)
                    except Exception as e:
                        print("Invalid ipnd packet received : {}".format(e))



        
