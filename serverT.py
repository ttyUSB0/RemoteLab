#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер UDP, имитатор КА
слушает порт 6505, возврат данных в порт источника
запуск с параметром номер порта

- посылка состоит из double управления вентилятором
по любой посылке - возврат 13-элем. вектора
1. текущее переданное управление float u
2. вектор из 9 элементов float (MPU9250)
wx, wy, wz [deg/s]
ax, ay, az [g]
mx, my, mz [mT]
3. вектор из 3 элементов float (QMC5883)
m2x, m2y, m2z [mT]

Все вектора в приборных СК, нефильтрованные, несмещённые,
моделирует ДУ вертушки, добавляя шум датчиков

@author: ttyUSB0
"""

timeout = 1.5 # после этого времени вентиляторы принудительно стопятся
timeoutGreat = 90 # за это время НУ становятся нулевыми

import socket
import serverLib as lib

import numpy as np
import random

from scipy.integrate import odeint
import time
# import matplotlib.pyplot as plt
import struct
import sys

#%% ka, ku, J - идентифицированы! dt=140мс
ka = 3.32914427e-05
ku = 6.36414245e-01
Jres = 1/6.24375258e-02
# array([1.43155798e-07, 5.88172838e-01, 4.74464837e-02])
def myode(y, t, u):
    """ система ДУ, описывающая вертушку """
    theta, omega = y
    Mu = ku*u if t<=timeout else 0
    dydt = [omega, (Mu - ka*omega**2*np.sign(omega))*Jres]
    return dydt

#%% Основной код
if __name__ == "__main__":
    if len(sys.argv)<2:
        bind_port = 6505
    else:
        bind_port = int(sys.argv[1])

    #% Сокет
    print('[*] Starting server')
    bind_ip = lib.getIP()
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
    server.settimeout(1.5)
    print('[*] Ready to receive Ack on %s:%d' % (bind_ip,bind_port))

    #% Основной цикл
    y0 = [0., 0.] # theta, omega in rad
    tPrev = time.time()

    random.seed()
    bounds = [0.05, 0.05, 0.05,
              2., 2., 2.,
              3., 3., 3.,
              0.5, 0.5, 0.5] # диапазон шума (+/- разброс)

    with lib.Printer() as p:
        while True:
            sendAns = False

            try:
                data, senderAddr = server.recvfrom(64)
                #print('[*] ack from %s:%d'%(senderAddr[0], senderAddr[1]))
                fan = struct.unpack('f',data)
                sendAns = True
                p.it()

            except socket.timeout:
                fan = [0]
                p.asterisk()

            except KeyboardInterrupt:
                print('\n[*] Exit...')
                break # выход из цикла

            fan = lib.clip(fan[0], -1., 1.)
            tNow = time.time()
            t = np.linspace(0, tNow-tPrev, 2)
            sol = odeint(myode, y0, t, args=(fan,), hmax=0.01) #, hmax=0.01

            y0 = sol[-1,:]
            tPrev = tNow

            if sendAns: # отвечаем данными MPU
                r = [] # шум по датчикам
                for b in bounds:
                    r.append(random.uniform(-b, b))
                aR = np.array(r[:3])
                wR = np.array(r[3:6])
                m1R = np.array(r[6:9])
                m2R = np.array(r[9:])

                # magnet field im uT
                mx = 45*np.cos(y0[0])
                my = 45*np.sin(y0[0])

                ans = [fan] # u
                # acceleration [g]
                ans.extend(np.array([-1., 0., 0.]) +aR)
                # angular velocity [deg/s]
                ans.extend(np.array([y0[1]*180/np.pi, 0., 0.]) +wR)
                #magnet field (AK) [uT]
                ans.extend(np.array([-my-16.2, 0., -mx-8.8]) +m1R)
                #magnet field (QMC) [uT]
                ans.extend(np.array([-my, 0., -mx]) +m2R)

                # передаём в приборной СК (см. документацию на MPU-9250)
                msg = struct.pack('13f', *ans)
                server.sendto(msg, senderAddr)

    #% Сокет закрываем
    server.close()
