#!/usr/bin/env python
# ipv6 traceroute path faker
# 
# Written by Job Snijders <job.snijders@atrato.com> in February 2013
#
# do something like this to guide the packets to this program:
# ip6tables -t raw -A PREROUTING -d 2a02:d28:601:1::/64 -j NFQUEUE --queue-num 0
# further more we need root privileges 
#
# apt-get install python-scapy memcached python-memcache libnetfilter-queue-dev python-nfqueue
# 
# Inner workings:
# we attach to a netfilterqueue and throw every packet at the form_reply def
# Because packets can come in from various locations around the internet
# we need to maintain some state, e.g. what the hoplimit was of the first new
# packet we see which is part of a mtr or tracroute run (a new sequence). 
# 
# 
prefix      = "2a02:d28:601:1::"
destination = "2a02:d28:601:1::ffff"
path_length = 19

import sys
import struct
import nfqueue
import memcache
from socket import AF_INET, AF_INET6, inet_ntoa
from scapy.all import *

mc = memcache.Client(['127.0.0.1:11211'], debug=1)

def form_reply(pkt):
    global mc
    ipv6        = IPv6()
    ipv6.dst    = pkt[IPv6].src
    icmp_id     = pkt[ICMPv6EchoRequest].id
    icmp_seq    = pkt[ICMPv6EchoRequest].seq
    hoplimit    = pkt[IPv6].hlim
    key         = "%s_%s" % (ipv6.dst, icmp_id)
    state       = mc.get(key)
    if not state:
        mc.set(key, hoplimit, 300)
        ipv6.src    = prefix
        icmp        = ICMPv6TimeExceeded()
        icmp.code   = 0
        send(ipv6/icmp/pkt, verbose=0)
        return
    if (hoplimit - state == 0) and state:
        ipv6.src    = prefix
        icmp        = ICMPv6TimeExceeded()
        icmp.code   = 0
        icmp.id     = icmp_id
        icmp.seq    = icmp_seq
        send(ipv6/icmp/pkt, verbose=0)
        return
    seen    = False
    i       = 0
    if state:
        while i < (path_length + 1 ):
            if hoplimit - state == i:
                ipv6.src    = "%s%s" % (prefix, i)
                icmp        = ICMPv6TimeExceeded()
                icmp.code   = 0
                icmp.id     = icmp_id
                icmp.seq    = icmp_seq
                seen        = True
            i   = i + 1
    if seen and (hoplimit == path_length):
        ipv6.src    = destination
        icmp        = ICMPv6EchoReply()
        icmp.id     = icmp_id
        icmp.seq    = icmp_seq
    print("Sending back an echo reply to %s from %s, key: %s, state: %s, hoplimit: %s, seq: %s, id: %s" % (ipv6.dst, ipv6.src, key, state, hoplimit, icmp_seq, icmp_id))
    data        = pkt[ICMPv6EchoRequest].data
    try:
        send(ipv6/icmp/pkt, verbose=0)
    except UnboundLocalError:
        pass

def do_callback(i, payload):
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
    q.create_queue(0)
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
