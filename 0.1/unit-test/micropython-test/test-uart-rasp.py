import serial

ser = serial.Serial ("/dev/ttyS0",9600)    #Open named port 

while 1:
    data = ser.readline()
    ser.write('esp\n'.encode())
    print(data)

