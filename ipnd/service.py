from abc import ABC, abstractmethod
from sdnv import SDNVUtil
import struct
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Union

BOOL_TYPE = 'bool'
UINT_TYPE = 'uint64'
SINT_TYPE = 'sint64'
FIXED16_TYPE = 'fixed16'
FIXED32_TYPE = 'fixed32'
FIXED64_TYPE = 'fixed64'
FLOAT_TYPE = 'float'
DOUBLE_TYPE = 'double'
STRING_TYPE = 'string'
BYTES_TYPE = 'bytes'

class Service(ABC):

    @abstractmethod
    def encode(self) -> bytes:
        pass
    
    def __bytes__(self) -> bytes:
        return self.encode()

class PrimitiveService:

    value = None
    type:str = None

    def __init__(self, value, type=None):
        self.value = value
        self.type = type

    def encode(self) -> bytes:
        ba = bytearray()

        tag = 0
        get_val = None

        if self.type == BOOL_TYPE:
            tag = 0
            get_val = lambda v: bool(v)

        elif self.type == UINT_TYPE:
            tag = 1
            get_val = lambda v: SDNVUtil.encode(v)

        elif self.type == SINT_TYPE:
            tag = 2
            get_val = lambda v: SDNVUtil.encode(v)

        elif self.type == FIXED16_TYPE:
            tag = 3
            get_val = lambda v: int(v).to_bytes(2, 'big')

        elif self.type == FIXED32_TYPE:
            tag = 4
            get_val = lambda v: int(v).to_bytes(4, 'big')

        elif self.type == FIXED64_TYPE:
            tag = 5
            get_val = lambda v: int(v).to_bytes(8, 'big')
            
        elif self.type == FLOAT_TYPE:
            tag = 6
            get_val = lambda v: struct.pack("!f", v)

        elif self.type == DOUBLE_TYPE:
            tag = 7
            get_val = lambda v: struct.pack("!d", v)

        elif self.type == STRING_TYPE:
            tag = 8
            get_val = lambda v: encode_primitive_array(str(self.value).encode("ascii"))
            
        elif self.type == BYTES_TYPE:
            tag = 9
            get_val = lambda v: encode_primitive_array(bytes(self.value))

        else:
            raise Exception("Unknown primitive service type {}".format(self.type))

        ba.append(tag)

        if self.type != BYTES_TYPE and isinstance(self.value, bytes) :
            ba.extend(self.value)
        else:
            ba.extend(get_val(self.value))

        return bytes(ba)

    def __bytes__(self) -> bytes:
        return self.encode()

def encode_primitive_array(a):
    ba = bytearray()
    
    if len(a) == 0:
        ba.append(1)
        ba.append(0)
    else:
        ba.extend(SDNVUtil.encode(len(a)))
        ba.extend(a)

    return bytes(ba)

class ConstructedService(Service):
    tag:int = None
    
    def __init__(self, tag: int):
        self.tag = tag

    @abstractmethod
    def get_services(self):
        pass

    def encode(self) -> bytes:
        ba = bytearray()
        ba.append(self.tag)

        contentba = bytearray()
        for s in self.get_services():
            contentba.extend(bytes(s))
        
        ba.extend(SDNVUtil.encode(len(contentba)))
        ba.extend(contentba)

        return bytes(ba)

class TCPCLService(ConstructedService):
    
    address:IPv4Address = None
    port:int = None

    def __init__(self, address: Union[IPv4Address, IPv6Address, str], port: int):
        if isinstance(address, str):
            address = ip_address(address)
        
        if isinstance(address, IPv4Address):
            self.tag = 64
        elif isinstance(address, IPv6Address):
            self.tag = 66
        else:
            raise Exception("Invalid address type")

        self.address = address
        self.port = port
    
    def get_services(self):
        address_type = None
        if isinstance(self.address, IPv4Address):
            address_type = FIXED32_TYPE
        elif isinstance(self.address, IPv6Address):
            address_type = BYTES_TYPE

        return (
            PrimitiveService(self.address.packed, type=address_type),
            PrimitiveService(self.port, type=FIXED16_TYPE)
        )