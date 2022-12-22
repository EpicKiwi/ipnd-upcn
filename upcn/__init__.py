import socket
from .aap import UPCNAAP


def upcn_sock(eid_suffix, socket_path: str = "/tmp/upcn.socket"):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    return UPCNAAP(sock, eid_suffix)
