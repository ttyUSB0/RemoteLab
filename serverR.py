#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
для запуска на Raspberry!

Сервер UDP для возврата измеренных данных с имитатора КА (вертушки)
слушает порт 6502
возврат данных в порт отправления

принимает double [-1..+1] - управление вентиляторами, коэфф. заполнения ШИМа

по любой посылке - возврат 12-элем. вектора
1. вектор из 9 элементов double (MPU9250)
wx, wy, wz [deg/s]
ax, ay, az [g]
mx, my, mz [mT]
2. вектор из 3 элементов double (QMC5883)
m2x, m2y, m2z [mT]

Все вектора в приборных СК, нефильтрованные, несмещённые
TODO: переделать библиотеки в pigpio...
@author: a.t.lelekov@yandex.ru
"""
import pigpio
from mpu9250 import mpu9250
import qmc5883l as qmc
import socket
import struct
import sys
import numpy as np

#%% Функции и классы - служебные
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

def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
    IP = s.getsockname()[0]
    s.close()
    return IP

#%% Основной код

# Номера пинов для вентиляторов (Broadcom)
# https://pinout.xyz/#s
cwPin = 13  # по часовой
ccPin = 12 # против часовой

freq = 1000 # частота, Hz
MEG = 1000000 # 1M, for duty cycle

pi = pigpio.pi() # pi accesses the local Pi's GPIO
if not pi.connected:
    print('[*] can\'t connect with pigpio..')
    exit()
pi.hardware_PWM(ccPin, freq, 0) # stop fans...
pi.hardware_PWM(cwPin, freq, 0)

print('[*] pigpio connected, starting udp server..')

imu = mpu9250()
compass = qmc.QMC5883L()

bind_ip = getIP()
bind_port = 6502
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
server.settimeout(1.5)
print('[*] Ready to receive AckMPU on %s:%d' % (bind_ip,bind_port))

with Printer() as p:
    while True:
        sendAns = False
        try:
            ack, senderAddr = server.recvfrom(64)
            #print('[*] ack from %s:%d'%(senderAddr[0], senderAddr[1]))
            fan = struct.unpack('d', ack)
            sendAns = True
            p.it()

        except (socket.timeout, struct.error):
            fan = [0]
            p.asterisk()

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла

        pi.hardware_PWM(ccPin, freq, int(MEG*np.clip(-fan[0], 0., 1.))) # stop fans...
        pi.hardware_PWM(cwPin, freq, int(MEG*np.clip(fan[0], 0., 1.)))

        if sendAns: # отвечаем данными MPU
            data = []
            data.extend(imu.accel)
            data.extend(imu.gyro)
            data.extend(imu.mag)
            data.extend(compass.measure())

            # передаём в приборной СК (см. документацию на MPU-9250, QMC)
            msg = struct.pack('12d', *data)
            server.sendto(msg, senderAddr) # на адрес отправителя

print('\n[*] Exit...')
server.close()

pi.hardware_PWM(ccPin, freq, 0) # stop fans...
pi.hardware_PWM(cwPin, freq, 0)
