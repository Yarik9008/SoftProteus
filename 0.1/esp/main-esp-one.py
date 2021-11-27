from machine import UART # общение с разбери по сериал порту 
from machine import Pin, PWM # шим модули 
from machine import ADC
from time import sleep

def initpins():
    global motor0, motor1, motor2, motor3, motor4, motor5,\
    servo0, servo1, uart1, analog0, analog1, analog2, analog3,\
    analog4, analog5, analogVolt
    #инициализация связи
    uart1 = UART(2, baudrate=19200, tx=17, rx=16, timeout = 1000)
    # инициализация моторов
    motor0 = PWM(Pin(13), freq=100)
    motor1 = PWM(Pin(12), freq=100)
    motor2 = PWM(Pin(14), freq=100)
    motor3 = PWM(Pin(27), freq=100)
    motor4 = PWM(Pin(26), freq=100)
    motor5 = PWM(Pin(25), freq=100)
    motor0.duty(220)
    motor1.duty(220)
    motor2.duty(220)
    motor3.duty(220)
    motor4.duty(220)
    motor5.duty(220)
    sleep(2)
    motor0.duty(90)
    motor1.duty(90)
    motor2.duty(90)
    motor3.duty(90)
    motor4.duty(90)
    motor5.duty(90)
    sleep(2)
    motor0.duty(155)
    motor1.duty(155)
    motor2.duty(155)
    motor3.duty(155)
    motor4.duty(155)
    motor5.duty(155)
    sleep(2)
    # инициализация сервоприводов 
    servo0 = PWM(Pin(23), freq=50)
    servo1 = PWM(Pin(22), freq=50)
    # инициализация аналоговых вводов 
    analog0 = ADC(Pin(32))
    analog0.atten(ADC.ATTN_11DB)
    analog0.width(ADC.WIDTH_12BIT)  
    analog1 = ADC(Pin(32))
    analog1.atten(ADC.ATTN_11DB)
    analog1.width(ADC.WIDTH_12BIT) 
    analog2 = ADC(Pin(32)) 
    analog2.atten(ADC.ATTN_11DB)
    analog2.width(ADC.WIDTH_12BIT)  
    analog3 = ADC(Pin(32))
    analog3.atten(ADC.ATTN_11DB)
    analog3.width(ADC.WIDTH_12BIT)  
    analog4 = ADC(Pin(32)) 
    analog4.atten(ADC.ATTN_11DB)
    analog4.width(ADC.WIDTH_12BIT)  
    analog5 = ADC(Pin(32))
    analog5.atten(ADC.ATTN_11DB)
    analog5.width(ADC.WIDTH_12BIT) 
    analogVolt = ADC(Pin(32)) 
    analogVolt.atten(ADC.ATTN_11DB)
    analogVolt.width(ADC.WIDTH_12BIT) 

def requestAnalog():
    value0 = str(analog0.read())
    value1 = str(analog1.read())
    value2 = str(analog2.read())
    value3 = str(analog3.read())
    value4 = str(analog4.read())
    value5 = str(analog5.read())
    valueVolt = str(analogVolt.read())
    return [value0, value1, value2, value3, value4, value5, valueVolt]

def controllPwm(massIn:list):
     # отправка полученных значений на моторы 
    motor0.duty(massIn[0])
    motor1.duty(massIn[1])
    motor2.duty(massIn[2])
    motor3.duty(massIn[3])
    motor4.duty(massIn[4])
    motor5.duty(massIn[5])
    # отправка полученных хначений на сервоприводы 
    servo0.duty(massIn[6])
    servo1.duty(massIn[7])

def main():
    initpins()
    while True:
        data = uart1.readline()
        if len(str(data)) <= 14:
            data = b'155-155-155-155-155-155-155-155\n'
            print(None)
        massControll = [int(i) for i in ((str(data)[2:-3]).split('-'))]
        print(massControll)
        controllPwm(massControll)
        outp = '-'.join(requestAnalog()) + '\n'
        print(outp)
        uart1.write(outp)
        
if __name__ == '__main__':
    main()



