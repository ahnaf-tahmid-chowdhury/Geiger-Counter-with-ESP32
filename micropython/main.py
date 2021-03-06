from geiger import GMtube,Buzzer
from utime import *
from umqtt.robust import MQTTClient
from wlan_connect import auto_connect
from hcsr04 import HCSR04
import uasyncio
import esp32

SERVER = "192.168.1.105"  #IP or DNS record
mqtt = MQTTClient("GM",SERVER)
auto_connect()
try:
    mqtt.connect()
    print("mqtt success")
except:
    print("mqtt faild")



g=GMtube(12,10000,675,15)
usonic=HCSR04(trigger_pin=19,echo_pin=18)

last_tick = ticks_ms()
current_tick = ticks_ms()
CPM = []
event = 0
delta_t= 0
d1= 0

async def geiger_count():
    global event, last_tick, current_tick, CPM, delta_t, d1
    while True:
        # check if a new event happened
        if g.count > event:
            event = g.count
            current_tick = ticks_ms()
            delta_t = ticks_diff(current_tick, last_tick)
            last_tick = current_tick
            
            if delta_t < 120000:
                CPM.append(delta_t)
                while sum(CPM) > 60000:
                    CPM.pop(0)
            d1=d1+1
            Buzzer()
            await uasyncio.sleep(0.00019) #dead time of GM tube

async def data_pass():
    while True:
        
        d2=(len(CPM))
        if d2 < 200:
            d2=int(d2/2)
        d3=str(d2*0.0057)
        d4=str(delta_t)
        d5=str(usonic.distance_cm())
        d6=str((esp32.raw_temperature()-32)*5/9)
        data=str(d1)+","+str(d2)+","+d3+","+d4+","+d5+","+d6
        print(data)
        
        try:
            mqtt.publish("total", d1)
            mqtt.publish("cpm", d2)
            mqtt.publish("uSv", d3)
            mqtt.publish("delta_t",d4)
            mqtt.publish("distance",d5)
            mqtt.publish("temperature",d6)
        except:
            pass
        if d2 < 400:
            await uasyncio.sleep_ms(100)
        elif d2 < 700:
            await uasyncio.sleep_ms(500)
        elif d2 < 1500:
            await uasyncio.sleep_ms(800)
        else:
            await uasyncio.sleep_ms(1000)
              
event_loop = uasyncio.get_event_loop()
event_loop.create_task(geiger_count())
event_loop.create_task(data_pass())
event_loop.run_forever()

