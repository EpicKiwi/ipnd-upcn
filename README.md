# IPND µPCN

*Implementation of the DTN IP Neighbor Discovery protocol with route definition in µPCN*

This is a Python implementation of the IPND protocol advertizing network about µPCN node.

## Getting started

By default, ipnd will advertize machine address with `TCPCLService` on `224.0.0.26:3003` on ipv4 and `[FF02::1]:3003` on ipv6

Install ipnd with the following command

```
make install
```

and start service with the following

```
systemctl start --user ipnd
```