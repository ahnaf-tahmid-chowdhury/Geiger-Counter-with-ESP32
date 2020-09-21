def connect():
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
        print('connecting to network...')
        d=input("do you want to connect to the previous network? yes/no : ")
        if d.lower()=="y" or d.lower()=="yes" or d.lower()=="ye" or d.lower()=="ok":
            wlan.connect(essid, password)
            
        else:
            print("searching available essid:")
            for x in wlan.scan():
                print(x)
            essid=input("essid: ")
            password=input("password: ")
            wlan.connect(essid, password)
            
        count+=1
        if not wlan.isconnected():
            time.sleep(3)
    print('network config:', wlan.ifconfig())
