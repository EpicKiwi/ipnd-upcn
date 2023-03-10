import socket
import struct
import time
from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService, CLAService
import upcn
from pyupcn.agents import make_contact
from datetime import datetime, timedelta
import threading

PERIOD = 10
DESTINATION_V4 = "224.0.0.26"
DESTINATION_V6 = "FF02::1"
DESTINATION_PORT = 3003
AAP_PREFIX = "ipcn"


def start_beacon_server():
    with upcn.upcn_sock(AAP_PREFIX+"/server") as aap:

        message = IPNDMessage()
        message.eid = aap.eid
        message.period = PERIOD
        message.sequence_number = 0
        period_timeout = datetime.now()

        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as sock:

            ttl = struct.pack('b', 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

            if socket.has_ipv6:
                sock.setsockopt(socket.IPPROTO_IPV6,
                                socket.IPV6_MULTICAST_LOOP, 0)
                print("Emitting on IPv6 {}:{}".format(
                    DESTINATION_V6, DESTINATION_PORT))
            else:
                print("Emitting on IPv4 {}:{}".format(
                    DESTINATION_V4, DESTINATION_PORT))

            while True:

                now = datetime.now()

                if now > period_timeout:

                    encoded_message = message.encode()
                    if socket.has_ipv6:
                        sock.sendto(encoded_message,
                                    (DESTINATION_V6, DESTINATION_PORT))
                    else:
                        sock.sendto(encoded_message,
                                    (DESTINATION_V4, DESTINATION_PORT))

                    message.sequence_number += 1
                    period_timeout = now + timedelta(seconds=PERIOD)

                else:
                    time.sleep((period_timeout - now).seconds)


def start_beacon_client():
    with upcn.upcn_sock(AAP_PREFIX+"/client") as aap:
        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as sock:

            sock.bind(('', DESTINATION_PORT))

            if socket.has_ipv6:
                group = socket.inet_pton(socket.AF_INET6, DESTINATION_V6)
                sock.setsockopt(socket.IPPROTO_IP,
                                socket.IPV6_JOIN_GROUP, group)
                sock.setsockopt(socket.IPPROTO_IPV6,
                                socket.IPV6_MULTICAST_LOOP, 0)
                print("Listening on IPv6 {}:{}".format(
                    DESTINATION_V6, DESTINATION_PORT))
            else:
                group = socket.inet_pton(socket.AF_INET, DESTINATION_V4)
                sock.setsockopt(socket.IPPROTO_IP,
                                socket.IP_ADD_MEMBERSHIP, group)
                print("Listening on IPv4 {}:{}".format(
                    DESTINATION_V4, DESTINATION_PORT))

            while True:

                mess = sock.recv(4096)

                try:
                    ipnd_mess = IPNDMessage.decode(mess)
                except Exception as e:
                    print("Invalid ipnd packet received : {}".format(e))

                if ipnd_mess.eid is None:
                    print("received message from unknown eid, skipping...")
                    continue

                cla_services = filter(lambda it: isinstance(
                    it, CLAService), ipnd_mess.services)
                cla_address = ";".join(
                    map(lambda it: it.get_cla_address(), cla_services))

                print("Received message from {}".format(
                    ipnd_mess.eid))

                aap.set_contact(ipnd_mess.eid, cla_address, contacts=[
                    make_contact(0, ipnd_mess.period+ipnd_mess.period/2, 1000)
                ])


server_thread = threading.Thread(target=start_beacon_server)
client_thread = threading.Thread(target=start_beacon_client)

server_thread.start()
client_thread.start()
