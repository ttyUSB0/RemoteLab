#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
для запуска на Raspberry!

Сервер UDP для возврата измеренных данных с имитатора КА (вертушки)
слушает порт 6502
возврат данных в порт отправления

принимает double [-1..+1] - управление вентиляторами, коэфф. заполнения ШИМа

по любой посылке - возврат 13-элем. вектора
1. текущее переданное управление u
2. вектор из 9 элементов double (MPU9250)
wx, wy, wz [deg/s]
ax, ay, az [g]
mx, my, mz [mT]
3. вектор из 3 элементов double (QMC5883)
m2x, m2y, m2z [mT]

Все вектора в приборных СК, нефильтрованные, несмещённые
@author: a.t.lelekov@yandex.ru
"""
import pigpio
from mpu9250 import mpu9250
import qmc5883l as qmc
import socket
import struct
import numpy as np

import serverLib as lib

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
print('[*] QMC5883L connected..')

bind_ip = lib.getIP()
bind_port = 6502
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
server.settimeout(1.5)
print('[*] Ready to receive AckMPU on %s:%d' % (bind_ip,bind_port))

with lib.Printer() as p:
    while True:
        sendAns = False
        try:
            ack, senderAddr = server.recvfrom(64)
            #print('[*] ack from %s:%d'%(senderAddr[0], senderAddr[1]))
            fan = struct.unpack('f', ack)[0]
            if np.isnan(fan):
                fan = 0.
            sendAns = True
            p.it()

        except struct.error:
            fan = 0.
            sendAns = True
            p.asterisk()

        except socket.timeout:
            fan = 0.
            p.asterisk()

        except KeyboardInterrupt:
            print('\n[*] Exit...')
            break # выход из цикла

        pi.hardware_PWM(ccPin, freq, int(MEG*np.clip(-fan, 0., 1.)))
        pi.hardware_PWM(cwPin, freq, int(MEG*np.clip(fan, 0., 1.)))

        if sendAns: # отвечаем данными
            data = [fan]
            data.extend(imu.accel)
            data.extend(imu.gyro)
            data.extend(imu.mag)
            data.extend(compass.measure())

            # передаём в приборной СК (также см. документацию на MPU-9250, QMC)
            msg = struct.pack('13f', *data)
            server.sendto(msg, senderAddr) # на адрес отправителя

print('\n[*] Exit...')
server.close()

pi.hardware_PWM(ccPin, freq, 0) # stop fans...
pi.hardware_PWM(cwPin, freq, 0)
