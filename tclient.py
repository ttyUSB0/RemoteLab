#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА

Сервер принимает double [-1..+1] - управление вентиляторами, коэфф. заполнения ШИМа
Возврат 12-элем. вектора:
1. вектор из 9 элементов double (MPU9250)
wx, wy, wz [deg/s]
ax, ay, az [g]
mx, my, mz [mT]
2. вектор из 3 элементов double (QMC5883)
m2x, m2y, m2z [mT]

@author: ttyUSB0
"""
import sys
sys.path.append("/home/alex/Science/magACS/Acs1D/pyRemote/")
import tlib

import time
import numpy as np

#%% Закон управления
def control(t, theta, omega):
    """ управление """
    return np.sin(2*np.pi/12*t)

#%% Основной цикл
lTime, lOmega, lTheta, lU = [], [], [], []
t0 = time.time()
theta, omega = 0., 0.
with tlib.Communicator(hostIP='89.22.167.12',
                       packetStruct='d'*13,
                       hostPort=6502,
                       bindPort=6501) as comm, tlib.Plotter() as plotter:
    while True:
        try:
            u = control(time.time()-t0, theta, omega)
            comm.control(u)
            data = comm.measure() # принимаем
            omega = data[4]
            theta = 180*np.arctan2(-data[10], -data[12])/np.pi
            lTime.append(time.time()-t0)
            lOmega.append(omega)
            lTheta.append(theta)
            lU.append(u)

            plotter.addData(time.time()-t0, (theta, omega, u))
            time.sleep(0.05)

        except KeyboardInterrupt:
                print('\n[*] Exit...')
                break # выход из цикла

#%% Графики после экспериммента
import matplotlib.pyplot as plt

plt.clf()
plt.plot(lTime, lOmega)






