from machine import Pin, PWM
from utime import sleep_ms, sleep_us

@micropython.native
class GMtube:
    count = 0
    def __init__(self,pwm=12,freq=10000,duty=675,event=15):
        self.freq=freq
        self.duty=duty
        
        #print('HV pin 12, freq 10kHz, duty 66%)
        self.pwmpin = PWM(Pin(pwm), freq=freq, duty=duty)
        #event pin 15
        self.discharge = Pin(event, Pin.IN)
        self.discharge.irq(trigger=Pin.IRQ_FALLING, handler= self.handle)

        # Function to be called when the interrupt triggers
    def handle(self,p):
        global count
        self.count+=1

class Buzzer:
    def __init__(self,pin1=2,pin2=4):
        self.pin_1 = Pin(pin1, Pin.OUT)
        self.pin_2 = Pin(pin2, Pin.OUT)

    def buzzer(self):
        self.pin_1.on()
        self.pin_2.off()
        sleep_ms(2)
        self.pin_1.off()
        self.pin_2.on()
        sleep_us(1) 
        self.pin_2.off()
    def off(self):
        self.pin_1.off()
        self.pin_2.off()