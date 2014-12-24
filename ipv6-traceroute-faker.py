#!/usr/bin/env python
# ipv6 traceroute path faker
#
# Written by Job Snijders <job@instituut.net> 2013, 2014
#
# do something like this to guide the packets to this program:
# ip6tables -t raw -A PREROUTING -d 2a02:898:52:666::/64 -j NFQUEUE --queue-num 0
# further more we need root privileges
#
# apt-get install python-scapy libnetfilter-queue-dev python-nfqueue
#
# Inner workings:
# we attach to a netfilterqueue and throw every packet at the do_callback
# function
#
# Special thanks to Lennert Buijtenhek for pointing out that the previous
# version maintained a lot of state without any need to do so.


prefix = "2a02:898:52:666::"
destination = "2a02:898:52:666::ffff"
path_length = 19

# the above settings allow you to do something like this:
# (at hop 5 we go into this python programme, path_length makes it stop at hop 23)
# job@ntt02:~$ mtr -w -r -c 1 2a02:898:52:666::ffff
# HOST: ntt02.ring.nlnog.net                         Loss%   Snt   Last   Avg  Best  Wrst StDev
#   1.|-- virbr0.scarlett.6core.net                     0.0%     2    0.1   0.4   0.1   0.7   0.4
#   2.|-- ge-101-0-0-36.r02.amstnl02.nl.bb.gin.ntt.net  0.0%     1    0.9   0.9   0.9   0.9   0.0
#   3.|-- ge-1-1-0.eunetworks-1.router.nl.coloclue.net  0.0%     1    1.0   1.0   1.0   1.0   0.0
#   4.|-- 2a02:898:0:20::52:1                           0.0%     1    0.8   0.8   0.8   0.8   0.0
#   5.|-- 2a02:898:52:666::1                            0.0%     1   47.9  47.9  47.9  47.9   0.0
#   6.|-- 2a02:898:52:666::2                            0.0%     1   22.4  22.4  22.4  22.4   0.0
#   7.|-- 2a02:898:52:666::3                            0.0%     1   22.2  22.2  22.2  22.2   0.0
#   8.|-- 2a02:898:52:666::4                            0.0%     1   18.5  18.5  18.5  18.5   0.0
#   9.|-- 2a02:898:52:666::5                            0.0%     1   13.5  13.5  13.5  13.5   0.0
#  10.|-- 2a02:898:52:666::6                            0.0%     1   43.6  43.6  43.6  43.6   0.0
#  11.|-- 2a02:898:52:666::7                            0.0%     1   31.2  31.2  31.2  31.2   0.0
#  12.|-- 2a02:898:52:666::8                            0.0%     1   88.2  88.2  88.2  88.2   0.0
#  13.|-- 2a02:898:52:666::9                            0.0%     1  121.2 121.2 121.2 121.2   0.0
#  14.|-- 2a02:898:52:666::10                           0.0%     1  135.6 135.6 135.6 135.6   0.0
#  15.|-- 2a02:898:52:666::11                           0.0%     1  158.8 158.8 158.8 158.8   0.0
#  16.|-- 2a02:898:52:666::12                           0.0%     1  161.2 161.2 161.2 161.2   0.0
#  17.|-- 2a02:898:52:666::13                           0.0%     1  159.2 159.2 159.2 159.2   0.0
#  18.|-- 2a02:898:52:666::14                           0.0%     1  256.3 256.3 256.3 256.3   0.0
#  19.|-- 2a02:898:52:666::15                           0.0%     1  320.6 320.6 320.6 320.6   0.0
#  20.|-- 2a02:898:52:666::16                           0.0%     1  326.5 326.5 326.5 326.5   0.0
#  21.|-- 2a02:898:52:666::17                           0.0%     1  286.6 286.6 286.6 286.6   0.0
#  22.|-- 2a02:898:52:666::18                           0.0%     1  282.3 282.3 282.3 282.3   0.0
#  23.|-- 2a02:898:52:666::ffff                         0.0%     1  334.0 334.0 334.0 334.0   0.0
#
import asyncore
from nfqueue import queue, NFQNL_COPY_PACKET
from socket import AF_INET6
from scapy.all import IPv6, ICMPv6TimeExceeded, send


def do_callback(payload):
    data = payload.get_data()
    pkt = IPv6(data)
    if pkt.version == 6:
        if pkt.nh == 58:
            reply = IPv6()
            reply.dst = pkt[IPv6].src
            hl = pkt[IPv6].hlim
            if hl == path_length:
                reply.src = destination
            else:
                reply.src = "%s%s" % (prefix, hl)
            icmp = ICMPv6TimeExceeded()
            icmp.code = 0
            try:
                send(reply/icmp/pkt, verbose=0)
            except UnboundLocalError:
                print "meh"
                pass


class AsyncNfQueue(asyncore.file_dispatcher):
    def __init__(self, cb, nqueue=0, family=AF_INET6, maxlen=5000, map=None):
        self._q = queue()
        self._q.set_callback(cb)
        self._q.fast_open(nqueue, family)
        self._q.set_queue_maxlen(maxlen)
        self.fd = self._q.get_fd()
        asyncore.file_dispatcher.__init__(self, self.fd, map)
        self._q.set_mode(NFQNL_COPY_PACKET)

    def handle_read(self):
        print "Processing at most 50 events"
        self._q.process_pending(50)

    def writable(self):
        return False

async_queue = AsyncNfQueue(do_callback)
asyncore.loop()
