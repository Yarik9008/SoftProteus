import socket
import threading  # модуль для разделения на потоки
import logging
import coloredlogs
import os
from datetime import datetime  # получение  времени
from time import sleep  # сон
from ast import literal_eval  # модуль для перевода строки в словарик
from pyPS4Controller.controller import Controller

DEBUG = False

class MedaLogging:
    '''Класс отвечающий за логирование. Логи пишуться в файл, так же выводться в консоль'''

    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        name = 'log/controll-post/' + '-'.join('-'.join('-'.join(str(datetime.now()
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
        coloredlogs.install(level=logging.DEBUG, logger=self.mylogs,
                            fmt='%(asctime)s [%(levelname)s] - %(message)s')

        self.mylogs.info('start-logging')

    def debug(self, message):
        '''сообщения отладочного уровня'''
        self.mylogs.debug(message)

    def info(self, message):
        '''сообщения информационного уровня'''
        self.mylogs.info(message)

    def warning(self, message):
        '''не критичные ошибки'''
        self.mylogs.warning(message)

    def critical(self, message):
        '''мы почти тонем'''
        self.mylogs.critical(message)

    def error(self, message):
        '''ребята я сваливаю ща рванет !!!!'''
        self.mylogs.error(message)


class ServerMainPult:
    '''
    Класс описывающий систему бекенд- пульта
    log - флаг логирования 
    log cmd - флаг вывода логов с cmd 
    host - хост на котором будет крутиться сервер 
    port- порт для подключения 
    motorpowervalue=1 - программное ограничение мощности моторов 
    joystickrate - частота опроса джойстика 
    '''

    def __init__(self, logger: MedaLogging, debug=False):
        # инициализация атрибутов
        self.JOYSTICKRATE = 0.2
        self.MotorPowerValue = 1
        self.telemetria = False
        self.checkConnect = False
        self.logger = logger
        # выбор режима: Отладка\Запуск на реальном аппарате
        if debug:
            self.HOST = '127.0.0.1'
            self.PORT = 1112
        else:
            self.HOST = '192.168.1.100'
            self.PORT = 1235
            
            
        # настройка сервера
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.server.bind((self.HOST, self.PORT))
        self.server.listen(1)
        self.user_socket, self.address = self.server.accept()
        self.checkConnect = True

        self.logger.info(f'ROV-Connected - {self.user_socket}')

    def ReceiverProteus(self):
        '''Прием информации с аппарата'''
        if self.checkConnect:
            data = self.user_socket.recv(512)
            if len(data) == 0:
                self.server.close()
                self.checkConnect = False
                self.logger.info(f'ROV-disconnection - {self.user_socket}')
                return None
            data = dict(literal_eval(str(data.decode('utf-8'))))
            if self.telemetria:
                self.logger.debug(f'DataInput - {str(data)}')
            return data

    def ControlProteus(self, data: dict):
        '''Отправка массива на аппарат'''
        if self.checkConnect:
            self.user_socket.send(str(data).encode('utf-8'))
            if self.telemetria:
                self.logger.debug(str(data))


class MyController(Controller):
    '''
    Класс для взаимодействия с джойстиком PS4 
    (работает только из под линукса из под винды управление только с помощью клавиатуры)

    правый джойтик вперед - движение вперед 
    правый джойстик вбок - движение лагом 

    левый джойстик вперед - всплытие
    левый джойстик вбок - разворот на месте 

    кнопки - корректировка нулевого положения для противодействия течениям и прочей ериси 

    кнопка ps - обнуление корректировок 
    '''

    def __init__(self):
        Controller.__init__(self, interface="/dev/input/js0",
                            connecting_using_ds4drv=False)
        self.DataPult = {'j1-val-y': 0, 'j1-val-x': 0,
                         'j2-val-y': 0, 'j2-val-x': 0,
                         'ly-cor': 0, 'lx-cor': 0,
                         'ry-cor': 0, 'rx-cor': 0,
                         'man': 90, 'servoCam': 90,
                         'led': False, 'auto-dept': False}
        self.log = True
        self.telemetria = False
        self.optionscontrol = False
        self.nitro = False
    # переключение режимов корректировок

    def on_options_press(self):
        self.optionscontrol = not self.optionscontrol
    # функция перевода данных с джойстиков

    def transp(self, value):
        return -1 * (value // 328)

    # блок опроса джойстиков
    def on_L3_up(self, value):
        '''погружение'''
        self.DataPult['j2-val-y'] =  value
        if self.telemetria:
            print('forward')

    def on_L3_down(self, value):
        '''всплытие'''
        self.DataPult['j2-val-y'] =  value
        if self.telemetria:
            print('back')

    def on_L3_y_at_rest(self):
        '''Обнуление'''
        self.DataPult['j2-val-y'] = 0
        if self.telemetria:
            print('back')

    def on_L3_left(self, value):
        '''Движение влево (лаг) '''
        if self.nitro:
            self.DataPult['j2-val-x'] =   value 
        else:
            self.DataPult['j2-val-x'] = value // 2
        if self.telemetria:
            print('left')

    def on_L3_right(self, value):
        '''Движение вправо (лаг) '''
        if self.nitro:
            self.DataPult['j2-val-x'] =   value 
        else:
            self.DataPult['j2-val-x'] = value // 2
        if self.telemetria:
            print('right')

    def on_L3_x_at_rest(self):
        '''Обнуление'''
        self.DataPult['j2-val-x'] = 0
        if self.telemetria:
            print('right')

    def on_R3_up(self, value):
        '''Вперед'''
        if self.nitro:
            self.DataPult['j1-val-y'] = -1*  value 
        else:
            self.DataPult['j1-val-y'] = -1 * value // 2
        if self.telemetria:
            print('up')

    def on_R3_down(self, value):
        '''назад'''
        if self.nitro:
            self.DataPult['j1-val-y'] = -1* value 
        else:
            self.DataPult['j1-val-y'] = -1 * value // 2
        if self.telemetria:
            print('down')

    def on_R3_y_at_rest(self):
        '''Обнуление'''
        self.DataPult['j1-val-y'] = 0
        if self.telemetria:
            print('down')

    def on_R3_left(self, value):
        '''Разворот налево'''
        if self.nitro:
            self.DataPult['j1-val-x'] =  value // 3
        else:
            self.DataPult['j1-val-x'] = value // 6
        if self.telemetria:
            print('turn-left')

    def on_R3_right(self, value):
        '''Разворот направо'''
        if self.nitro:
            self.DataPult['j1-val-x'] =  value // 3
        else:
            self.DataPult['j1-val-x'] = value // 6
        if self.telemetria:
            print('turn-left')

    def on_R3_x_at_rest(self):
        '''Обнуление'''
        self.DataPult['j1-val-x'] = 0
        if self.telemetria:
            print('turn-left')

    # блок внесения корректировок с кнопок и управления светом, поворотом камеры, манипулятором
    def on_x_press(self):
        '''Нажатие на крестик'''
        if self.optionscontrol:
            if self.DataPult['ry-cor'] >= - 50:
                self.DataPult['ry-cor'] -= 10
        else:
            if self.DataPult['servoCam'] <= 170:
                self.DataPult['servoCam'] += 10

    def on_triangle_press(self):
        '''Нажатие на триугольник'''
        if self.optionscontrol:
            if self.DataPult['ry-cor'] <= 50:
                self.DataPult['ry-cor'] += 10
        else:
            if self.DataPult['servoCam'] >= 10:
                self.DataPult['servoCam'] -= 10

    def on_square_press(self):
        '''Нажатие на круг'''
        if self.optionscontrol:
            if self.DataPult['rx-cor'] <= 50:
                self.DataPult['rx-cor'] += 10
        else:
            if self.DataPult['man'] <= 150:
                self.DataPult['man'] += 20

    def on_circle_press(self):
        '''Нажатие на квадрат'''
        if self.optionscontrol:
            if self.DataPult['rx-cor'] >= -50:
                self.DataPult['rx-cor'] -= 10
        else:
            if self.DataPult['man'] >= 40:
                self.DataPult['man'] -= 20

    def on_up_arrow_press(self):
        if self.optionscontrol:
            if self.DataPult['ly-cor'] >= -50:
                self.DataPult['ly-cor'] -= 10
        else:
            self.DataPult['led'] = not self.DataPult['led']

    def on_down_arrow_press(self):
        if self.optionscontrol:
            if self.DataPult['ly-cor'] <= 50:
                self.DataPult['ly-cor'] += 10
        else:
            self.DataPult['auto-dept'] = not self.DataPult['auto-dept']

    def on_left_arrow_press(self):
        if self.optionscontrol:
            if self.DataPult["lx-cor"] >= -50:
                self.DataPult["lx-cor"] -= 10
        else:
            self.nitro = not self.nitro

    def on_right_arrow_press(self):
        if self.optionscontrol:
            if self.DataPult['lx-cor'] <= 50:
                self.DataPult['lx-cor'] += 10

    def on_playstation_button_press(self):
        '''Отмена всех корректировок'''
        self.DataPult['ly-cor'] = 0
        self.DataPult['lx-cor'] = 0
        self.DataPult['rx-cor'] = 0
        self.DataPult['ry-cor'] = 0
        '''Приведение всех значений в исходное положение'''
        self.DataPult['auto-dept'] = False
        self.DataPult['servoCam'] = 90
        self.DataPult['man'] = 90
        self.DataPult['led'] = False
        self.nitro = False


class MainPost:
    def __init__(self):
        # словарик для отправки на аппарат
        self.DataOutput = {'time': None,  # Текущее время
                           'motorpowervalue': 1,  # мощность моторов
                           'led': False,  # управление светом
                           'man': 90,  # Управление манипулятором
                           'servoCam': 90,  # управление наклоном камеры
                           'motor0': 0, 'motor1': 0,  # значения мощности на каждый мотор
                           'motor2': 0, 'motor3': 0,
                           'motor4': 0, 'motor5': 0}
        # словарик получаемый с аппарата
        self.DataInput = {'time': None, 'dept': None,
                          'volt': None, 'azimut': None}
        self.lodi = MedaLogging()

        self.Server = ServerMainPult(self.lodi, DEBUG)  # поднимаем сервер
        #self.lodi.info('ServerMainPult - init')

        self.Controllps4 = MyController()  # поднимаем контролеер
        #self.lodi.info('MyController - init')
        self.DataPult = self.Controllps4.DataPult

        self.RateCommandOut = 0.2
        self.telemetria = False
        self.checkKILL = False
        self.correctCom = True

        self.lodi.info('MainPost-init')

    def RunController(self):
        '''запуск на прослушивание контроллера ps4'''
        # self.lodi.info('MyController-listen')
        self.Controllps4.listen()

    def RunCam(self):
        '''Запуск скрипта отвечающего за трансляцию видео потока'''
        os.system('/bin/python3 /home/proteus/SoftProteus-2.0/cam/udp_server.py')

    def RunCommand(self, CmdMod = True):
        self.lodi.info('MainPost-RunCommand')
        '''
        Движение вперед - (1 вперед 2 вперед 3 назад 4 назад) 
        Движение назад - (1 назад 2 назад 3 вперед 4 вперед)
        Движение лагом вправо - (1 назад 2 вперед 3 вперед 4 назад)
        Движение лагом влево - (1 вперед 2 назад 3 назад 4 вперед)
        Движение вверх - (5 вниз 6 вниз)
        Движение вниз - (5 вверх 6 вверх)
        '''
        def transformation(value: int):
            # Функция перевода значений АЦП с джойстика в проценты
            value = (32768 - value) // 655
            return value

        def defense(value: int):
            '''Функция защитник от некорректных данных'''
            if value > 100:
                value = 100
            elif value < 0:
                value = 0
            return value

        while True:
            # запрос данный из класса пульта (потенциально слабое место)
            data = self.DataPult

            # математика преобразования значений с джойстика в значения для моторов
            if self.telemetria:
                self.lodi.debug(f'DataPult - {data}')

            if self.correctCom:
                J1_Val_Y = transformation(data['j1-val-y']) + data['ly-cor']
                J1_Val_X = transformation(data['j1-val-x']) + data['lx-cor']
                J2_Val_Y = transformation(data['j2-val-y']) + data['ry-cor']
                J2_Val_X = transformation(data['j2-val-x']) + data['lx-cor']
            else:
                J1_Val_Y = transformation(data['j1-val-y'])
                J1_Val_X = transformation(data['j1-val-x'])
                J2_Val_Y = transformation(data['j2-val-y'])
                J2_Val_X = transformation(data['j2-val-x'])

            self.DataOutput['motor0'] = defense(
                J1_Val_Y + J1_Val_X + J2_Val_X - 100)
            self.DataOutput['motor1'] = defense(
                J1_Val_Y - J1_Val_X - J2_Val_X + 100)
            self.DataOutput['motor2'] = defense(
                (-1 * J1_Val_Y) - J1_Val_X + J2_Val_X + 100)
            self.DataOutput['motor3'] = defense(
                (-1 * J1_Val_Y) + J1_Val_X - J2_Val_X + 100)
            # Подготовка массива для отправки на аппарат
            self.DataOutput['motor4'] = defense(J2_Val_Y)
            self.DataOutput['motor5'] = defense(J2_Val_Y)

            self.DataOutput["time"] = str(datetime.now())

            self.DataOutput['led'] = data['led']
            self.DataOutput['man'] = data['man']
            self.DataOutput['servoCam'] = data['servoCam']
            # Запись управляющего массива в лог 
            if self.telemetria:
                self.lodi.debug('DataOutput - {self.DataOutput}')
            # отправка и прием сообщений
            self.Server.ControlProteus(self.DataOutput)
            self.DataInput = self.Server.ReceiverProteus()
            # Запись принятого массива в лог 
            if self.telemetria:
                self.lodi.debug('DataInput - {self.DataInput}')
            # возможность вывода принимаемой информации в соммандную строку
            if CmdMod:
                print(self.DataInput)
            # Проверка условия убийства сокета 
            if self.checkKILL:
                self.Server.server.close()
                self.lodi.info('command-stop')
                break

            sleep(self.RateCommandOut)
    '''
    def CommandLine(self):
        while True:
            command = input()  # ввод с клавиатуры
            if command == 'stop':
                self.checkKILL = True
                self.Controllps4.cilled()
                break
    '''
    
    def RunMain(self):
        self.ThreadJoi = threading.Thread(target=self.RunController)
        self.ThreadCom = threading.Thread(target=self.RunCommand)
        #self.ThreadComLine = threading.Thread(target=self.CommandLine)

        self.ThreadJoi.start()
        self.ThreadCom.start()
        #self.ThreadComLine.start()



if __name__ == '__main__':
    post = MainPost()
    post.RunMain()
