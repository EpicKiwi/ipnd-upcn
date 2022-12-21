from .sdnv import SDNVUtil
from .service import Service, decode_services

class IPNDMessage:

    version:bytes = 0x04

    eid:str = None
    period:int = None
    sequence_number:int = 0
    services = []

    def encode(self) -> bytes:
        ba = bytearray()

        # Set versions

        ba.append(self.version)

        # Set flags

        flags = 0x00

        if self.eid is not None:
            flags |= 0b00000001

        if len(self.services) > 0:
            flags |= 0b00000010
        
        if self.period is not None:
            flags |= 0b00001000

        ba.append(flags)

        # Set sequence number

        ba += self.sequence_number.to_bytes(2, 'big', signed=False)

        # Set eid

        if self.eid is not None:
            beid = self.eid.encode("ascii")
            ba += SDNVUtil.encode(len(beid))
            ba += beid
        
        # Set services definition
        if len(self.services) > 0:
            ba += SDNVUtil.encode(len(self.services))
            for s in self.services:
                ba.extend(bytes(s))

        # Set period

        if self.period is not None:
            ba += SDNVUtil.encode(self.period)

        return bytes(ba)
    
    def decode_with_offset(bytes: bytes):
        self = IPNDMessage()
        
        self.version = bytes[0]
        
        flags = bytes[1]

        self.sequence_number = int.from_bytes(bytes[2:4], 'big')

        offset = 4

        # if we have a eid
        if flags & 0b00000001:
            (eid_length, num_bytes) = SDNVUtil.decode(bytes, offset)
            offset += num_bytes
            self.eid = bytes[offset:offset+eid_length].decode("ascii")
            offset = offset+eid_length
        
        # if we have services
        if (flags & 0b00000010) >> 1:
            (service_number, num_bytes) = SDNVUtil.decode(bytes, offset)
            offset += num_bytes

            (services, num_bytes) = decode_services(service_number, bytes[offset:])
            self.services = services
            offset += num_bytes
        
        # if we have period
        if (flags & 0b00001000) >> 3:
            (period, num_bytes) = SDNVUtil.decode(bytes, offset)
            self.period = period
            offset += num_bytes

        return (self, offset)

    def decode(bytes:bytes):
        return IPNDMessage.decode_with_offset(bytes)[0]

    def __bytes__(self) -> bytes:
        return self.encode()
    
    def __repr__(self):
        return """IPNDMessage {{ 
    version={}, 
    eid={}, 
    period={}, 
    sequence_number={},
    services=[\t{}]
}}""".format(
            self.version, 
            self.eid, 
            self.period, 
            self.sequence_number,
            ",\n\t\t".join(map(str, self.services)))
