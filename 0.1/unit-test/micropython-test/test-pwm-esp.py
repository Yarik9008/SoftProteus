<<<<<<< HEAD
from machine import Pin, PWM
from time import sleep

pwm0 = PWM(Pin(23), freq=50)# create PWM object from a pin

for i in range(20,121):
    pwm0.duty(i)# set duty cycle
    print(i)
    sleep(0.1)
=======
from machine import Pin, PWM
from time import sleep

pwm0 = PWM(Pin(23), freq=50)# create PWM object from a pin

for i in range(20,121):
    pwm0.duty(i)# set duty cycle
    print(i)
    sleep(0.1)
>>>>>>> 60636f8cf41ce6ed7954913253b849bfe73c69ce
