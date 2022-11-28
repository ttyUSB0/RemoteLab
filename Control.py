#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDP client for data exchange with the spacecraft simulator testbed
@author: ttyUSB0, a.t.lelekov@yandex.ru
"""
import sys
sys.path.append("/home/alex/Science/magACS/Acs1D/pyRemote/")
# ^^^ change to your path to clientLib.py
import clientLib as lib
import time
import numpy as np

#%% Data preprocessing
def sensor2BodyFrame(data):
    """ Translate sensor data from the instrument to body coordinate system
     body SC (right-handed): z vertical, x from RPi to viewer, y to right fan
     (also see the docs in clientLib.Communicator)
     """
    state = {'u':data[0],            'a':[data[3], -data[2], data[1]],
            'w':[data[6], -data[5], data[4]],
            'mAK':[-data[9], -data[7], data[8]],
            'mQMC':[-data[12], -data[10], data[11]]}
    return state


def calcState(state):
    """ state calculation:
        - angle from QMC magnetometer,
        - angular velocity from gyroscope """
    state['pos'] = np.arctan2(state['mQMC'][1], state['mQMC'][0])*180/np.pi
    state['vel'] = state['w'][2]
    return state

#%% Control law
def control(t, w, B):
    return 0

#%% main loop
# initialize state
state = sensor2BodyFrame(np.zeros(13))
state = calcState(state)

with lib.Communicator(hostIP='192.168.43.139', # 188.162.92.109
                       hostPort=6502) as comm, lib.Plotter() as plotter:
    t0 = time.time()
    while True:
        try:
            # calculate control
            ti = time.time()-t0

            u = control(ti, state['vel'], state['mQMC'])
            comm.control(u) # send it to testbed

            data = comm.measure() # receive answer
            data = sensor2BodyFrame(data) # translate it to body CS
            state = calcState(data) # state calculation

            plotter.addData(ti, (state['pos'], state['vel'], u))
            if plotter.stopNow:
                break
            #time.sleep(0.05)

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # exit from loop, Ctrl+C

