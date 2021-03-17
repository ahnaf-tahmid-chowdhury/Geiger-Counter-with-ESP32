import esp32
from machine import freq
from utime import *
from geiger import GMtube,Buzzer,BiColorLED
from umqtt.robust import MQTTClient
import urequests
from machine import PWM
from json import loads, dumps
from hcsr04 import HCSR04
import uasyncio
import network
import webrepl

led=BiColorLED(red=22,green=23,rduty=0,gduty=1023)
f = open('config.json', 'r')
config = loads(f.read())
f.close()


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    led.color(r=700,g=1023)
    wlan.active(True)
    print('connecting to network...')
    wlan.connect(config['essid'], config['password'])
    sleep(4) # wait 5 sec to connect
    if not wlan.isconnected():
        wlan.active(False)
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid = config["clientID"],password = config["clientID"]) # set the ESSID of the access point with password
        while not ap.active():
            webrepl.start()
            led.color(r=400,g=700)
            pass
    led.color(r=0,g=1023)
    print('network config:', wlan.ifconfig())
mqtt_local = MQTTClient(config["clientID"], config["local_server"], port=1883)
mqtt_cloud = MQTTClient(config["clientID"], config["ubidots"],port= 1883, user = config["ubidots_key"], password = "None")

do_connect()

try:
    mqtt_local.connect()
    print("mqtt local success")
except:
    print("mqtt local faild")
    led.color(r=1023,g=0)
try:
    mqtt_cloud.connect()
    print("mqtt cloud success")
except:
    print("mqtt cloud faild")
    led.color(r=1023,g=100)

g=GMtube(12,100000,675,15)
usonic=HCSR04(trigger_pin=19,echo_pin=18)

last_tick = ticks_ms()
current_tick = ticks_ms()
CPM = []
event = 0
delta_t= 0
d1= 0
d2= 0
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

try:
    mqtt_local.subscribe("smartgiger",qos=0)
    print("waiting for msg...")
    led.color(500, 700)
    mqtt_local.wait_msg()
    
except:
    print("local subscribe faild")
    led.color(r=1023,g=0)
timer = ticks_ms()


async def geiger_count():
    global event, last_tick, current_tick, CPM, delta_t, d1
    while True:
        # check if a new event happened
        if g.count > event:

            led.color(1023, 0) if d2>200 else led.color(1023, 200) if d2>100 else led.color(1023,1023) if d2>70 else led.color(500, 950) if d2>40 else led.color(200, 1023) if d2>25 else led.color(0, 1023)
            
            event = g.count
            current_tick = ticks_ms()
            delta_t = ticks_diff(current_tick, last_tick)
            last_tick = current_tick
            d1=d1+1

            if delta_t < 120000:
                CPM.append(delta_t)
                while sum(CPM) > 60000:
                    CPM.pop(0)
            
            Buzzer().buzzer() if config["buzzer"] == "true" else Buzzer().off()
            led.off()

            await uasyncio.sleep(0.00019) #dead time of GM tube


async def machine_freq():
    global freq, d2, t
    while True:
        led.color(400, 500)
        t=ticks_ms()
        if config["powersave"] == "true":
            freq(80000000)
        if config["auto_freq"] == "true":
            freq(auto)
        if config["max_freq"] == "true":
            freq(240000000)
        d2=int(d2+(d2*(ticks_ms()-t)/60000))
        led.off()
        await uasyncio.sleep_ms(500)


async def data_pass():
    global d2, d3, d4, d5, d6, auto, t
    while True:
        t=ticks_us()
        d2= int(len(CPM)/2)
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
                mqtt_local.publish(b"freq",str(int(freq()/1000000)))
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
    global d2, t
    while True:
        if config["cloud"] == "true" :
            t=ticks_ms()
            try:
                led.color(700, 700)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/total-counts", dumps(d1), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/cpm", dumps(d2), qos=0,retain=False)
                #added usv as a mathematical formula at ubidots
                #mqtt_cloud.publish("/v1.6/devices/smartgeiger/usv", dumps(d3), qos=0,retain=False) 
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/delta-t",dumps(d5), qos=0,retain=False)
                mqtt_cloud.publish("/v1.6/devices/smartgeiger/temperature",dumps(d7), qos=0,retain=False)
                led.off()
            except:
                print("cloud publish faild")    
            d2=int(d2+(d2*(ticks_ms()-t)/60000))
            
        await uasyncio.sleep(config["time_interval"])
        

async def local_subscribe():
    global config, d2, t
    while True:
        if config["config_sync"] == "true" and config["local"] == "true":
            t=ticks_ms()
            try:
                led.color(700, 700)
                mqtt_local.check_msg()
                led.off()
            except:
                print("local subscribe faild")             
            f = open('config.json', 'w')
            f.write(dumps(config))
            f.close()
            d2=int(d2+(d2*(ticks_ms()-t)/60000))
        await uasyncio.sleep(config["time_interval"])
        

async def cloud_subscribe():
    global d2, t
    global config
    while True:
        if config["cloud"] == "true":
            t=ticks_ms()
            try:
                led.color(700, 700)
                mqtt_cloud.subscribe("/v1.6/devices/smartgeiger/buzzer")
                mqtt_cloud.check_msg()
                led.off()
            except:
                print("cloud subscribe faild")
            d2=int(d2+(d2*(ticks_ms()-t)/60000))
        await uasyncio.sleep(config["time_interval"])


async def ifttt():

    while True:
        global d2, t
        if d2 > 100 and config["msg_alert"] == "true":
            t=ticks_ms()
            try:
                led.color(700, 700)
                readings = {'value1':d1, 'value2':d2, 'value3':d3}
                print(readings)
            
                request_headers = {'Content-Type': 'application/json'}

                request = urequests.post(
                    'http://maker.ifttt.com/trigger/SmartGeiger/with/key/' + config["ifttt_key"],
                    json=readings,
                    headers=request_headers)
                request.close()
                led.off()
                await uasyncio.sleep(180)
            except OSError as e:
                print('Failed to read/publish readings.')
                await uasyncio.sleep(10)
            d2=int(d2+(d2*(ticks_ms()-t)/60000))
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
