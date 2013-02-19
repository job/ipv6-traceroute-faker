IPv6 Traceroute faker
=====================

This script will allow you to create a fake IPv6 path. It will reply to
ICMPEchoRequests with the appropiate source address and TTL exceeded messages.

Install:
--------

    sudo apt-get install python-scapy memcached python-memcache
    sudo pip install NetfilterQueue
    sudo ip6tables -t raw -A PREROUTING -d 2a02:d28:601:1::/64 -j NFQUEUE --queue-num 0

Edit the values at the top of the script to reflect your prefix and destination!

Route the subnet to your linux machine which runs the script and launch it:

    sudo python ./ipv6-traceroute-faker.py

test with:

    sudo tracroute6 -I $ipv6_destination
    mtr $ipv6_destination

