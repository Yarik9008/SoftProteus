import socket
import threading  # модуль для разделения на потоки
import logging
import coloredlogs
import os
from datetime import datetime  # получение  времени
from time import sleep  # сон
from ast import literal_eval  # модуль для перевода строки в словарик
from pyPS4Controller.controller import Controller
from keyboard import wait, on_release_key, on_press_key


class MedaLogging:
    '''Класс отвечающий за логирование. Логи пишуться в файл, так же выводться в консоль'''

    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        name = '0.2 GUI/logs/' + '-'.join('-'.join('-'.join(str(datetime.now()
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


class ServerPult:
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
            self.PORT = 1115
        else:
            self.HOST = '192.168.1.107'
            self.PORT = 1236
        # настройка сервера
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        print(self.HOST, self.PORT)
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

        self.deli = [1, 1, 1, 1]
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
        self.DataPult['j2-val-y'] = value / self.deli[1]
        if self.telemetria:
            print('forward')

    def on_L3_down(self, value):
        '''всплытие'''
        self.DataPult['j2-val-y'] = value / self.deli[1]
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
            self.DataPult['j2-val-x'] = value
        else:
            self.DataPult['j2-val-x'] = value // self.deli[0]
        if self.telemetria:
            print('left')

    def on_L3_right(self, value):
        '''Движение вправо (лаг) '''
        if self.nitro:
            self.DataPult['j2-val-x'] = value
        else:
            self.DataPult['j2-val-x'] = value // self.deli[0]
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
            self.DataPult['j1-val-y'] = -1 * value
        else:
            self.DataPult['j1-val-y'] = -1 * value // self.deli[3]
        if self.telemetria:
            print('up')

    def on_R3_down(self, value):
        '''назад'''
        if self.nitro:
            self.DataPult['j1-val-y'] = -1 * value
        else:
            self.DataPult['j1-val-y'] = -1 * value // self.deli[3]
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
            self.DataPult['j1-val-x'] = value // 3
        else:
            self.DataPult['j1-val-x'] = value // self.deli[2]
        if self.telemetria:
            print('turn-left')

    def on_R3_right(self, value):
        '''Разворот направо'''
        if self.nitro:
            self.DataPult['j1-val-x'] = value // 3
        else:
            self.DataPult['j1-val-x'] = value // self.deli[2]
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


class MyControllerKeyboard:
    '''
    Класс для резервного управления ROV с помощью клавиатуры ноутбука 
    вперед - w
    назад - s
    вправо - a
    влево - d
    вверх - up
    вниз - down  
    поворот влево - left
    поворот направо - right
    '''

    def __init__(self):
        self.DataPult = {'j1-val-y': 0, 'j1-val-x': 0,
                         'j2-val-y': 0, 'j2-val-x': 0,
                         'ly-cor': 0, 'lx-cor': 0,
                         'ry-cor': 0, 'rx-cor': 0,
                         'man': 90, 'servoCam': 90,
                         'led': False, 'auto-dept': False}
        self.log = True
        self.telemetria = True
        self.optionscontrol = False
        self.nitro = False

    def mainKeyboard(self):
        on_press_key('w', self.forward, suppress=False)
        on_release_key('w', self.forward_release, suppress=False)
        on_press_key('s', self.back, suppress=False)
        on_release_key('s', self.back_release, suppress=False)
        on_press_key('a', self.left, suppress=False)
        on_release_key('a', self.left_relaese, suppress=False)
        on_press_key('d', self.right, suppress=False)
        on_release_key('d', self.right_relaese, suppress=False)
        on_press_key('up', self.up, suppress=False)
        on_release_key('up', self.up_relaese, suppress=False)
        on_press_key('down', self.down, suppress=False)
        on_release_key('down', self.down_relaese, suppress=False)
        on_press_key('left', self.turn_left, suppress=False)
        on_release_key('left', self.turn_left_relaese, suppress=False)
        on_press_key('right', self.turn_right, suppress=False)
        on_release_key('right', self.turn_right_relaese, suppress=False)
        wait()

    def forward(self, key):
        self.DataPult['j1-val-y'] = 32767
        if self.telemetria:
            print('forward')

    def forward_release(self, key):
        self.DataPult['j1-val-y'] = 0
        if self.telemetria:
            print('forward-stop')

    def back(self, key):
        self.DataPult['j1-val-y'] = -327672

        if self.telemetria:
            print('back')

    def back_release(self, key):
        self.DataPult['j1-val-y'] = 0
        if self.telemetria:
            print('back-relaese')

    def left(self, key):
        self.DataPult['j1-val-x'] = -32767

        if self.telemetria:
            print('left')

    def left_relaese(self, key):
        self.DataPult['j1-val-x'] = 0
        if self.telemetria:
            print('left_relaese')

    def right(self, key):
        self.DataPult['j1-val-x'] = 32767

        if self.telemetria:
            print('right')

    def right_relaese(self, key):
        self.DataPult['j1-val-x'] = 0
        if self.telemetria:
            print('right-relaese')

    def up(self, key):
        self.DataPult['j2-val-y'] = 32767

        if self.telemetria:
            print('up')

    def up_relaese(self, key):
        self.DataPult['j2-val-y'] = 0
        if self.telemetria:
            print('up-relaese')

    def down(self, key):
        self.DataPult['j2-val-y'] = -32767

        if self.telemetria:
            print('down')

    def down_relaese(self, key):
        self.DataPult['j2-val-y'] = 0
        if self.telemetria:
            print('down-relaese')

    def turn_left(self, key):
        self.DataPult['j2-val-x'] = -32767
        if self.telemetria:
            print('turn-left')

    def turn_left_relaese(self, key):
        self.DataPult['j2-val-x'] = 0
        if self.telemetria:
            print('turn-stop')

    def turn_right(self, key):
        self.DataPult['j2-val-x'] = 32767
        if self.telemetria:
            print('turn-right')

    def turn_right_relaese(self, key):
        self.DataPult['j2-val-x'] = 0
        if self.telemetria:
            print('turn-stop')
