def Connect():
    import network
    import time
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    essid="Chowdhury"                         #set default essid
    password="atc48888"                       #set default password
    count=0
    while wlan.isconnected()==False:
        if count>0:
            print("wrong entry.")
            time.sleep(0.2)
        print('Network setup')
        d=input("do you want to connect to the previous network? yes/no : ")
        if d.lower()=="y" or d.lower()=="yes" or d.lower()=="ye" or d.lower()=="ok" or d.lower()=="":
            wlan.connect(essid, password)
            
        else:
            print("searching available essid:")
            for x in wlan.scan():
                print(x)
            essid=input("essid: ")
            password=input("password: ")
            wlan.connect(essid, password)
            print('connecting to network...')
        count+=1
        if not wlan.isconnected():
            time.sleep(4)
    print('network config:', wlan.ifconfig())
    
def auto_connect():
    import network
    essid="Chowdhury"                         #set default essid
    password="atc48888"                       #set default password
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(essid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
