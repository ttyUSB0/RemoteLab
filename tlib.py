#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Библиотека, содежит:
    Plotter - создаёт график, динамически обновляет, добавляя данные
    Communicator - организует связь с имитатором, 1 сокет
    Printer - для печати вращающейся палочки, индикатор активности

@author: alex
"""
import socket
import struct
import sys
import matplotlib.pyplot as plt
import numpy as np


#%% Класс для динамического графика.
# Задержка отрисовки около 70мс!
class Plotter():
    def __init__(self, figNum=None, maxPoints=300):
        if figNum is None:
            self.figure, axes = plt.subplots(3, 1, figsize=(6, 6))
            self.figNum = plt.gcf().number
        else:
            self.figure = plt.figure(num=figNum, clear=True)
            axes = self.figure.subplots(3, 1)
            self.figNum = figNum
        #self.figure.tight_layout()

        # init data, add empty lines with colors
        self.lines = {}
        self.axes = {}
        self.data = {'t':[]}
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        self.keys = ['t', 'theta', 'omega', 'u']
        dimension = ['s', 'rad', 'rad/s', '-1..1']
        for (key, ax, c, dim) in zip(self.keys[1:], axes, colors, dimension[1:]):
            self.axes[key] = ax
            ax.grid(b=True) # сетку на всех осях
            self.data[key] = []
            self.lines[key], = self.axes[key].plot(self.data['t'],
                                                  self.data[key],
                                                  color=c) # и пустую линию
            self.axes[key].set_ylabel(key+' ['+dim+']') # обозначения на осях

        self.maxPoints = maxPoints

    def addData(self, t, ThetaOmegaU):
        ttwu = [t]
        ttwu.extend(ThetaOmegaU)
        for (key, d) in zip(self.keys, ttwu):
            self.data[key].append(d)
            if len(self.data[key])>self.maxPoints: # cut len to maxPoints
                self.data[key] = self.data[key][1:]

        for key in self.keys[1:]: # updating data values
            self.lines[key].set_xdata(self.data['t'])
            self.lines[key].set_ydata(self.data[key])
            self.axes[key].set_xlim(right=self.data['t'][-1],
                                    left=self.data['t'][0])

            self.axes[key].set_ylim(top=np.nanmax(self.data[key]),
                                    bottom=np.nanmin(self.data[key]))

        self.figure.canvas.draw() # drawing updated values
        self.figure.canvas.flush_events()

    def getData(self):
        return self.data

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        plt.close(self.figNum)


#%% Коммуникатор
def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
    IP = s.getsockname()[0]
    s.close()
    return IP

class Communicator():
    """ обмен данными с имитатором вертушки, 1 сокет"""
    def __init__(self, hostIP = None,
                 packetStruct='d'*2,
                 hostPort=6505, bindPort=6502):
        self.packetStruct = packetStruct # структура пакета
        self.hostAddr = (hostIP, hostPort)
        self.bindAddr = (getIP(), bindPort)

        if hostIP is None:
            self.hostAddr = (getIP(), self.hostAddr[1])
        self.dataNaN = [np.NaN for i in range(len(self.packetStruct))] #вернём в случае пропуска

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(self.bindAddr)  # Привязка адреса и порта к сокету.
        print('[+] Ready to receive MPU data on %s:%d' %(self.bindAddr[0],
                                                         self.bindAddr[1]))
        self.server.connect(self.hostAddr)
        print('[+] Connected to %s:%d' %(self.hostAddr[0], self.hostAddr[1]))
        self.server.settimeout(0.25)

    def control(self, u):
        msg = struct.pack('d', u)
        self.server.send(msg) # отправляем запрос

    def measure(self):
        try:
            msg, _ = self.server.recvfrom(256) # принимаем
            data = struct.unpack(self.packetStruct, msg)
            return data
        except (socket.error, socket.timeout, struct.error):
            print('[+] No data available', socket.error)
            return self.dataNaN

    def ctrlAndMeas(self, u):
        self.control(u)
        return self.measure()

    def close(self):
        self.server.close()
        print('[+] server closed...')

    def __enter__(self):
        self.connect()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


#%% Принтер
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