from machine import UART # общение с разбери по сериал порту 
from machine import Pin, PWM # шим модули 
from time import sleep # сон модуль 
import _thread # многопоточность micropython 

def init():
    global motor0, motor1, motor2, motor3, motor4, motor5, led0, led1, servo0, servo1, uart1
    #инициализация связи
    uart1 = UART(2, baudrate=9600, tx=17, rx=16, timeout = 1000)
    # инициализация моторов
    
    motor0 = PWM(Pin(2), freq=50)
    motor1 = PWM(Pin(3), freq=50)
    motor2 = PWM(Pin(4), freq=50)
    motor3 = PWM(Pin(5), freq=50)
    motor4 = PWM(Pin(6), freq=50)
    motor5 = PWM(Pin(7), freq=50)
    # инициализация светильников 
    led0= PWM(Pin(8), freq=50)
    led1 = PWM(Pin(9), freq=50)
    # инициализация сервоприводов 
    servo0 = PWM(Pin(10), freq=50)
    servo1 = PWM(Pin(11), freq=50)
    

def mainIn(*args):
    global motor0, motor1, motor2, motor3, motor4, motor5, led0, led1, servo0, servo1, uart1
    while True:
        # massControll распиновка 
        # 70-70-70-70-70-70-20-20-70-70
        # m0-m1-m2-m3-m4-m5-l0-l1-s0-s1 
        # по умолчению если ничего не приходит будет каждую секунду выдовать None и все будет оставаться в начальной позиции
        data = uart1.readline()
        if data == None:
            print(None)
            # установка в нулевое положение и отключение всего
            motor0.duty(70)
            motor1.duty(70)
            motor2.duty(70)
            motor3.duty(70)
            motor4.duty(70)
            motor5.duty(70)
        
            #led0.duty(20)
            #led1.duty(20)
        
            servo0.duty(70)
            servo1.duty(70)
            continue
        else:
            massControll = str(data).split('-')
        # отправка полученных значений на моторы 
        motor0.duty(massControll[0])
        motor1.duty(massControll[1])
        motor2.duty(massControll[2])
        motor3.duty(massControll[3])
        motor4.duty(massControll[4])
        motor5.duty(massControll[5])
        # отправка полученных значений на светильники 
        #led0.duty(massControll[6])
        #led1.duty(massControll[7])
        # отправка полученных хначений на сервоприводы 
        #servo0.duty(massControll[8])
        servo1.duty(massControll[9])

def mainOut(*args):
    global uart1
    gebag = True
    while True:
        # v1-a0-a1-a2-a3-a4-a5-x-y
        # 0-0-0-0-0-0-0-0-0
        # опрос датчиков
        if gebag: 
            uart1.write('0-0-0-0-0-0-0-0-0\n')
        sleep(1)
        
        
def main():
    init()
    #threadIn = _thread.start_new_thread(mainIn,())
    #threadOut = _thread.start_new_thread(mainOut,())
    

main()
