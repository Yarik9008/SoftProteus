import time
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

canal = 6

print(180)
kit.servo[canal].angle = 180
time.sleep(10)
print(0)
kit.servo[canal].angle = 0
print('final')