import socket
import logging
import coloredlogs
from datetime import datetime
from ast import literal_eval


class MedaLogging:
    '''Класс отвечающий за логирование. Логи пишуться в файл, так же выводться в консоль'''
    def __init__(self):
        self.mylogs = logging.getLogger(__name__)
        self.mylogs.setLevel(logging.DEBUG)
        # обработчик записи в лог-файл
        name = '-'.join('-'.join('-'.join(str(datetime.now()
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


class ServerMain:
    def __init__(self, HOST: str, PORT: int, logger: MedaLogging, DEBUG:bool=False):
        # инициализация атрибутов
        self.telemetria = False
        self.checkConnect = False
        self.logger = logger
        self.HOST = HOST
        self.PORT = PORT
        self.DEBUG = DEBUG

        # настройка сервера
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.server.bind((self.HOST, self.PORT))
        # сколько клиентов могут подключиться к серверу
        self.server.listen(1)
        self.user_socket, self.address = self.server.accept()
        self.checkConnect = True
        if self.DEBUG:
            self.logger.info(f'Client-connected - {self.user_socket}')

    def ServerReceiver(self):
        '''Прием информации с аппарата'''
        if self.checkConnect:
            # сколько информации в байтах можем принять
            data = self.user_socket.recv(512)
            if len(data) == 0:
                self.server.close()
                self.checkConnect = False
                self.logger.info(f'Client-disconnection - {self.user_socket}')
                return None

            data = dict(literal_eval(str(data.decode('utf-8'))))
            if self.DEBUG:
                self.logger.debug(f'DataInput - {str(data)}')
            return data

    def ServerControl(self, data: dict):
        '''Отправка массива на аппарат'''
        if self.checkConnect:
            self.user_socket.send(str(data).encode('utf-8'))
            if self.DEBUG:
                self.logger.debug(str(data))


class ClientMain:
    # Класс ответсвенный за связь с постом
    def __init__(self, HOST: str, PORT: int, logger: MedaLogging, DEBUG:bool = False):
        self.logger = logger
        self.HOST = HOST
        self.PORT = PORT
        self.checkConnect = True
        self.DEBUG = DEBUG
        # Настройки клиента
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM,)
        self.client.connect((self.HOST, self.PORT))  # подключение адресс  порт

    def ClientDispatch(self, data: dict):
        # Функция для  отправки пакетов на пульт
        if self.checkConnect:
            data['time'] = str(datetime.now())
            if self.DEBUG:
                self.logger.debug(str(data))
            DataOutput = str(data).encode('utf-8')
            self.client.send(DataOutput)

    def ClientReceivin(self):
        # Прием информации с поста управления
        if self.checkConnect:
            data = self.client.recv(512).decode('utf-8')
            if len(data) == 0:
                self.checkConnect = False
                
                self.logger.info('Client-disconect')
                self.client.close()
                return None
            data = dict(literal_eval(str(data)))
            if self.DEBUG:
                self.logger.debug(str(data))
            return data
