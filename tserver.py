#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер UDP для обмена данными с имитатором КА
слушает порт 6505, возврат данных в порт источника

- посылка состоит из double управления вентилятором, ответ d*12 данные датчиков
- моделирует ДУ вертушки, добавляя шум датчиков
В конце будет раздваивать посылку в локальном адресе, на sudo
@author: alex
"""
bind_port = 6505
timeout = 1.5 # после этого временивентиляторы принудительно стопятся
timeoutGreat = 90 # за это время НУ становятся нулевыми

import socket
import sys
import numpy as np
from scipy.integrate import odeint
import time
# import matplotlib.pyplot as plt
import struct

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

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

clip = lambda n, minn, maxn: max(min(maxn, n), minn) # https://stackoverflow.com/a/5996949/5355749

kAir = 0.5
kFan = 0.2
J = 1/12
def myode(y, t, u):
    """ система ДУ, описывающая вертушку """
    theta, omega = y
    M = kFan*u if t<=timeout else 0 # https://stackoverflow.com/a/2802748/5355749
    dydt = [omega, (M - kAir*omega**2*np.sign(omega))/J]
    return dydt

#%% Сокет
print('[*] Starting server')
bind_ip = get_ip()
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
server.settimeout(1.5)
print('[*] Ready to receive Ack on %s:%d' % (bind_ip,bind_port))

#%% Основной цикл
y0 = [0., 0.0]
tPrev = time.time()
with Printer() as p:
    while True:
        sendAns = False

        try:
            data, senderAddr = server.recvfrom(64)
            #print('[*] ack from %s:%d'%(senderAddr[0], senderAddr[1]))
            fan = struct.unpack('d',data)
            sendAns = True
            p.it()

        except socket.timeout:
            fan = [0]
            p.asterisk()

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла

        fan = clip(fan[0], -1., 1.)
        tNow = time.time()
        t = np.linspace(0, tNow-tPrev, 2)
        sol = odeint(myode, y0, t, args=(fan,)) #, hmax=0.01

        y0 = sol[-1,:]
        tPrev = tNow

        if sendAns: # отвечаем данными MPU
            #a = np.array([0., 0., -1.])
            #g = np.array([0., 0., y0[1]])
            #m = np.array([0., 0., -1.]) #in uT
            # передаём в приборной СК (см. документацию на MPU-9250)
            msg = struct.pack('d'*2, y0[0], y0[1])
                          #a[0], a[1], a[2],
                          #g[0], g[1], g[2],
                          #m[0], m[1], m[2])
            server.sendto(msg, senderAddr)



#%% Сокет закрываем
server.close()