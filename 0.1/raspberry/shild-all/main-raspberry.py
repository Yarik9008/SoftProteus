import socket  # библиотека для связи
import board
import busio
import logging
import coloredlogs
import os
from time import sleep  # библиотека длязадержек
from datetime import datetime  # получение текущего времени
from ast import literal_eval
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_servokit import ServoKit
import FaBo9Axis_MPU9250
from math import atan2, pi
import ms5837
from threading import Thread



class MedaLogging:
    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        name = 'log/controll-post/' + '-'.join('-'.join('-'.join(str(datetime.now()
                                              ).split()).split('.')).split(':')) + '.log'
        name = 'main.log'
        
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
        coloredlogs.install(level=logging.DEBUG, logger=self.mylogs,
                            fmt='%(asctime)s [%(levelname)s] - %(message)s')

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


class ROVProteusClient:
    #Класс ответсвенный за связь с постом 
    def __init__(self, logger:MedaLogging):
        self.logger = logger
        self.HOST = '192.168.1.100'
        self.PORT = 1211
        self.telemetria = True
        self.checkConnect = True      
        # Настройки клиента 
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.client.connect((self.HOST, self.PORT))  # подключение адресс  порт

    def ClientDispatch(self, data:dict):
        #Функция для  отправки пакетов на пульт 
        if self.checkConnect:
            data['time'] = str(datetime.now())
            self.logger.debug(str(data))
            DataOutput = str(data).encode("utf-8")
            self.client.send(DataOutput)

    def ClientReceivin(self):
        #Прием информации с поста управления 
        if self.checkConnect:
            data = self.client.recv(512).decode('utf-8')
            if len(data) == 0:
                self.checkConnect = False
                self.logger.info('Rov-disconect')
                self.client.close()
                return None
            data = dict(literal_eval(str(data)))
            self.logger.debug(str(data))
            return data


class Acp:
    def __init__(self, logger: MedaLogging):
        '''
        Класс описывающий взаимодействие и опрос датчиков тока
        '''
        self.logger = logger
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ads13 = ADS.ADS1115(self.i2c)
            self.adc46 = ADS.ADS1115(self.i2c, address=0x49)
            a0 = AnalogIn(self.ads13, ADS.P0)
            a1 = AnalogIn(self.ads13, ADS.P1)
            a2 = AnalogIn(self.ads13, ADS.P2)
            a3 = AnalogIn(self.adc46, ADS.P3)
            a4 = AnalogIn(self.adc46, ADS.P0)
            a5 = AnalogIn(self.adc46, ADS.P1)
            

            self.CorNulA1 = a0.value
            self.CorNulA2 = a1.value
            self.CorNulA3 = a2.value
            self.CorNulA4 = a3.value
            self.CorNulA5 = a4.value
            self.CorNulA6 = a5.value
            self.logger.info('ADC1115-init')
        except:
            self.logger.critical('NO-ADC1115')
        
        self.MassOut = {}

    def ReqestAmper(self):
        try:
            #Функция опроса датчиков тока 
            a0 = AnalogIn(self.ads13, ADS.P0)
            a1 = AnalogIn(self.ads13, ADS.P1)
            a2 = AnalogIn(self.ads13, ADS.P2)
            a3 = AnalogIn(self.ads13, ADS.P3)
            a4 = AnalogIn(self.adc46, ADS.P0)
            a5 = AnalogIn(self.adc46, ADS.P1)
            v = AnalogIn(self.adc46, ADS.P2)
            # TODO  матан для перевода значений - отсылается уже в амперах
            self.MassOut['a0'] = round(
                (a0.value - self.CorNulA1) * 0.00057321919, 3)
            self.MassOut['a1'] = round(
                (a1.value - self.CorNulA2) * 0.00057321919, 3)
            self.MassOut['a2'] = round(
                (a2.value - self.CorNulA3) * 0.00057321919, 3)
            self.MassOut['a3'] = round(
                (a3.value - self.CorNulA4) * 0.00057321919, 3)
            self.MassOut['a4'] = round(
                (a4.value - self.CorNulA5) * 0.00057321919, 3)
            self.MassOut['a5'] = round(
                (a5.value - self.CorNulA6) * 0.00057321919, 3)
            
            self.MassOut['v'] = round(v.voltage * 5, 3)
            # возвращает словарь с значениями амрепметра нумерация с нуля
            return self.MassOut
        except:
            self.logger.critical('NO-ADC1115')
            return None


class Compass:
    # класс описывающий общение с модулем навигации mpu9250
    def __init__(self, logger:MedaLogging):
        self.logger = logger
        
        try:
            self.mpu9250 = FaBo9Axis_MPU9250.MPU9250()
            self.logger.info('MPU9250-init')
        except:
            self.logger.critical('NO-MPU9250')
    
    def reqiest(self):
        # возвращает словарь с значениями азимута
        try:
            mag = self.mpu9250.readMagnet()
            return {'azim':(round((atan2(mag['x'], mag['y']) * 180 / pi), 3))}
        except:
            self.logger.critical('NO-MPU9250')
            return None


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
            self.logger.info('DEPT-SENSOR-init')
        else:
            self.logger.critical('NO-SENSOR-DEPT')


    def reqiest(self):
        # опрос датчика давления
        if self.sensor.read():
            massout = {}
            massout['dept'] = round(self.sensor.depth(), 3)
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
            
        

class ReqiestSensor:
    # класс-адаптер обьеденяющий в себе сбор информации с всех сенсоров 
    def __init__(self, logger):
        self.logger = logger
        self.acp = Acp(self.logger) # обект класса ацп 
        self.mpu9250 = Compass(self.logger) # обьект класса compass 
        self.ms5837 = DeptAndTemp(self.logger)
    
    def reqiest(self):
        # опрос датчиков; возвращает обьект класса словарь 
        massacp  = self.acp.ReqestAmper()
        massaz = self.mpu9250.reqiest()
        massMs5837 = self.ms5837.reqiest()
        
        massout = {**massacp, **massaz, **massMs5837}
        
        return massout
    
class Command:
    def __init__(self, logger):
        self.logger = logger
        self.pwmcom = PwmControl(self.logger)
    
    def safety(self, value):
        if value < 0:
            return 0
        elif value > 180:
            return 180
        else:
            return value
        
    def commanda(self, command):
        command['motor0'] = self.safety((180 - command['motor0'] * 1.8) - 3)
        command['motor1'] = self.safety((180 - command['motor1'] * 1.8) - 3)
        command['motor2'] = self.safety((command['motor2'] * 1.8) - 3)
        command['motor3'] = self.safety((180 - command['motor3'] * 1.8) - 3)
        command['motor4'] = self.safety((180 - command['motor4'] * 1.8) - 3)
        command['motor5'] = self.safety((command['motor5'] * 1.8) - 3)
        self.pwmcom.ControlMotor(command)

class MainApparat:
    def __init__(self):
        self.DataInput = {'time': None,  # Текущее время
                            'motorpowervalue': 1,  # мощность моторов
                            'led': False,  # управление светом
                            'manipul': 0,  # Управление манипулятором
                            'servo': 0, # управление наклоном камеры 
                            'motor0': 0, 'motor1': 0, # значения мощности на каждый мотор 
                            'motor2': 0, 'motor3': 0, 
                            'motor4': 0, 'motor5': 0}
        # массив отсылаемый на аппарат 
        self.DataOutput = {'time': None,'dept': 0,'volt': 0, 'azimut': 0 }

        self.logger = MedaLogging()
        
        self.client = ROVProteusClient(self.logger)
        self.sensor = ReqiestSensor(self.logger)
        self.comandor = Command(self.logger)
        
    
    def RunMainApparat(self):
        # прием информации с поста управления 
        # отработка по принятой информации 
        # сбор информации с датчиков 
        # отправка телеметрии на пост управления
        while True:
            data = self.client.ClientReceivin()
            if data!= None:
                self.controllmass = data # прием информации с поста управления 
            else:
                break
            
            self.comandor.commanda(self.controllmass)
            self.client.ClientDispatch(self.sensor.reqiest()) # сбор информации с датчиков и отправка на пост управления 

if __name__ == '__main__':
    apparat = MainApparat()
    apparat.RunMainApparat()
