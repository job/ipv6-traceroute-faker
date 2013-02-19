IPv6 Traceroute faker
=====================

This script will allow you to create a fake IPv6 path. It will reply to
ICMPEchoRequests with the appropiate source address and TTL exceeded messages.

This allows you to broadcast a message to the world through your reverse DNS
entries :-)

Install:
--------

    sudo apt-get install python-scapy memcached python-memcache
    sudo pip install NetfilterQueue
    sudo ip6tables -t raw -A PREROUTING -d 2a02:d28:601:1::/64 -j NFQUEUE --queue-num 0

Edit the values at the top of the script to reflect your prefix and destination!

Route the subnet to your linux machine which runs the script and launch it:

    sudo python ./ipv6-traceroute-faker.py

test with:

    sudo traceroute6 -I $ipv6_destination
    mtr $ipv6_destination

Example:
--------

    job@intouch01.ring.nlnog.net:~$ mtr -w -c 1 -r 2a02:d28:601:1::ffff
    HOST: intouch01.ring.nlnog.net                                                         Loss%   Snt   Last   Avg  Best  Wrst StDev
      1.|-- 2001:6e0:100:4001::1                                                              0.0%     2    1.1   1.1   1.1   1.1   0.0
      2.|-- 2001:67c:21b4:8954:1::9                                                           0.0%     1    1.7   1.7   1.7   1.7   0.0
      3.|-- 2001:67c:21b4:8954:1::9                                                           0.0%     1    1.7   1.7   1.7   1.7   0.0
      4.|-- eth15-2.r1.ams2.nl.atrato.net                                                     0.0%     1    8.5   8.5   8.5   8.5   0.0
      5.|-- o-----------------------------------------o.atrato.net                            0.0%     1    7.9   7.9   7.9   7.9   0.0
      6.|-- Hi_there.atrato.net                                                               0.0%     1    8.6   8.6   8.6   8.6   0.0
      7.|-- You_are_a_curious_mind.atrato.net                                                 0.0%     1    9.7   9.7   9.7   9.7   0.0
      8.|-- A_warm_welcome_to_our_backbone_network.atrato.net                                 0.0%     1    7.8   7.8   7.8   7.8   0.0
      9.|-- We_are_Atrato_Communications.atrato.net                                           0.0%     1    8.1   8.1   8.1   8.1   0.0
     10.|-- We_operate_a_rather_big_network.atrato.net                                        0.0%     1    8.7   8.7   8.7   8.7   0.0
     11.|-- We_have_gear_all_over_the_world.atrato.net                                        0.0%     1    7.9   7.9   7.9   7.9   0.0
     12.|-- Ranging_from_Stockholm.atrato.net                                                 0.0%     1    8.3   8.3   8.3   8.3   0.0
     13.|-- through_Amsterdam_to_Miami.atrato.net                                             0.0%     1    7.9   7.9   7.9   7.9   0.0
     14.|-- And_even_in_Palo_Alto_we_do_peering.atrato.net                                    0.0%     1    8.0   8.0   8.0   8.0   0.0
     15.|-- Our_multi-terabit_network_is.one_of_the_fastest_growing_networks.atrato.net       0.0%     1    9.8   9.8   9.8   9.8   0.0
     16.|-- And_we_are_looking_for_smart.and.ambitious_system_or_network_engineers.atrato.ne  0.0%     1    8.0   8.0   8.0   8.0   0.0
     17.|-- 2013.will_be_a_year_full_of_awesomeness.atrato.net                                0.0%     1    8.5   8.5   8.5   8.5   0.0
     18.|-- You_can_be_part_of_our_operation.atrato.net                                       0.0%     1    8.0   8.0   8.0   8.0   0.0
     19.|-- Our_offices_are_located_near.Amsterdam_Netherlands.atrato.net                     0.0%     1   11.6  11.6  11.6  11.6   0.0
     20.|-- you_can_check_out_our.peeringdb_record.for_an_overview.atrato.net                 0.0%     1    8.1   8.1   8.1   8.1   0.0
     21.|-- as5580.peeringdb.net                                                              0.0%     1    7.7   7.7   7.7   7.7   0.0
     22.|-- for_more_information_contact_me_at.job_at_atrato_com.anytime.atrato.net           0.0%     1    7.9   7.9   7.9   7.9   0.0
     23.|-- hope_to_see_you_soon.at.atrato.net                                                0.0%     1    7.6   7.6   7.6   7.6   0.0
    job@intouch01.ring.nlnog.net:~$ 
    
