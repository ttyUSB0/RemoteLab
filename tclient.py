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
import time
import matplotlib.pyplot as plt
import numpy as np


class Vertushka():
    """ обмен данными с вертушкой """
    pass


host = '192.168.1.150'
host = '89.22.167.12'

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#%%
bind_ip = get_ip()
bind_port = 6502

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
print('[*] Ready to receive MPU data on %s:%d' % (bind_ip,bind_port))

server.connect((get_ip(), 6505))
server.settimeout(0.5)

#%% Тесты


#%% Класс для динамического графика.
# Задержка отрисовки 70мс!

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

# plotter = PlotterObject(maxPoints=30)
# t = []
# t0 = time.time()
# for i in range(50):
#     t.append(time.time()-t0)
#     plotter.addData(t[-1], np.random.rand(3))
#     #time.sleep(0.1)

# plt.plot(np.diff(np.array(t)))

#%% Закон управления
def control(t, theta, omega):
    """ управление """
    return np.sin(t)



#%% Основной цикл
plotter = PlotterObject()
t0 = time.time()
theta_i, omega_i = 0., 0.

while True:
    u = control(time.time()-t0, theta_i, omega_i)
    msg = struct.pack('d', u)
    server.send(msg) # отправляем запрос

    try:
        msg, address = server.recvfrom(64) # принимаем
        theta_i, omega_i = struct.unpack('d'*2, msg)
        plotter.addData(time.time()-t0, (theta_i, omega_i, u))

    except socket.error:
        print('No data available', socket.error)
    except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла
    time.sleep(0.05)


#%%
server.close()






