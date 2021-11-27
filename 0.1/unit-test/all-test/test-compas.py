import FaBo9Axis_MPU9250
import time
import sys
mpu9250 = FaBo9Axis_MPU9250.MPU9250()
from math import atan2, pi

try:
    
    while True:
        accel = mpu9250.readAccel()
        gyro = mpu9250.readGyro()
        mag = mpu9250.readMagnet()
        time.sleep(0.1) 
        print(round((atan2(mag['x'], mag['y']) * 180 / pi), 3))
        

except KeyboardInterrupt:
    sys.exit()
