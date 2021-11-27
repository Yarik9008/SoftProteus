import socket  # библиотека для связи
import threading  # библиотека для потоков
import sys
import serial
from time import sleep  # библиотека длязадержек
from datetime import datetime  # получение текущего времени
from configparser import ConfigParser  # чтание конфигов
from ast import literal_eval

class ROVProteusClient:
    #Класс ответсвенный за связь с постом 
    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 1234
        self.telemetria = True
        self.checkConnect = True      
        # Настройки клиента 
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.client.connect((self.HOST, self.PORT))  # подключение адресс  порт

    def ClientDispatch(self, data:dict):
        #Функция для  отправки пакетов на пульт 
        if self.checkConnect:
            data['time'] = str(datetime.now())
            DataOutput = str(data).encode("utf-8")
            self.client.send(data)

    def ClientReceivin(self):
        #Прием информации с поста управления 
        if self.checkConnect:
            data = self.client.recv(512).decode('utf-8')
            if len(data) == 0:
                self.checkConnect = False
                self.client.close()
                return None
            data = dict(literal_eval(str(data)))
            if self.telemetria:
                print(data)
            return data

class ShieldTnpa:
    def __init__(self):
        # Создание обьекта для взаимодействия с низким уровнем по uart
        self.PORT = "/dev/serial0"
        self.RATE = 19200
        self.serialPort = serial.Serial(self.PORT, self.RATE)
        self.checkConnect = True   
    
    def ShildDispatch(self, data:list):
        # отправка на аппарат
        if self.checkConnect:
            data = (str(data) + '\n').encode()
            self.serialPort.write(data)
            
    def ShildReceivin(self):
        # прием информации с аппарата 
        if self.checkConnect:
            data = self.serialPort.readline()
            if len(str(data)) <= 5:
                return None
            data = [int(i) for i in ((str(data)[2:-3]).split('-'))]
            return data 

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
        
        self.client = ROVProteusClient()
        self.shield = ShieldTnpa()
        
    def RunCommand(self):
        while True:
            # блок отправки значений на аппарат
            self.DataInput = self.client.ClientReceivin()
            dat = self.DataInput
            datalist  = [dat['motor0'], dat['motor1'], dat['motor2'],
                        dat['motor3'], dat['motor4'], dat['motor5'], 
                        dat['servo'], dat['manipul']]
            self.shield.ShildDispatch(datalist)
            
            # блок приема ответа с телеметрией 
            inputlist = self.shield.ShildReceivin()
            self.DataOutput['volt'] = inputlist[0]
            self.DataOutput['dept'] = inputlist[1]
            self.DataOutput['azimut'] = inputlist[2]
            self.DataOutput['time'] = str(datetime.now())
            
            self.client.ClientDispatch(self.DataOutput)
            

