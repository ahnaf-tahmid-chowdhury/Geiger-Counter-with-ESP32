# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)

import gc
gc.collect()

from json import loads, dumps
f = open('config.json', 'r')
config = loads(f.read())
f.close()
