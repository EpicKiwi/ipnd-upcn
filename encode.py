from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService, PrimitiveService
import ipaddress
import sys

myMessage  = IPNDMessage()

myMessage.eid = "dtn://epickiwi.dtn"
myMessage.period = 1
myMessage.sequence_number = 0
myMessage.services += (TCPCLService(ipaddress.ip_address("192.168.0.1"), 4222),)
myMessage.services += (TCPCLService(ipaddress.ip_address("fe80::b453:d21:cf3c:aec2"), 4222),)
myMessage.services += (
    PrimitiveService(True, "bool"),
    PrimitiveService(10, "uint64"),
    PrimitiveService(-10, "sint64"),
    PrimitiveService(1552, "fixed16"),
    PrimitiveService(1337, "fixed32"),
    PrimitiveService(481451545454856, "fixed64"),
    PrimitiveService(1.5, "float"),
    PrimitiveService(49.3, "double"),
    PrimitiveService("Hello, world", "string"),
    PrimitiveService(b"rrr", "bytes"),
)

sys.stdout.buffer.write(bytes(myMessage))