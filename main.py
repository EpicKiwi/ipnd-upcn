from time import sleep
from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService
import ipaddress
import sys

myMessage  = IPNDMessage()

myMessage.eid = "dtn://epickiwi.dtn"
myMessage.period = 1
myMessage.sequence_number = 0
myMessage.services += (TCPCLService(ipaddress.ip_address("192.168.0.1"), 4222),)
myMessage.services += (TCPCLService(ipaddress.ip_address("fe80::b453:d21:cf3c:aec2"), 4222),)

sys.stdout.buffer.write(bytes(myMessage))