import logging
from time import sleep  
from datetime import datetime  
import ms5837
from simple_pid import PID
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_servokit import ServoKit
import FaBo9Axis_MPU9250



'''
sudo pip3  install simple-pid

'''


PATCH = ''



class MedaLogging:
    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        name = PATCH + '-'.join('-'.join('-'.join(str(datetime.now()
                                              ).split()).split('.')).split(':')) + '.log'
        
        self.file = logging.FileHandler(name)
        self.fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s")
        self.file.setLevel(logging.DEBUG)
        self.file.setFormatter(self.fileformat)
        # обработчик вывода в консоль лог файла
        self.stream = logging.StreamHandler()
        self.streamformat = logging.Formatter(
            "%(levelname)s:%(module)s:%(message)s")
        self.stream.setLevel(logging.DEBUG)
        self.stream.setFormatter(self.streamformat)
        # инициализация обработчиков
        self.mylogs.addHandler(self.file)
        self.mylogs.addHandler(self.stream)

        self.mylogs.info('start-logging')

    def debug(self, message):
        self.mylogs.debug(message)

    def info(self, message):
        self.mylogs.info(message)

    def warning(self, message):
        self.mylogs.warning(message)

    def critical(self, message):
        self.mylogs.critical(message)

    def error(self, message):
        self.mylogs.error(message)




class DeptAndTemp:
    # класс описывающий общение с датчиком глубины 
    def __init__(self, logger: MedaLogging):
        
        self.logger = logger
        # плотность воды 
        density = 1000 
        # илициализация сенсора 
        self.sensor  = ms5837.MS5837_30BA()
        if self.sensor.init():
            self.sensor.setFluidDensity(ms5837.DENSITY_SALTWATER)
            self.sensor.setFluidDensity(density)
            self.dept_defolt = round(self.sensor.depth(), 3)
            self.logger.info('DEPT-SENSOR-init')
        else:
            self.logger.critical('NO-SENSOR-DEPT')


    def reqiest(self):
        # опрос датчика давления
        if self.sensor.read():
            massout = {}
            massout['dept'] = round(self.sensor.depth(), 3) - self.dept_defolt
            massout['term'] = round(self.sensor.temperature(), 3)
            return massout
        else:
            self.logger.critical('NO-SENSOR-DEPT')
            return {'dept':-100,'temp': -100}


class PwmControl:
    def __init__(self,logger:MedaLogging):
        self.logger = logger
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
            self.logger.info('PWM-CONTROL-init')
        except:
            self.logger.critical('NO-PWM-CONTROL')

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
        
        self.man.angle = mass['man']
        
        self.servoCam.angle = mass['servoCam']
        
        if mass['led']:
            self.led.angle = 180 
        else:
            self.led.angle = 0
            
        



logger = MedaLogging()
dept_temp = DeptAndTemp(logger)
pid = PID(1, 0.1, 0.05, setpoint=1)
pid.output_limits


def main_autodept():

    control_dept = dept_temp.reqiest()['dept']

    while True:
        

        