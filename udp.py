#!/usr/bin/env python3
import argparse
import socket
import sys

_socket = None

def parse_args():
    desc = "UDP client/server script and library for NAT testing"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', '--client', metavar="HOST", nargs='*')
    parser.add_argument('-s', '--server', metavar="PORT", type=int)
    args = parser.parse_args()
    if not args.client and not args.server:
        parser.error("Must specify client-mode or server-mode")
    if args.client and args.server:
        parser.error("Cannot specify both client-mode and server-mode")
    return args


def make_socket(port=None):
    global _socket
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if port:
        _socket.bind(('0.0.0.0', port))


def send(host, port, message):
    if not _socket:
        make_socket()
    host = socket.gethostbyname(host)
    _socket.sendto(message.encode('ascii'), (host, port))
    print("sent", '"'+message+'"', "to", (host, port), "from port",
          _socket.getsockname()[1])


def recv():
    """ returns (host, port, message) """
    if not _socket:
        make_socket()
    bytes, address = _socket.recvfrom(1024)
    message = bytes.decode("ascii")
    print("received", message, "from", address)
    return address[0], address[1], message


if __name__ == '__main__':
    args = parse_args()
    print(args)
    try:
        if args.client:
            make_socket()
            for host in args.client:
                send(host, 7777, 'test blah')
            for i in range(len(args.client)):
                recv()
        elif args.server:
            make_socket(port=args.server)
            while True:
                host, port, message = recv()
                send(host, port, "reply to " + message)
    except KeyboardInterrupt:
        sys.exit(1)
