#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Библиотека, содежит классы:
    Printer - для печати вращающейся палочки, индикатор активности

+ getIP
@author: ttyUSB0
"""
import socket
import sys

clip = lambda n, minn, maxn: max(min(maxn, n), minn) # https://stackoverflow.com/a/5996949/5355749

def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
    IP = s.getsockname()[0]
    s.close()
    return IP


#%% Принтер
class Printer():
    """Print things to stdout on one line dynamically"""
    def __init__(self, prefix=''):
        self.i = 0
        self.item = ['|', '/', '-', '\\']
        self.prefix = prefix
    def __enter__(self):
        return self
    def it(self):
        sys.stdout.write("\r\x1b[K" + self.prefix + self.item[self.i])
        sys.stdout.flush()
        self.i += 1
        if self.i==len(self.item):
            self.i = 0
    def asterisk(self):
        sys.stdout.write("\r\x1b[K" + self.prefix + '*')
        sys.stdout.flush()
    def __exit__(self, exc_type, exc_value, traceback):
        print('\n')