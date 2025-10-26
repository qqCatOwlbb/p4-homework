#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Reason-GPL: import-scapy
import socket
import sys

from scapy.all import (
    IP,
    UDP,
    Ether,
    Packet,
    bind_layers,
    get_if_hwaddr,
    get_if_list,
    sendp
)
from scapy.fields import *


def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

class SourceRoute(Packet):
   fields_desc = [ BitField("bos", 0, 1),
                   BitField("port", 0, 15)]
class IPv4Only(Packet):
   fields_desc = [] # Placeholder for plain IP packets

bind_layers(Ether, SourceRoute, type=0x1234)
bind_layers(SourceRoute, SourceRoute, bos=0)
bind_layers(SourceRoute, IP, bos=1)
# Add bind layer for pure IPv4 traffic (EtherType 0x800 is default for IP)


def main():

    if len(sys.argv)<2:
        print('pass 1 argument: <destination>')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()
    print("sending on interface %s to %s" % (iface, str(addr)))

    while True:
        print()
        s = str(input('Type space separated port nums (example: "2 3 2 2 1"), "ip" for IPv4, or "q" to quit: '))
        if s == "q":
            break;
        print()

        pkt = None
        if s.lower() == "ip":
            # IPv4 only packet (EtherType 0x800)
            pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff') / \
                  IP(dst=addr) / UDP(dport=4321, sport=1234) / b"IPv4 packet"
        else:
            # Source Routing packet (EtherType 0x1234)
            i = 0
            pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff');
            port_list_ok = True
            
            for p in s.split(" "):
                try:
                    pkt = pkt / SourceRoute(bos=0, port=int(p))
                    i = i+1
                except ValueError:
                    port_list_ok = False
                    break
            
            if not port_list_ok or not pkt.haslayer(SourceRoute):
                print("Invalid input for Source Routing.")
                continue

            # Set the 'bottom of stack' bit on the last SourceRoute header
            if pkt.haslayer(SourceRoute):
                pkt.getlayer(SourceRoute, i).bos = 1

            # Append encapsulated IP and payload
            pkt = pkt / IP(dst=addr) / UDP(dport=4321, sport=1234) / b"Source Route packet"
            

        pkt.show2()
        sendp(pkt, iface=iface, verbose=False)


if __name__ == '__main__':
    main()