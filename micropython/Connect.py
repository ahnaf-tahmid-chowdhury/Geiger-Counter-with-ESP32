import network
from utime import sleep
import webrepl
from json import loads

f = open('config.json', 'r')
config = loads(f.read())
f.close()

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print('connecting to network...')
    wlan.connect(config['essid'], config['password'])
    sleep(4)
    if not wlan.isconnected():
        wlan.active(False)
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid = "SmartGeiger",password = "SmartGeiger") # set the ESSID of the access point with password
        while not ap.active():
            webrepl.start()

