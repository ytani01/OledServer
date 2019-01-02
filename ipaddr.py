#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import netifaces
import sys

#####
class ipaddr:
    def __init__(self):
        self._ip = {}
        self._if_name = []
        self._ip_addr = []
    
        for ifn in netifaces.interfaces():
            if ifn == 'lo':
                continue
                
            ifaddrs = netifaces.ifaddresses(ifn)

            try:
                ip = ifaddrs[netifaces.AF_INET]
            except(KeyError):
                continue

            self._if_name.append(ifn)
            
            self._ip[ifn] = []
            for addr in ip:
                ip1 = addr['addr']
                self._ip[ifn].append(ip1)
                self._ip_addr.append(ip1)

    def if_name(self, num=0):
        return self._if_name[num]

    def ip_addr(self, num=0):
        return self._ip_addr[num]

    def print(self):
        print(self._ip)
        print(self._if_name)
        print(self._ip_addr)
        
##### Main
def main():
    sys.argv.pop(0)
    ip=ipaddr()
    #ip.print()
    print(ip.ip_addr())

if __name__ == '__main__':
    main()
