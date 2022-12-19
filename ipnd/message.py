from sdnv import SDNVUtil

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
            beid = self.eid.encode("ascii") # TODO check if ascii or other encoding for eid
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
    
    def __bytes__(self) -> bytes:
        return self.encode()