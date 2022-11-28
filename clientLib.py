#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Библиотека, содежит классы:
    Plotter - создаёт график, динамически обновляет, добавляя данные
    Communicator - организует связь с имитатором, 1 сокет

@author: ttyUSB0
"""
import socket
import struct
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

clip = lambda n, minn, maxn: max(min(maxn, n), minn) # https://stackoverflow.com/a/5996949/5355749

#%% Класс для динамического графика.
# Задержка отрисовки около 70мс!
class Plotter():
    def __init__(self, figNum=None, maxPoints=300, figSize=(6,6),
                 noStopButton=False):
        if figNum is None:
            self.figure, axes = plt.subplots(3, 1, figsize=figSize)
            self.figNum = plt.gcf().number
        else:
            self.figure = plt.figure(num=figNum, clear=True)
            axes = self.figure.subplots(3, 1)
            self.figNum = figNum
        #self.figure.tight_layout()

        # init data, add empty lines with colors
        self.lines = {}
        self.axes = {}
        self.data = {'t':[0., 0.]} # добавляем два пустых отсчёта (c NaN), для замеров dt
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        self.keys = ['t', 'theta', 'omega', 'u']
        dimension = ['s', 'deg', 'deg/s', '-1..1']
        for (key, ax, c, dim) in zip(self.keys[1:], axes, colors, dimension[1:]):
            self.axes[key] = ax
            ax.grid(b=True) # сетку на всех осях
            self.data[key] = [np.nan, np.nan]
            self.lines[key], = self.axes[key].plot(self.data['t'],
                                                  self.data[key],
                                                  color=c) # и пустую линию
            self.axes[key].set_ylabel(key+' ['+dim+']') # обозначения на осях
        self.axes['theta'].set_title('dt = %5.2f ms'%(0.,))
        self.maxPoints = maxPoints

        self.stopNow = False
        if not noStopButton:
            self.axButton = plt.axes([0.7, 0.895, 0.2, 0.05])
            self.button = Button(self.axButton, 'Stop') # Создание кнопки
            self.button.on_clicked(self.onButtonClicked)

    def onButtonClicked(self, event):
        """ обработчик нажатия на СТОП """
        self.stopNow = True

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
            top = np.nanmax(self.data[key])
            if np.isnan(top):
                top = 1
            bottom = np.nanmin(self.data[key])
            if np.isnan(bottom):
                bottom = 0
            if top==bottom:
                top = top*1.02
                bottom = bottom*0.98
            self.axes[key].set_ylim(top=top, bottom=bottom)

        self.axes['theta'].set_title('dt = %5.2f ms'%(1000*np.mean(np.diff(self.data['t'])),)) #(self.data['t'][-1]-self.data['t'][-2])
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
                 hostPort=6505, bindPort=6502):
        self.packetStruct = '13f' # структура пакета
        self.hostAddr = (hostIP, hostPort)
        self.bindAddr = (getIP(), bindPort)

        if hostIP is None:
            self.hostAddr = (getIP(), self.hostAddr[1])
        self.dataNaN = [np.NaN for i in range(13)] #вернём в случае пропуска

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(self.bindAddr)  # Привязка адреса и порта к сокету.
        print('[+] Ready to receive MPU data on %s:%d' %(self.bindAddr[0],
                                                         self.bindAddr[1]))
        self.server.connect(self.hostAddr)
        print('[+] Connected to %s:%d' %(self.hostAddr[0], self.hostAddr[1]))
        self.server.settimeout(0.25)

    def control(self, u):
        msg = struct.pack('f', u)
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
