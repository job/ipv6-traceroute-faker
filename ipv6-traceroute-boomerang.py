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
# 
# Example output which illustrates the path from iij01.ring.nlnog.net (in Japan)
# to boomerang.atrato.net, and back to iij01. Starting from hop 16 the packets
# are mangled by this python script. 
#
#   job@iij01.ring.nlnog.net:~$ mtr -r -c 1 -w -6 boomerang.atrato.net
#   HOST: iij01.ring.nlnog.net              Loss%   Snt   Last   Avg  Best  Wrst StDev
#     1.|-- 2001:240:10c:5:219:30ff:fec6:d49b  0.0%     2    0.5   0.5   0.5   0.6   0.1
#     2.|-- 2001:240:bb43:1002::2              0.0%     1    1.3   1.3   1.3   1.3   0.0
#     3.|-- tky006bb01.IIJ.Net                 0.0%     1    1.0   1.0   1.0   1.0   0.0
#     4.|-- 2001:240:bb00:8021::7e             0.0%     1    1.2   1.2   1.2   1.2   0.0
#     5.|-- tky001bf01.IIJ.Net                 0.0%     1    1.1   1.1   1.1   1.1   0.0
#     6.|-- sjc002bf00.iij.net                 0.0%     1  106.0 106.0 106.0 106.0   0.0
#     7.|-- plt001bb00.iij.net                 0.0%     1  106.9 106.9 106.9 106.9   0.0
#     8.|-- plt001bb01.iij.net                 0.0%     1  106.8 106.8 106.8 106.8   0.0
#     9.|-- tge1-3.sjo01-1.us.as5580.net       0.0%     1  119.8 119.8 119.8 119.8   0.0
#    10.|-- eth4-2.r1.den1.us.atrato.net       0.0%     1  130.5 130.5 130.5 130.5   0.0
#    11.|-- eth3-1.r1.chi1.us.atrato.net       0.0%     1  176.1 176.1 176.1 176.1   0.0
#    12.|-- eth1-4.r1.nyc1.us.atrato.net       0.0%     1  198.9 198.9 198.9 198.9   0.0
#    13.|-- eth1-5.core1.lon1.uk.atrato.net    0.0%     1  257.9 257.9 257.9 257.9   0.0
#    14.|-- 2a02:d28:5580:1::96                0.0%     1  264.0 264.0 264.0 264.0   0.0
#    15.|-- eth4-1.r1.ams2.nl.atrato.net       0.0%     1  276.5 276.5 276.5 276.5   0.0
#    16.|-- boomerang.atrato.net               0.0%     1  270.0 270.0 270.0 270.0   0.0
#    17.|-- ve1007.r1.ams2.nl.atrato.net       0.0%     1  281.5 281.5 281.5 281.5   0.0
#    18.|-- eth1-1.core1.ams2.nl.atrato.net    0.0%     1  267.3 267.3 267.3 267.3   0.0
#    19.|-- 2a02:d28:5580:1::95                0.0%     1  266.9 266.9 266.9 266.9   0.0
#    20.|-- eth4-2.r1.nyc1.us.atrato.net       0.0%     1  301.2 301.2 301.2 301.2   0.0
#    21.|-- ipv6-iij.net                       0.0%     1  281.1 281.1 281.1 281.1   0.0
#    22.|-- nyc002bb11.iij.net                 0.0%     1  271.9 271.9 271.9 271.9   0.0
#    23.|-- sjc002bb01.iij.net                 0.0%     1  258.3 258.3 258.3 258.3   0.0
#    24.|-- sjc002bf02.iij.net                 0.0%     1  262.4 262.4 262.4 262.4   0.0
#    25.|-- 2001:48b0:bb00:803e::75            0.0%     1  261.2 261.2 261.2 261.2   0.0
#    26.|-- tky001bb11.IIJ.Net                 0.0%     1  261.2 261.2 261.2 261.2   0.0
#    27.|-- tky006bb01.IIJ.Net                 0.0%     1  261.8 261.8 261.8 261.8   0.0
#    28.|-- tky006gate01a.IIJ.Net              0.0%     1  261.3 261.3 261.3 261.3   0.0
#    29.|-- 2001:240:bb43:1002::6              0.0%     1  261.1 261.1 261.1 261.1   0.0
#    30.|-- ???                               100.0     1    0.0   0.0   0.0   0.0   0.0
#   job@iij01.ring.nlnog.net:~$
#   
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
