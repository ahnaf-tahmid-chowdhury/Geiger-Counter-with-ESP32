# buzzer
from machine import Pin
from utime import sleep_ms

D2 = Pin(2, Pin.OUT)
D4 = Pin(4, Pin.OUT)

def buzzer():
    D2.on()
    D4.off()
    sleep_ms(2)
    D2.off()
    D4.on()
    sleep_ms(2) # this goes into dead time of the counter
    D4.off()