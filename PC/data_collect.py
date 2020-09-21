'''
author: ahnaf tahmid chowdhury
'''

import serial                     # to get data from serial
import numpy as np                # to create array

data= serial.Serial("/dev/ttyUSB0",115200)  # I m using ubuntu. If u r using windows use COM

counts=[]
timedelta=[]
#add more empty list if have more data

while True:
    while not data.inWaiting():
        pass
    data_s=data.readline().decode('utf-8')  # data are in byte code. decode to unicode
    data_array=data_s.split(",")            # split data to ,
    counts.append(float(data_array[0]))
    timedelta.append(float(data_array[1])) 