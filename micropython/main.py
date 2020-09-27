import Geiger
import Buzzer
from utime import *
from umqtt.robust import MQTTClient
from wlan_connect import auto_connect

auto_connect()

SERVER = "192.168.1.100"        #IP or DNS record

mqtt = MQTTClient("GM",SERVER)
mqtt.connect()

Geiger.pwm_400v()
Geiger.discharge()

last_tick = ticks_ms()
current_tick = ticks_ms()
CPM = []
count = 0

while True:
    # check if a new event happened
    if Geiger.count > count:
        count = Geiger.count
        current_tick = ticks_ms()
        delta_t = ticks_diff(current_tick, last_tick)
        last_tick = current_tick

        if delta_t < 120000:
            CPM.append(delta_t)
            while sum(CPM) > 60000:
                CPM.pop(0)
        
        Buzzer.buzzer()
        d1=str(len(CPM))
        d2=str(delta_t)
        data = d1+","+d2+","+str(time())
        print(data)
        mqtt.publish("CPM", d1)
        mqtt.publish("delta_t",d2)
