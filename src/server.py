#!/bin/env python3

import socket
import struct
import time
from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService, CLAService, Service
import upcn
from pyupcn.agents import make_contact
from datetime import datetime, timedelta
import threading
import os
import netifaces
from dataclasses import dataclass

PERIOD = 3
DESTINATION_V4 = "224.0.0.26"
DESTINATION_V6 = "FF02::1"
DESTINATION_PORT = 3003
AAP_PREFIX = "ipcn"

socket_path = "/var/run/user/{}/upcn.socket".format(os.getuid())

def start_beacon_server():

    services:list[Service] = []

    for iface_name in netifaces.interfaces():    
        if iface_name == "lo":
            continue
        
        addresses = netifaces.ifaddresses(iface_name)

        if socket.AF_INET in addresses:
            services += map(lambda it: TCPCLService(it["addr"], 4556), addresses[socket.AF_INET])

        if socket.AF_INET6 in addresses:
            services += map(lambda it: TCPCLService(it["addr"], 4556), addresses[socket.AF_INET6])

    print("Advertizing services :")
    for it in services:
        print("\t", it)

    with upcn.upcn_sock(AAP_PREFIX+"/server", socket_path=socket_path) as aap:

        print("Advertizing {} (period: {}s)".format(aap.eid, PERIOD))

        ttl = struct.pack('b', 1)

        with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as v6sock:
            v6sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            v6sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 0)
            print("Emitting on {}:{}".format(DESTINATION_V4, DESTINATION_PORT))

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as v4sock:
                v4sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
                print("Emitting on {}:{}".format(DESTINATION_V6, DESTINATION_PORT))

                message = IPNDMessage()
                message.eid = aap.eid
                message.period = PERIOD
                message.sequence_number = 0
                message.services = services
                period_timeout = datetime.now()

                while True:

                    now = datetime.now()

                    if now > period_timeout:
                        print("\rBeacon {} ".format(message.sequence_number), end="")

                        encoded_message = message.encode()

                        v6sock.sendto(encoded_message,
                                    (DESTINATION_V6, DESTINATION_PORT))
                        
                        v4sock.sendto(encoded_message,
                                    (DESTINATION_V4, DESTINATION_PORT))

                        message.sequence_number += 1

                        period_timeout = now + timedelta(seconds=PERIOD)

                    else:
                        time.sleep((period_timeout - now).seconds)


def start_beacon_client():
    with upcn.upcn_sock(AAP_PREFIX+"/client", socket_path=socket_path) as aap:
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
                
                if ipnd_mess.eid == aap.eid:
                    # Advertized myself, skipping
                    continue

                print("Received message from {}".format(
                    ipnd_mess.eid))

                cla_service = list(filter(lambda it: isinstance(
                    it, CLAService), ipnd_mess.services))

                if len(cla_service) == 0:
                    print("No CLA Service available")
                    continue

                # TODO Do a better selectio of the best CLA
                cla_address = cla_service[0].get_cla_address()

                aap.set_contact(ipnd_mess.eid, cla_address, contacts=[
                    make_contact(0, ipnd_mess.period+ipnd_mess.period/2, 1000)
                ])

server_thread = threading.Thread(target=start_beacon_server)
client_thread = threading.Thread(target=start_beacon_client)

server_thread.start()
client_thread.start()
