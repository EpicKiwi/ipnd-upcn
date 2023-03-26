from time import sleep
from ipnd.message import IPNDMessage
from ipnd.service import TCPCLService
import ipaddress
import sys

print(IPNDMessage.decode(sys.stdin.buffer.read()))