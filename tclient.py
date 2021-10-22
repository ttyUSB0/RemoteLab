#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА
запрашивает порт 6502
слушает порт 6501

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
def control(t, theta, omega):
    """ управление """
    return np.sin(t)


#%% Основной цикл
plotter = tlib.PlotterObject()

# host = '192.168.1.150'
# host = '89.22.167.12'

t0 = time.time()
theta_i, omega_i = 0., 0.
with tlib.Communicator(hostIP='192.168.1.14') as comm:
    while True:
        try:
            u = control(time.time()-t0, theta_i, omega_i)
            comm.control(u)
            theta_i, omega_i = comm.measure() # принимаем
            plotter.addData(time.time()-t0, (theta_i, omega_i, u))
            time.sleep(0.05)

        except KeyboardInterrupt:
                print('\n[*] Exit...')
                break # выход из цикла






