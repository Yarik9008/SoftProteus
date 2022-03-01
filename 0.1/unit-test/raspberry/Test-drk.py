from time import sleep
from adafruit_servokit import ServoKit


# motor[0]  1 ходовой мотор (вид сверху левый передний)     // <0>   <1>//
# motor[1]  2 ходовой мотор (вид сверху правый передний)    //    <4>    //      
# motor[2]  3 ходовой мотор (вид сверху левый задний)       //    <5>    //
# motor[3]  4 ходовой мотор (вид сверзу правый задний)      // <2>   <3> //
# motor[4]  передний дифферентный мотор
# motor[5]  задний дифферентный мотор


class PwmControl:
    def __init__(self):
        # диапазон шим модуляции 
        self.pwmMin = 1100
        self.pwmMax = 1950
        # коофиценты корректировки мощности на каждый мотор 
        self.CorDrk0 = 1
        self.CorDrk1 = 1
        self.CorDrk2 = 1
        self.CorDrk3 = 1
        self.CorDrk4 = 1
        self.CorDrk5 = 1
        # инициализация платы 
        try:
            self.kit = ServoKit(channels=16)
            print('\033[92mPWM-CONTROL-init\033[0m')
        except:
            print('\033[91mNO-PWM-CONTROL\033[0m')
            

        self.drk0 = self.kit.servo[0]
        self.drk0.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.drk1 = self.kit.servo[2]
        self.drk1.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.drk2 = self.kit.servo[1]
        self.drk2.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.drk3 = self.kit.servo[3]
        self.drk3.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.drk4 = self.kit.servo[4]
        self.drk4.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.drk5 = self.kit.servo[5]
        self.drk5.set_pulse_width_range(self.pwmMin, self.pwmMax)
        
        # взаимодействие с манипулятором 
        self.man = self.kit.servo[6]
        self.man.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.man.angle = 0
        
        # взаимодействие с сервоприводом камеры 
        self.servoCam = self.kit.servo[7]
        #self.servoCam.set_pulse_width_range(self.pwmMin, self.pwmMax)
        self.servoCam.angle = 90
        
        # взаимодействие с светильником 
        self.led = self.kit.servo[8]
        self.led.angle = 0
        
        # инициализация моторов 
        self.drk0.angle = 180
        self.drk1.angle = 180
        self.drk2.angle = 180
        self.drk3.angle = 180
        self.drk4.angle = 180
        self.drk5.angle = 180
        sleep(2)
        self.drk0.angle = 0
        self.drk1.angle = 0
        self.drk2.angle = 0
        self.drk3.angle = 0
        self.drk4.angle = 0
        self.drk5.angle = 0
        sleep(2)
        self.drk0.angle = 87
        self.drk1.angle = 87
        self.drk2.angle = 87
        self.drk3.angle = 87
        self.drk4.angle = 87
        self.drk5.angle = 87
        sleep(3)

    def ControlMotor(self, mass: dict):
        # отправка шим сигналов на моторы
        self.drk0.angle = mass['motor0']
        self.drk1.angle = mass['motor1']
        self.drk2.angle = mass['motor2']
        self.drk3.angle = mass['motor3']
        self.drk4.angle = mass['motor4']
        self.drk5.angle = mass['motor5']
        

if __name__ == '__main__':
    test_control = {'motor0': 0, 'motor1': 0, 
                    'motor2': 0, 'motor3': 0, 
                    'motor4': 0, 'motor5': 0}

    test_motor = PwmControl()
    for i in range(6):
        print(f'motor-{i}')
        test_control[f'motor{i}'] = 50
        test_motor.ControlMotor()
        test_control['motor{i}'] = 0
        sleep(5)
