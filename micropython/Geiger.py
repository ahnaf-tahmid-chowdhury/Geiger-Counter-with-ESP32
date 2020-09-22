from machine import Pin, PWM

count = 0

def pwm_400v():
    # PWM for 400V driver (pin12=D12)
    print('HV pin 12, freq 10kHz, duty 66, event pin 15')
    pwm = PWM(Pin(12), freq=10000, duty=66)
def discharge():
    # geiger discharge (pin15=D15)
    global count
    dc = Pin(15, Pin.IN)
    dc.irq(trigger=Pin.IRQ_FALLING, handler= handle)


def handle(p):     # Function to be called when the interrupt triggers.
    global count
    count += 1

