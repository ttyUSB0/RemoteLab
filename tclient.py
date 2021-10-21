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


bind_ip = get_ip()
bind_port = 6502

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  # Привязка адреса и порта к сокету.
print('[*] Ready to receive MPU data on %s:%d' % (bind_ip,bind_port))

server.connect((host, bind_port))
server.settimeout(0.1)

#%%

# отправляем запрос , (address[0], 6501)
server.send(b'!') # неважно что будем отправлять

try:
    msg, address = server.recvfrom(255) # принимаем
    print(address)
    print(msg.decode("utf-8"))
except socket.error:
    print('No data available', socket.error)



#%%
server.close()




