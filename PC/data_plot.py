'''
author: ahnaf tahmid
'''

import serial
import numpy as np
import matplotlib.pyplot as plt
from drawnow import *

plt.ion()
data= serial.Serial("/dev/ttyUSB0",115200)
d1=[]
d2=[]
c=0

def Fig():
    plt.ylim(100,200)
    plt.plot(d1,"--",label="Degree F")
    plt.grid(True)
    plt.title("Live data")
    plt.ylabel("counts")
    plt.legend(loc="upper left")
    plt2=plt.twinx()
    plt.ylim(50,700)
    plt2.plot(d2,"r-",label="time delta")
    plt2.set_ylabel("Touch")
    plt2.legend(loc="upper right")


while True:
    while not data.inWaiting():
        pass
    data_s=data.readline().decode('utf-8')
    data_array=data_s.split(",")
    d1.append(float(data_array[0]))
    d2.append(float(data_array[1]))
    drawnow(Fig)
    c+=1
    if c>50:
        d1.pop(0)
        d2.pop(0)