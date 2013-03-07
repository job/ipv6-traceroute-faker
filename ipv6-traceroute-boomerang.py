#!/usr/bin/env python
# IPv6 traceroute boomerang
#
# Written by Job Snijders <job.snijders@atrato.com> , March 2013
#
# do something like this to guide the packets to this program:
# ip6tables -t raw -A PREROUTING -d 2a02:d28:601:2::1/128 -j NFQUEUE --queue-num 1
# further more we need root privileges
# The target IPv6 address '2a02:d28:601:2::1' is what you can put into DNS as
# the boomerang hostname.
#
# For both the midpoint and the endpoint we create the same reverse DNS PTR
# record. This is to make the tool easier to use.
#
# apt-get install python-scapy memcached python-memcache libnetfilter-queue-dev python-nfqueue
#
# Purpose:
# When somebody traceroutes to the boomerang endpoint, packets after reaching
# the midpoint will be spoofed in such a way that effectively the originator
# ends up with a traceroute back to him or herself. So in one traceroute
# you can discover both the forward path, and the path _back_.

boomerang_target    = "2a02:d28:601:2::1"
boomerang_midpoint  = "2a02:d28:601:2::"
netfilterqueue      = 1
memcache_server     = ['127.0.0.1:11211']

import sys
import struct
import nfqueue
import threading
import memcache
from socket import AF_INET6
from scapy.all import *
mc = memcache.Client(memcache_server, debug=0)

def form_reply(pkt):
    global mc
    sender      = pkt[IPv6].src
    hoplimit    = pkt[IPv6].hlim
    key         = "boom_%s" % sender
    state       = mc.get(key)
    if (not state) or (hoplimit == state):
        if not state:
            mc.set(key, hoplimit, 300)
        ipv6        = IPv6()
        ipv6.src    = boomerang_midpoint
        ipv6.dst    = sender
        ipv6.hlim   = 64
        icmp        = ICMPv6TimeExceeded()
        icmp.id     = pkt[ICMPv6EchoRequest].id
        icmp.seq    = pkt[ICMPv6EchoRequest].seq
        icmp.code   = 0
        send(ipv6/icmp/pkt, verbose=0)
        return
    else:
        ipv6        = pkt
        ipv6.src    = sender
        ipv6.dst    = sender
        ipv6.hlim   -= 1
        send(ipv6, verbose=0)
        return

def do_callback(payload):
    global total
    data = payload.get_data()
    pkt = IPv6(data)
    if pkt.version == 6 and pkt.nh == 58:
        form_reply(pkt)
    sys.stdout.flush()
    return 1

if __name__ == "__main__":
    q = nfqueue.queue()
    print "open"
    q.open()
    print "bind"
    q.bind(AF_INET6)
    print "setting callback"
    q.set_callback(do_callback)
    print "creating queue"
    q.create_queue(netfilterqueue)
    q.set_queue_maxlen(50000)
    print "trying to run"
    try:
        q.try_run()
    except KeyboardInterrupt, e:
        print "interrupted"
    print "unbind"
    q.unbind(AF_INET6)
    print "close"
    q.close()
    sys.exit()
