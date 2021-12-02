from time import sleep
from adafruit_servokit import ServoKit

# Set channels to the number of servo channels on your kit.
# 8 for FeatherWing, 16 for Shield/HAT/Bonnet.


class PWMControll:
    def __init__(self):

        # инициализация моторов
        self.kit = ServoKit(channels=16)

        self.drk0 = self.kit.servo[0]
        self.drk0.set_pulse_width_range(1100, 1900)
        self.drk1 = self.kit.servo[1]
        self.drk1.set_pulse_width_range(1100, 1900)
        self.drk2 = self.kit.servo[2]
        self.drk2.set_pulse_width_range(1100, 1900)
        self.drk3 = self.kit.servo[3]
        self.drk3.set_pulse_width_range(1100, 1900)
        self.drk4 = self.kit.servo[4]
        self.drk4.set_pulse_width_range(1000, 1900)
        self.drk5 = self.kit.servo[5]
        self.drk5.set_pulse_width_range(1000, 1900)
        
        # взаимодействие с манипулятором
        self.man = self.kit.servo[6]
        # взаимодействие с сервоприводом камеры
        self.servoCam = self.kit.servo[7]
        # взаимодействие с светильником
        self.led = self.kit.servo[8]

        self.initMotor()

        print('init-motor')

    def initMotor(self):
        self.drk0.angle = 180
        self.drk1.angle = 180
        self.drk2.angle = 180
        self.drk3.angle = 180
        self.drk4.angle = 180
        self.drk5.angle = 180
        print('motor max')
        sleep(2)
        self.drk0.angle = 0
        self.drk1.angle = 0
        self.drk2.angle = 0
        self.drk3.angle = 0
        self.drk4.angle = 0
        self.drk5.angle = 0
        print('motor min')
        sleep(2)
        self.drk0.angle = 87
        self.drk1.angle = 87
        self.drk2.angle = 87
        self.drk3.angle = 87
        self.drk4.angle = 87
        self.drk5.angle = 87
        print('motor center')
        sleep(6)
        print('motor good')

    def test_value(self):
        # тест первого мотора
        self.drk0.angle = 0
        print('motor0: 0')
        sleep(2)
        self.drk0.angle = 180
        print('motor0: 180')
        sleep(2)
        self.drk0.angle = 87
        # тест второго мотора
        self.drk1.angle = 0
        print('motor1: 0')
        sleep(2)
        self.drk1.angle = 180
        print('motor1: 180')
        sleep(2)
        self.drk1.angle = 87
        # тест третьего мотора 
        self.drk2.angle = 0
        print('motor2: 0')
        sleep(2)
        self.drk2.angle = 180
        print('motor2: 180')
        sleep(2)
        self.drk2.angle = 87
        # тест четвертого мотора
        self.drk3.angle = 0
        print('motor3: 0')
        sleep(2)
        self.drk3.angle = 180
        print('motor3: 180')
        sleep(2)
        self.drk3.angle = 87
        # тест пятого мотора 
        self.drk4.angle = 0
        print('motor4: 0')
        sleep(2)
        self.drk4.angle = 180
        print('motor4: 180')
        sleep(2)
        self.drk4.angle = 87
        # тест шестого мотора 
        self.drk5.angle = 0
        print('motor5: 0')
        sleep(2)
        self.drk5.angle = 180
        print('motor5: 180')
        sleep(2)
        self.drk5.angle = 87
        
        #тест манипулятора 
        self.man.angle = 0
        print('man: 0')
        sleep(2)
        self.man.angle = 180 
        print('man: 180')
        sleep(2)
        
        # тест сервопривода камеры 
        self.servoCam.angle = 10
        print('servoCam: 10')
        sleep(2)
        self.servoCam.angle = 170
        print('servoCam: 170')
        sleep(2)
        self.servoCam.angle = 90
        
        # тест светильника 
        self.led.angle = 0 
        print('led: False')
        sleep(2)
        self.led.angle = 180
        print('led: True')
        sleep(2)
        self.led.angle = 0 
        
        
        print('final')



if __name__ == '__main__':
    pwmi = PWMControll()
    pwmi.test_value()
