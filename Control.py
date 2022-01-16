#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА

@author: ttyUSB0
"""
import sys
sys.path.append("/home/alex/Science/magACS/Acs1D/pyRemote/")
import clientLib as lib

import time
import numpy as np

#%% Предобработка данных
def sensor2BodyFrame(data):
    """ Перевод значений из приборной в связанную СК
    связанная СК: z по вертикали, х от RPi на зрителя, y вправо к вентилятору
    (также см. доки на clientLib.Communicator)
    """
    state = {'u':data[0],
            'a':[data[3], -data[2], data[1]],
            'w':[data[6], -data[5], data[4]],
            'mAK':[-data[9], -data[7], data[8]],
            'mQMC':[-data[12], -data[10], data[11]]}
    return state

def calcState(state):
    """ расчёт угла ориентации по магнитометру """
    state['pAK'] = np.arctan2(state['mAK'][1], state['mAK'][0])
    state['pQMC'] = np.arctan2(state['mQMC'][1], state['mQMC'][0])

    state['pos'] = state['pQMC'] #(2*state['pAK'] + state['pQMC'])/3
    state['vel'] = state['w'][1]
    return state


#%% Закон управления
def control(t):
    """ управление """
    return .1*np.sin(0.5*t - np.pi/4)

#%% Основной цикл

# '89.22.167.12'
# '192.168.1.150'
with lib.Communicator(hostIP='192.168.43.251',
                       hostPort=6505,
                       bindPort=6501) as comm, lib.Plotter() as plotter:
    t0 = time.time()
    while True:
        try:
            u = control(time.time()-t0)
            comm.control(u)
            data = comm.measure() # принимаем

            data = sensor2BodyFrame(data)
            state = calcState(data)

            plotter.addData(time.time()-t0, (state['pos'], state['vel'], u))
            if plotter.stopNow:
                break
            #time.sleep(0.05)

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла







