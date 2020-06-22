#!/usr/bin/env python3
"""
This module contains code from https://github.com/Akhavi/pyping

LICENSE from that project:
The original code derived from ping.c distributed in Linux's netkit.
That code is copyright (c) 1989 by The Regents of the University of California.
That code is in turn derived from code written by Mike Muuss of the
US Army Ballistic Research Laboratory in December, 1983 and
placed in the public domain. They have my thanks.

Copyright (c) Matthew Dixon Cowles, <http://www.visi.com/~mdc/>.
Distributable under the terms of the GNU General Public License
version 2. Provided with no warranties of any sort.

See AUTHORS for complete list of authors and contributors.
"""

import argparse
import socket
import struct
import sys

# ICMP parameters
ICMP_ECHOREPLY = 0 # Echo reply (per RFC792)
ICMP_ECHO = 8 # Echo request (per RFC792)
ICMP_MAX_RECV = 2048 # Max size of incoming buffer

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
    parser.add_argument('-o', '--reply-other', action="store_true",
                        help="Server will reply to client packet from a \
                        different port in addition to the normal reply.")
    args = parser.parse_args()
    if not args.client and not args.server:
        parser.error("Must specify client-mode or server-mode")
    if args.client and args.server:
        parser.error("Cannot specify both client-mode and server-mode")
    return args


def make_socket(port=None):
    global _socket
    try:
        _socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    except PermissionError:
        print("You must be root (or mess with setcap to run this program)")
        sys.exit(1)


def calculate_checksum(source_string):
    """
    A port of the functionality of in_cksum() from ping.c
    Ideally this would act on the string as a series of 16-bit ints (host
    packed), but this works.
    Network data is big-endian, hosts are typically little-endian
    """
    countTo = (int(len(source_string) / 2)) * 2
    sum = 0
    count = 0
    
    # Handle bytes in pairs (decoding as short ints)
    loByte = 0
    hiByte = 0
    while count < countTo:
        if (sys.byteorder == "little"):
            loByte = source_string[count]
            hiByte = source_string[count + 1]
        else:
            loByte = source_string[count + 1]
            hiByte = source_string[count]
        sum = sum + (hiByte * 256 + loByte)
        count += 2
    
    # Handle last byte if applicable (odd-number of bytes)
    # Endianness should be irrelevant in this case
    if countTo < len(source_string): # Check for odd length
        loByte = source_string[len(source_string) - 1]
        sum += loByte
    
    sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                      # uses signed ints, but overflow is unlikely in ping)
    
    sum = (sum >> 16) + (sum & 0xffff)  # Add high 16 bits to low 16 bits
    sum += (sum >> 16)                  # Add carry from above (if any)
    answer = ~sum & 0xffff              # Invert and truncate to 16 bits
    answer = socket.htons(answer)
    
    return answer


def make_echo_packet(id, sequence):
    """
    Make the binary string contents of an ICMP echo request

    Header is type (8), code (8), checksum (16), id (16), sequence (16)
    """
    packet_size = 55
    checksum = 0
    
    # Make a dummy header with a 0 checksum.
    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, checksum, id, sequence
    )
    
    padBytes = []
    startVal = 0x42
    for i in range(startVal, startVal + (packet_size)):
        padBytes += [(i & 0xff)]  # Keep chars in the 0-255 range
    data = bytes(padBytes)
    
    # Calculate the checksum on the data and the dummy header.
    checksum = calculate_checksum(header + data) # Checksum is in network order
    
    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, checksum, id, sequence
    )
    
    packet = header + data
    return packet


def send(host, id, sequence, message):
    if not _socket:
        make_socket()
    host = socket.gethostbyname(host)
    packet = make_echo_packet(id, sequence)
    _socket.sendto(packet, (host, 0))
    print("sent", '"'+message+'"', "to", host, "id:", id, "sequence:", sequence)


def recv():
    """ returns (host, port, message) """
    if not _socket:
        make_socket()
    bytes, address = _socket.recvfrom(1024)
    message = bytes.decode("ascii")
    print("received", "(packet #" + str(received) + ')', message, "from", address)
    return address[0], address[1], message


if __name__ == '__main__':
    args = parse_args()
    print(args)
    try:
        received = 1
        if args.client:
            n = 1
            if args.sweep:
                n = args.sweep
            for i in range(n):
                make_socket()
                for host in args.client:
                    # increment the ID each time to make new sessions
                    send(host, i, 1234, 'test blah')
                if not args.sweep:
                    while True:
                        recv()
        elif args.server:
            make_socket(port=args.server)
            while True:
                host, port, message = recv()
                received += 1
                send(host, port, "reply to " + message)
                if args.reply_other:
                    send_from_new_socket(host, port, message + " from other port")
    except KeyboardInterrupt:
        sys.exit(1)
