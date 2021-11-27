import socket  # библиотека для связи
import logging
import coloredlogs
import os
from time import sleep  # библиотека длязадержек
from datetime import datetime  # получение текущего времени
from configparser import ConfigParser  # чтание конфигов
from ast import literal_eval
from threading import Thread


class MedaLogging:
    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        self.file = logging.FileHandler("Main.log")
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
    def __init__(self, logger: MedaLogging):
        self.logger = logger
        self.HOST = '127.0.0.1'
        self.PORT = 1115
        self.telemetria = True
        self.checkConnect = True
        # Настройки клиента
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.client.connect((self.HOST, self.PORT))  # подключение адресс  порт

    def ClientDispatch(self, data: dict):
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
            self.logger.info('ADC1115-init')
        except:
            self.logger.critical('NO-ADC1115')

        self.MassOut = {}

    def ReqestAmper(self):
        try:
            return {'a0':1, 'a1':1, 'a2':1,'a2':1,'a3':1, 'a4':1, 'a5':1}
        except:
            self.logger.critical('NO-ADC1115')
            return None


class Compass:
    # класс описывающий общение с модулем навигации mpu9250
    def __init__(self, logger: MedaLogging):
        self.logger = logger

        try:
            self.logger.info('MPU9250-init')
        except:
            self.logger.critical('NO-MPU9250')

    def reqiest(self):
        # возвращает словарь с значениями азимута
        try:
            return {'azim':  180}
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
        self.logger.info('DEPT-SENSOR-init')

    def reqiest(self):
        # опрос датчика давления
        massout = {}
        massout['dept'] = 5
        massout['term'] = 25
        return massout


class PwmControl:
    def __init__(self, logger: MedaLogging):
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
            self.logger.info('PWM-CONTROL-init')
        except:
            self.logger.critical('NO-PWM-CONTROL')


    def ControlMotor(self, mass: dict):
        # отправка шим сигналов на моторы
        print(mass)

class ReqiestSensor:
    # класс-адаптер обьеденяющий в себе сбор информации с всех сенсоров
    def __init__(self, logger):
        self.logger = logger
        self.acp = Acp(self.logger)  # обект класса ацп
        self.mpu9250 = Compass(self.logger)  # обьект класса compass
        self.ms5837 = DeptAndTemp(self.logger)

    def reqiest(self):
        # опрос датчиков; возвращает обьект класса словарь
        massacp = self.acp.ReqestAmper()
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
        command['motor2'] = self.safety((180 - command['motor2'] * 1.8) - 3)
        command['motor3'] = self.safety((180 - command['motor3'] * 1.8) - 3)
        command['motor4'] = self.safety((180 - command['motor4'] * 1.8) - 3)
        command['motor5'] = self.safety((180 - command['motor5'] * 1.8) - 3)
        self.pwmcom.ControlMotor(command)


class MainApparat:
    def __init__(self):
        self.DataInput = {'time': None,  # Текущее время
                          'motorpowervalue': 1,  # мощность моторов
                          'led': False,  # управление светом
                          'manipul': 0,  # Управление манипулятором
                          'servo': 0,  # управление наклоном камеры
                          'motor0': 0, 'motor1': 0,  # значения мощности на каждый мотор
                          'motor2': 0, 'motor3': 0,
                          'motor4': 0, 'motor5': 0}
        # массив отсылаемый на аппарат
        self.DataOutput = {'time': None, 'dept': 0, 'volt': 0, 'azimut': 0}

        self.logger = MedaLogging()

        self.client = ROVProteusClient(self.logger)
        self.sensor = ReqiestSensor(self.logger)
        self.comandor = Command(self.logger)

    def RunCam(self):
        os.system('/home/pi/SoftProteus-2.0/cam/udp_client.py')

    def RunMainApparat(self):
        # прием информации с поста управления
        # отработка по принятой информации
        # сбор информации с датчиков
        # отправка телеметрии на пост управления
        while True:
            data = self.client.ClientReceivin()
            if data != None:
                self.controllmass = data  # прием информации с поста управления
            else:
                break

            self.comandor.commanda(self.controllmass)
            # сбор информации с датчиков и отправка на пост управления
            self.client.ClientDispatch(self.sensor.reqiest())


if __name__ == '__main__':
    apparat = MainApparat()
    apparat.RunMainApparat()
