import csv
import time
import serial

data= serial.Serial("/dev/ttyUSB0",115200)
filename='PC/data3D.csv'
header1='x'
header2='y'
header3='z'

fildnames = [header1,header2,header3]
x = 0.0
y = 0.0
z = 0.0

with open(filename,"w") as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames = fildnames)
    csv_writer.writeheader()

while 1:
    while not data.inWaiting():
        pass
    data_read=data.readline().decode('utf-8')  # data are in byte code. decode to unicode
    data_array=data_read.split(",")

    with open(filename, 'a') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames = fildnames)

        info = {
            header1 : x,
            header2 : y,
            header3 : z,
        }

        x = data_array[0]
        y = data_array[1]
        z = data_array[2]
        csv_writer.writerow(info)
        print(x,y,z)

    time.sleep(0.004)
