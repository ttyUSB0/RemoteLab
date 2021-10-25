#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА
запрашивает порт 6502


У сервера по любой посылке - возврат вектор из 9 элементов double
wx, wy, wz
ax, ay, az
mx, my, mz

@author: alex
"""
import sys
sys.path.append("/home/alex/Science/magACS/Acs1D/pyRemote/")
import tlib

import time
import numpy as np

#%% Закон управления
def control(t):
    """ управление """
    return np.sin(0.5*t)

#%% Основной цикл
plotter = tlib.Plotter()
t0 = time.time()

# '89.22.167.12'
# '192.168.1.150'

with tlib.Communicator(hostIP='89.22.167.12',
                       packetStruct='d'*12,
                       hostPort=6502, bindPort=6501) as comm:
    while True:
        try:
            u = control(time.time()-t0)
            comm.control(u)
            data = comm.measure() # принимаем
            plotter.addData(time.time()-t0, (data[5], data[6], u))
            time.sleep(0.05)

        except KeyboardInterrupt:
                print('\n[*] Exit...')
                break # выход из цикла






