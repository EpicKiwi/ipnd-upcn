import socket
import uuid
from pyupcn.aap import AAPMessage, AAPMessageType, InsufficientAAPDataError
from pyupcn.agents import ConfigMessage, RouterCommand


class UPCNAAP:

    def __init__(self, socket, eid_suffix=None):
        self.socket = socket
        self.eid_suffix = eid_suffix if eid_suffix is not None else str(
            uuid.uuid4())

    def __enter__(self):
        msg_welcome = self.recv()
        assert msg_welcome.msg_type == AAPMessageType.WELCOME
        self.eid = msg_welcome.eid

        self.socket.send(AAPMessage(AAPMessageType.REGISTER,
                         self.eid_suffix).serialize())
        msg_ack = self.recv()
        assert msg_ack.msg_type == AAPMessageType.ACK

        return self

    def __exit__(self, *args):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

        return self

    def recv(self):
        buf = bytearray()
        msg = None
        while msg is None:
            buf += self.socket.recv(1)
            try:
                msg = AAPMessage.parse(buf)
            except InsufficientAAPDataError:
                continue
        return msg

    def send(self, destination, bundle):
        self.socket.send(AAPMessage(AAPMessageType.SENDBUNDLE,
                                    destination,
                                    bundle).serialize())
        msg_sendconfirm = self.recv()
        assert msg_sendconfirm.msg_type == AAPMessageType.SENDCONFIRM

    def set_contact(self, other_eid: str, cla_address: str, contacts=[], reachable_eids=[]):
        config_msg = bytes(ConfigMessage(
            other_eid,
            cla_address,
            contacts=contacts,
            reachable_eids=reachable_eids,
            type=RouterCommand.UPDATE
        ))
        self.send(self.eid + "/config", config_msg)
