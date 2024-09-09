#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА
@author: ttyUSB0
"""
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
    """ расчёт угла ориентации по магнитометру QMC"""
    state['pos'] = np.arctan2(state['mQMC'][1], state['mQMC'][0])*180/np.pi
    state['vel'] = state['w'][2]
    return state

#%% Закон управления Zero
def control(t, w, phi):
    """ управление """
    return 0

#%%
def control(t, w, phi):
    """ управление """
    if t<5:
        return 1
    elif t<10:
        return -1
    else:
        return 0

#%% Закон управления Relay
def control(t, w, phi):
    """ управление """
    err = 0 - w
    if err>3:
        u = 0.05
    elif err<-3:
        u = -0.05
    else:
        u = 0
    return u


#%% Закон управления w
def control(t, w, phi):
    """ управление """
    err = -10 - w
    u = .1*err
    return u


#%% Phi
def control(t, w, phi):
    """ управление """
    errPhi = 0 - phi
    uPhi = 0.1*errPhi

    errW = uPhi - w
    u = .1*errW
    return u

#%% Основной цикл
state = {'vel':0, 'pos':0}
with lib.Communicator(hostIP='192.168.0.11',
              hostPort=6502) as comm, lib.Plotter() as plotter:
    t0 = time.time()
    while True:
        try:
            u = control(time.time()-t0, state['vel'], state['pos']) # расчёт управления
            comm.control(u) # отправляем его в НОК
            data = comm.measure() # принимаем ответ

            data = sensor2BodyFrame(data) # переводим из ПСК в СвСК
            state = calcState(data) # рассчитываем состояние

            plotter.addData(time.time()-t0, (state['pos'], state['vel'], u))
            if plotter.stopNow:
                break
            #time.sleep(0.05)

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла


