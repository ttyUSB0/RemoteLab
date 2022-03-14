#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент UDP для обмена данными с имитатором КА
@author: ttyUSB0
"""
import sys
sys.path.append("/home/alex/Science/magACS/Acs1D/pyRemote/")
# ^^^ заменить на свой путь к clientLib.py
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
    """ расчёт состояния:
        - угол по магнитометру QMC,
        - скорость по гироскопу """
    state['pos'] = np.arctan2(state['mQMC'][1], state['mQMC'][0])*180/np.pi
    state['vel'] = state['w'][2]
    return state

#%% Закон управления
def control(t, w, phi):
    """ управление релейное """
    err = 0 - w
    treshold = 1
    if err > treshold:
        u = 0.9
    elif err < -treshold:
        u = -0.9
    else:
        u = 0
    return u

#%% Основной цикл
state = {'vel':0, 'pos':0}
with lib.Communicator(hostIP='192.168.1.150',# 89.22.167.12
                       hostPort=6502,
                       bindPort=6501) as comm, lib.Plotter() as plotter:
    t0 = time.time()
    while True:

        try:
            # расчёт управления
            u = control(time.time()-t0, state['vel'], state['pos'])
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


