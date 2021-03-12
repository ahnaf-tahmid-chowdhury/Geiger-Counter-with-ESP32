import esp32
from utime import *
from geiger import GMtube,Buzzer
from umqtt.robust import MQTTClient
import urequests
from hcsr04 import HCSR04
import uasyncio
from machine import Pin,PWM
import Connect

mqtt_local = MQTTClient(config["clientID"], config["local_server"], port=1883)
mqtt_cloud = MQTTClient(config["clientID"], config["ubidots"],port= 1883, user = config["ubidots_key"], password = "None")

Connect.do_connect()

try:
    mqtt_local.connect()
    print("mqtt local success")
except:
    print("mqtt local faild")

try:
    mqtt_cloud.connect()
    print("mqtt cloud success")
except:
    print("mqtt cloud faild")

g=GMtube(12,10000,675,15)
usonic=HCSR04(trigger_pin=19,echo_pin=18)

last_tick = ticks_ms()
current_tick = ticks_ms()
CPM = []
event = 0
delta_t= 0
d1= 0
d2=0
d3=0
d4=0
d5=0
d6=0

def onMessage(topic, msg):
    m=loads(msg)
    print(m["value"])
    if m["value"] == 1.0:
        usonic=HCSR04(trigger_pin=19,echo_pin=18)
        print("works")
    elif m["value"] == 0.0:
        trigger = Pin(19,Pin.OUT).off()
        echo = Pin(18,Pin.IN).off()
        
mqtt_local.set_callback(onMessage)
mqtt_cloud.set_callback(onMessage)

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
    global d2, d3, d4, d5, d6
    while True:
        d2=(len(CPM))
        if d2 < 200:
            d2=int(d2/2)
        d3=d2*0.0057
        d4=delta_t
        print(d4)
        d5=usonic.distance_cm()
        d6=(esp32.raw_temperature()-32)*5/9
        
        if config["local"] == "1":
            
            try:
                mqtt_local.publish(b"total-counts",str(d1))
                mqtt_local.publish(b"cpm",str(d2))
                mqtt_local.publish(b"usv",str(d3))
                mqtt_local.publish(b"delta-t",str(d4))
                mqtt_local.publish(b"distance",str(d5))
                mqtt_local.publish(b"temperature",str(d6))
            except:
                print("local publish failed")
  
        if d2 < 400:
            await uasyncio.sleep_ms(100)
        elif d2 < 700:
            await uasyncio.sleep_ms(500)
        elif d2 < 1500:
            await uasyncio.sleep_ms(800)
        elif d2 < 2500:
            await uasyncio.sleep_ms(1000)
        else:
            await uasyncio.sleep_ms(2000)



async def cloud_publish():
    while True:
        if config["cloud"] == "1" :
            try:
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/total-counts", dumps(d1), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/cpm", dumps(d2), qos=0,retain=False)
                #added usv as a mathematical formula at ubidots
                #mqtt_cloud.publish("/v1.6/devices/smartgeiger/usv", dumps(d3), qos=0,retain=False) 
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/delta-t",dumps(d4), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/temperature",dumps(d6), qos=0,retain=False)
            except:
                print("cloud publish faild")        
        await uasyncio.sleep(10)


async def cloud_subscribe():
    
    while True:
        if config["cloud"] == "1" and d2 < 500:
            try:
                mqtt_cloud.subscribe("/v1.6/devices/smartgeiger/hc-sr04")
                mqtt_cloud.check_msg()
            except:
                print("cloud subscribe faild")
        await uasyncio.sleep(60)


async def ifttt():

    while True:
        if d2 > 100 and config["msg alert"] == "1":
            try:
                readings = {'value1':d1, 'value2':d2, 'value3':d3}
                print(readings)
            
                request_headers = {'Content-Type': 'application/json'}

                request = urequests.post(
                    'http://maker.ifttt.com/trigger/SmartGeiger/with/key/' + config["ifttt_key"],
                    json=readings,
                    headers=request_headers)
                request.close()
                await uasyncio.sleep(180)
            except OSError as e:
                print('Failed to read/publish readings.')
                await uasyncio.sleep(10)
        elif d2>200:
            await uasyncio.sleep(120)
        else:
            await uasyncio.sleep(10)
            
event_loop = uasyncio.get_event_loop()
event_loop.create_task(geiger_count())
event_loop.create_task(data_pass())
event_loop.create_task(cloud_publish())
event_loop.create_task(cloud_subscribe())
event_loop.create_task(ifttt())
event_loop.run_forever()

