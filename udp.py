#!/usr/bin/env python3
import argparse
import socket
import sys

_socket = None

def parse_args():
    desc = "UDP client/server script and library for NAT testing"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', '--client', metavar="HOST", nargs='*')
    parser.add_argument('-p', '--port', metavar="DESTPORT", type=int,
                        default=7777)
    parser.add_argument('-s', '--server', metavar="PORT", type=int)
    parser.add_argument('-w', '--sweep', metavar="N", type=int,
                        help="Sweep N connections to the same destination. \
                        Don't wait for a response.")
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


def send_from_new_socket(host, port, message):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host = socket.gethostbyname(host)
    s.sendto(message.encode('ascii'), (host, port))
    print("sent", '"'+message+'"', "to", (host, port), "from port",
          s.getsockname()[1])


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
            n = 1
            if args.sweep:
                n = args.sweep
            for i in range(n):
                make_socket()
                for host in args.client:
                    send(host, args.port, 'test blah')
                if not args.sweep:
                    while True:
                        recv()
        elif args.server:
            make_socket(port=args.server)
            while True:
                host, port, message = recv()
                send(host, port, "reply to " + message)
                send_from_new_socket(host, port, message + " from other port")
    except KeyboardInterrupt:
        sys.exit(1)
