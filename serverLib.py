#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Библиотека. Работает только внутри, интерфейс loopback
Параметры:
  номер порта для ответа (по умолчанию порт 7201)
  номер порта, на котором будет слушать (по умолчанию порт 7200)

+ getIP
@author: ttyUSB0
"""
import socket
import struct

#%%
class Communicator():
    def __init__(self, runLocally=True, bindPort=7200, SiTport=7201,
                 packetIn='', packetOut=''):
        """
        bindPort - на котором слушаем
        SiTport - на котором настроен приёмник в SimInTech
        """
        print('[*] Starting TLE server')
        if runLocally:
            bindIP = "127.0.0.1"  # Standard loopback interface address (localhost)
        else:
            bindIP = self.getIP()
        self.bindAddr = (bindIP, bindPort)
        self.SiTport = SiTport
        self.packetIn = packetIn
        self.packetOut = packetOut
        self.clientAddr = (bindIP, 7201)

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(self.bindAddr)  # Привязка адреса и порта к сокету.
        self.server.settimeout(5.0)
        print('[+] Server binded on %s:%d' %(self.bindAddr[0], self.bindAddr[1]))


    def close(self):
        self.server.close()
        print('[+] server closed...')

    def __enter__(self):
        self.connect()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def getIP(self):
        """ Получить IP машины, на которой запущен """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.168.1.1', 1)) # doesn't even have to be reachable
        IP = s.getsockname()[0]
        s.close()
        return IP

    def receive(self):
        """ получение запроса """
        try:
            msg, self.clientAddr = self.server.recvfrom(256) # принимаем
            data = struct.unpack(self.packetIn, msg)
            return data
        except (socket.error, socket.timeout, struct.error) as Err:
            print('[+] No data available:', Err)
            return [None]

    def send(self, data):
        """ отправка """
        msg = struct.pack(self.packetOut, *data)
        self.server.sendto(msg, (self.clientAddr[0], self.SiTport)) # отправляем запрос



# Проверка обмена в файле "Обмен UDP тест.prt"
if __name__ == "__main__":
    with Communicator(bindPort=7200, SiTport=7201,
                      packetIn='ff', packetOut='f') as comm:
        while True:
            try:
                data = comm.receive()
                if not(data[0] is None):
                    print(data)
                    comm.send(data)

            except KeyboardInterrupt:
                print('\n[*] Exit...')
                break # выход из цикла



