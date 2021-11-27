from machine import Pin, PWM
from time import sleep

pwm0 = PWM(Pin(13), freq=100)# create PWM object from a pin
pwm0.duty(220)
sleep(2)
pwm0.duty(90)
sleep(2)
pwm0.duty(153)
sleep(6)
for i in range(90,155):
    pwm0.duty(i)# set duty cycle
    print(i)
    sleep(0.5)
