<<<<<<< HEAD
import serial

ser = serial.Serial ("/dev/ttyS0",9600)    #Open named port 

while 1:
    data = ser.readline()
    ser.write('esp\n'.encode())
    print(data)

=======
import serial

ser = serial.Serial ("/dev/ttyS0",9600)    #Open named port 

while 1:
    data = ser.readline()
    ser.write('esp\n'.encode())
    print(data)

>>>>>>> 60636f8cf41ce6ed7954913253b849bfe73c69ce
