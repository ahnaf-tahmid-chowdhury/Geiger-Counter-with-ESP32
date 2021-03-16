import esp32
import machine
from utime import *
from geiger import GMtube,Buzzer
from umqtt.robust import MQTTClient
import urequests
from json import loads, dumps
from hcsr04 import HCSR04
import uasyncio
import network
import webrepl

f = open('config.json', 'r')
config = loads(f.read())
f.close()

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print('connecting to network...')
    
    wlan.connect(config['essid'], config['password'])
    sleep(4) # wait 4 sec to connect
    if not wlan.isconnected():
        wlan.active(False)
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid = "SmartGeiger",password = "SmartGeiger") # set the ESSID of the access point with password
        while not ap.active():
            webrepl.start()


mqtt_local = MQTTClient(config["clientID"], config["local_server"], port=1883)
mqtt_cloud = MQTTClient(config["clientID"], config["ubidots"],port= 1883, user = config["ubidots_key"], password = "None")

do_connect()

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
auto = 160000000

def onMessage_cloud(topic, msg):
    m=loads(msg)
    print(m["value"])
    if m["value"] == 1.0:
        config["buzzer"] = "true"
    elif m["value"] == 0.0:
        config["buzzer"] = "false"

def onMessage_local(topic, msg):
    m=loads(msg)
    print(m)
    config["config_sync"] = m["config_sync"]
    config["time_interval"] = m["time_interval"]*60
    config["local"] = m["local"]
    config["cloud"] = m["cloud"]
    config["buzzer"] = m["buzzer"]
    config["msg_alert"] = m["msg_alert"]
    config["powersave"] = m["powersave"]
    config["auto_freq"] = m["auto_freq"]
    config["max_freq"] = m["max_freq"]
    

mqtt_local.set_callback(onMessage_local)
mqtt_cloud.set_callback(onMessage_cloud)
mqtt_local.subscribe("smartgiger",qos=0)

try:
    mqtt_local.wait_msg()
except:
    print("local subscribe faild")

timer = ticks_ms()


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

            if config["buzzer"] == "true":
                Buzzer().buzzer()
            else:
                Buzzer().off()

            await uasyncio.sleep(0.00019) #dead time of GM tube

async def machine_freq():
    global freq
    while True:
        if config["powersave"] == "true":
            machine.freq(80000000)
        if config["auto_freq"] == "true":
            machine.freq(auto)
        if config["max_freq"] == "true":
            machine.freq(240000000)
        await uasyncio.sleep_ms(500)

async def data_pass():
    global d2, d3, d4, d5, d6, auto
    while True:
        d2=(len(CPM))
        if d2 < 200:
            d2=int(d2/2)
        d3 = d2*0.0057
        time = ticks_diff(ticks_ms(),timer)/1000
        avg = d1/time
        std = (d1**0.5)/time
        d4 = str(avg)+ " +/- " +str(std)
        d5 = delta_t
        d6 = usonic.distance_cm()
        d7 = (esp32.raw_temperature()-32)*5/9
        
        if config["local"] == "true":
            
            try:
                mqtt_local.publish(b"time",str(time))
                mqtt_local.publish(b"total-counts",str(d1))
                mqtt_local.publish(b"cpm",str(d2))
                mqtt_local.publish(b"usv",str(d3))
                mqtt_local.publish(b"counting-rate",d4)
                mqtt_local.publish(b"delta-t",str(d5))
                mqtt_local.publish(b"distance",str(d6))
                mqtt_local.publish(b"temperature",str(d7))
                mqtt_local.publish(b"freq",str(int(machine.freq()/1000000)))
            except:
                print("local publish failed")
  
        if d2 < 400:
            await uasyncio.sleep_ms(200)
        elif d2 < 700:
            auto = 160000000
            await uasyncio.sleep_ms(500)
        elif d2 < 1500:
            auto = 240000000
            await uasyncio.sleep_ms(800)
        elif d2 < 2500:
            await uasyncio.sleep_ms(1000)
        else:
            await uasyncio.sleep_ms(2000)



async def cloud_publish():
    while True:
        if config["cloud"] == "true" :
            try:
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/total-counts", dumps(d1), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/cpm", dumps(d2), qos=0,retain=False)
                #added usv as a mathematical formula at ubidots
                #mqtt_cloud.publish("/v1.6/devices/smartgeiger/usv", dumps(d3), qos=0,retain=False) 
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/delta-t",dumps(d5), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/temperature",dumps(d7), qos=0,retain=False)
            except:
                print("cloud publish faild")        
        await uasyncio.sleep(config["time_interval"])
        
async def local_subscribe():
    global config
    while True:
        if config["config_sync"] == "true":            
            try:
                mqtt_local.check_msg()
            except:
                print("local subscribe faild")             
        f = open('config.json', 'w')
        f.write(dumps(config))
        f.close()
        await uasyncio.sleep(config["time_interval"])
        


async def cloud_subscribe():
    global config
    while True:
        if config["cloud"] == "true":
            try:
                mqtt_cloud.subscribe("/v1.6/devices/smartgeiger/buzzer")
                mqtt_cloud.check_msg()
            except:
                print("cloud subscribe faild")
        await uasyncio.sleep(config["time_interval"])


async def ifttt():

    while True:
        if d2 > 100 and config["msg_alert"] == "true":
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
event_loop.create_task(local_subscribe())
event_loop.create_task(cloud_subscribe())
event_loop.create_task(machine_freq())
event_loop.create_task(ifttt())

event_loop.run_forever()
