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

#%% Предобработка данных
def sensor2BodyFrame(data):
    """ Перевод значений из приборной в связанную СК
    связанная СК: z по вертикали, х от RPi на зрителя, y вправо к вентилятору
    """
    state = {'u':data[0],
            'a':[data[3], -data[2], data[1]],
            'w':[data[6], -data[5], data[4]],
            'mAK':[-data[9], -data[7], data[8]],
            'mQMC':[-data[12], -data[10], data[11]]}
    return state

def calcState(state):
    """ расчёт угла ориентации по магнитометру, с g-h фильтром """
    state['pAK'] = np.arctan2(state['mAK'][1]+16., state['mAK'][0]-10.)
    state['pQMC'] = np.arctan2(state['mQMC'][1]+14., state['mQMC'][0]+12.)

    state['pos'] = state['pAK'] #(2*state['pAK'] + state['pQMC'])/3
    state['vel'] = state['w'][1]
    return state


#%% Закон управления
def control(t):
    """ управление """
    return np.sin(0.5*t - np.pi/4)

#%% Основной цикл

# '89.22.167.12'
# '192.168.1.150'
with tlib.Communicator(hostIP='89.22.167.12',
                       packetStruct='d'*12,
                       hostPort=6502,
                       bindPort=6501) as comm, tlib.Plotter() as plotter:
    t0 = time.time()
    while True:
        try:
            u = control(time.time()-t0)
            comm.control(u)
            data = comm.measure() # принимаем

            data = sensor2BodyFrame(data)
            state = calcState(data)

            plotter.addData(time.time()-t0, (state['pos'], state['vel'], u))
            time.sleep(0.05)

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла
    data = comm.getData()






