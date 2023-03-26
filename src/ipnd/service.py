from abc import ABC, abstractmethod
from .sdnv import SDNVUtil
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
    
    def decode_with_offset(bytes: bytes, services_by_tag = None):
        if services_by_tag is None:
            services_by_tag = DEFAULT_SERVICES

        tag = bytes[0]

        if tag not in services_by_tag:
            return UnknownService.decode_with_offset(bytes)
        
        else:
            return services_by_tag[tag].decode_with_offset(bytes)

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
            get_val = lambda v: (int(v),)

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

    def decode_with_offset(bytes: bytes):
        tag = bytes[0]
        offset = 1

        type = None
        value = None

        if tag == 0:
            type = BOOL_TYPE
            value = bytes[offset] == 1
            offset += 1

        elif tag == 1:
            type = UINT_TYPE
            (v, num_bytes) = SDNVUtil.decode(bytes, offset)
            value = v
            offset += num_bytes

        elif tag == 2:
            type = SINT_TYPE
            (v, num_bytes) = SDNVUtil.decode(bytes, offset)
            value = v
            offset += num_bytes

        elif tag == 3:
            type = FIXED16_TYPE
            value = int.from_bytes(bytes[offset:offset+2], 'big')
            offset += 2

        elif tag == 4:
            type = FIXED32_TYPE
            value = int.from_bytes(bytes[offset:offset+4], 'big')
            offset += 4

        elif tag == 5:
            type = FIXED64_TYPE
            value = int.from_bytes(bytes[offset:offset+8], 'big')
            offset += 8
            
        elif tag == 6:
            type = FLOAT_TYPE
            value = struct.unpack("!f", bytes[offset:offset+4])
            offset += 4

        elif tag == 7:
            type = DOUBLE_TYPE
            value = struct.unpack("!d", bytes[offset:offset+8])
            offset += 8

        elif tag == 8:
            type = STRING_TYPE
            (length, num_bytes) = SDNVUtil.decode(bytes, offset)
            offset += num_bytes
            value = bytes[offset:offset+length].decode("ascii")
            offset += length
            
        elif tag == 9:
            type = BYTES_TYPE
            (length, num_bytes) = SDNVUtil.decode(bytes, offset)
            offset += num_bytes
            value = bytes[offset:offset+length]
            offset += length
        
        self = PrimitiveService(value, type)

        return (self, offset)

    def __bytes__(self) -> bytes:
        return self.encode()
    
    def __repr__(self):
        return """PrimitiveService {{ type={}, value={} }}""".format(self.type, self.value)

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

    @abstractmethod
    def decode_with_offset(bytes: bytes):
        pass

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
    
    def decode_with_offset(bytes: bytes):
        offset = 1
        
        (length, num_bytes) = SDNVUtil.decode(bytes, offset)
        offset += num_bytes

        (services, num_bytes) = decode_services(2, bytes[offset: offset+length])
        offset += num_bytes

        address = ip_address(services[0].value)
        port = services[1].value

        self = TCPCLService(address, port)

        return (self, offset)
    
    def __repr__(self):
        return """TCPCLService {{ address={}, port={} }}""".format(self.address, self.port)

class UnknownService(Service):
    def decode_with_offset(bytes: bytes):
        self = UnknownService()

        self.tag = bytes[0]
        offset = 1
        
        (length, num_bytes) = SDNVUtil.decode(bytes, offset)
        offset += num_bytes

        self.buffer = bytes[offset: offset+length]

        return (self, offset+length)

    def encode(self) -> bytes:
        ba = bytearray()
        ba.append(self.tag)
        
        ba.extend(SDNVUtil.encode(len(self.buffer)))
        ba.extend(self.buffer)

        return bytes(ba)
    
    def __repr__(self):
        return """UnknownService {{ tag={}, length={} }}""".format(self.tag, len(self.buffer))

def decode_services(n_services, bytes, services_by_tag = None):
    offset = 0
    service_list = []
    
    for _ in range(n_services):
        (service, num_bytes) = Service.decode_with_offset(bytes[offset:], services_by_tag)
        service_list += (service,)
        offset += num_bytes

    return (service_list, offset)

DEFAULT_SERVICES = {
    0: PrimitiveService,
    1: PrimitiveService,
    2: PrimitiveService,
    3: PrimitiveService,
    4: PrimitiveService,
    5: PrimitiveService,
    6: PrimitiveService,
    7: PrimitiveService,
    8: PrimitiveService,
    9: PrimitiveService,
    64: TCPCLService,
    66: TCPCLService
}