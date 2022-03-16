import time
from adafruit_servokit import ServoKit

# Set channels to the number of servo channels on your kit.
# 8 for FeatherWing, 16 for Shield/HAT/Bonnet.
kit = ServoKit(channels=16)

canal = 8


kit.servo[canal].angle = 180
time.sleep(5)
kit.servo[canal].angle = 0
print('final')

