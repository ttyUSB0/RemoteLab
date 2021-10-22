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
import socket
import struct
import matplotlib.pyplot as plt
# import numpy as np

#%% Класс для динамического графика.
# Задержка отрисовки около 70мс!

class PlotterObject():
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
            self.axes[key].set_xlim(right=max(self.data['t']),
                                    left=min(self.data['t']))
            self.axes[key].set_ylim(top=max(self.data[key]),
                                    bottom=min(self.data[key]))

        self.figure.canvas.draw() # drawing updated values
        self.figure.canvas.flush_events()

#%%
class CommObject():
    """ обмен данными с вертушкой """
    def __init__(self, hostIP = None, packetStruct='d'*2):
        self.packetStruct = packetStruct # структура пакета
        self.hostAddr = (hostIP, 6505)
        self.bindAddr = (self.getIP(), 6502)

        if hostIP is None:
            self.hostAddr = (self.getIP(), self.hostAddr[1])

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(self.bindAddr)  # Привязка адреса и порта к сокету.
        print('[+] Ready to receive MPU data on %s:%d' %(self.bindAddr[0],
                                                         self.bindAddr[1]))
        self.server.connect(self.hostAddr)
        print('[+] Connected to %s:%d' %(self.hostAddr[0], self.hostAddr[1]))
        self.server.settimeout(0.5)

    def control(self, u):
        msg = struct.pack('d', u)
        self.server.send(msg) # отправляем запрос

    def measure(self):
        try:
            msg, _ = self.server.recvfrom(64) # принимаем
            data = struct.unpack(self.packetStruct, msg)
            return data
        except socket.error:
            print('[+] No data available', socket.error)
            return [0. for i in range(len(self.packetStruct))] #вернём нули

    def getIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
        IP = s.getsockname()[0]
        s.close()
        return IP
    def close(self):
        self.server.close()
        print('[+] server closed...')


class Communicator:
    """ обёртка для CommObject https://stackoverflow.com/a/865272/5355749 """
    def __init__(self, hostIP = None, packetStruct='d'*2):
        self.Comm = CommObject(hostIP, packetStruct)
    def __enter__(self):
        self.Comm.connect()
        return self.Comm
    def __exit__(self, exc_type, exc_value, traceback):
        self.Comm.close()


