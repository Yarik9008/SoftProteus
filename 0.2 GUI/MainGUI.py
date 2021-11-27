from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QIcon, QPixmap
import keyboard
from Server import *
from Design import *
import threading
import sys


DEBUG = True
KEYBOARD = False

class ThreadServer(QtCore.QObject):
    commandserver = QtCore.pyqtSignal(dict)
    
    
    def __init__(self):
        super().__init__()
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
        
        self.deli = [1,1,1,1]
        self.lodi = MedaLogging()

        self.Server = ServerPult(self.lodi, DEBUG)  # поднимаем сервер
        #self.lodi.info('ServerMainPult - init')
        if KEYBOARD:
            self.keboar = MyControllerKeyboard()
            self.DataPult = self.keboar.DataPult
        else:
            self.Controllps4 = MyController()  # поднимаем контролеер
            #self.lodi.info('MyController - init')
            self.DataPult = self.Controllps4.DataPult
            self.Controllps4.deli = self.deli

        self.RateCommandOut = 0.2
        self.telemetria = False
        self.cmdMod = False
        self.checkKILL = False
        self.correctCom = True

        self.lodi.info('MainPost-init')
        

        

    def RunController(self):
        if KEYBOARD:
            self.keboar.wait()
        '''запуск на прослушивание контроллера ps4'''
        # self.lodi.info('MyController-listen')
        self.Controllps4.listen()

    def run(self):
        # основной цикл программы 
        self.lodi.info('MainPost-RunCommand')
        
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
            datagui = self.DataInput
            datagui['log'] = self.DataOutput
            self.commandserver.emit(self.DataInput)
            
            # Запись принятого массива в лог
            if self.telemetria:
                self.lodi.debug('DataInput - {self.DataInput}')
            # возможность вывода принимаемой информации в соммандную строку
            if self.cmdMod:
                print(self.DataInput)
            # Проверка условия убийства сокета
            if self.checkKILL:
                self.Server.server.close()
                self.lodi.info('command-stop')
                break
            
            QtCore.QThread.msleep(1000)


class ApplicationGUI(QMainWindow, Ui_SoftProteus_2_0):
    def __init__(self):
        # импорт и создание интерфейса
        super().__init__()
        self.setupUi(self)
        
        self.check_connect = False
        
        ### изначальное обнуление всех иконок ###
        self.lineEdit.returnPressed.connect(self.append_text)
        
        
        
        pixmap = QPixmap('urc.png')
        self.logo.setPixmap(pixmap)
        self.progressBar.setValue(0)
        self.Camera.setEnabled(False)
        self.Connect.setEnabled(False)
        self.Joystick.setEnabled(False)
        self.textBrowser_2.setTextColor(QColor(0, 255, 0))
        self.textBrowser.setTextColor(QColor(0, 255, 0))
        self.textBrowser.append('### Start Programm ###')
        self.Connect_2.clicked.connect(self.start_server)
        
        ### создание потоков и привязка ###
        self.thread = QtCore.QThread()
        
    def append_text(self):
        text = self.lineEdit.text()
        self.textBrowser.append(text)
        self.lineEdit.clear()
    
    def start_server(self):
        # запуск сервера
        self.threadserver = ThreadServer()
        self.threadserver.moveToThread(self.thread)
        self.threadserver.commandserver.connect(self.updategui)
        self.thread.started.connect(self.threadserver.run)
        self.textBrowser.append('### Connecting ###')
        ### запуск джойстика ####
        self.threadJoi = threading.Thread(target=self.threadserver.RunController)
        self.threadJoi.start()
        self.thread.start()
        

    def closeEvent(self,e):
        # диалоговое окошко закрытия 
        result = QtWidgets.QMessageBox.question(self, "Подтверждение закрытия окна",
                                                "Вы действительно хотите закрыть окно?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            e.accept()
            QtWidgets.QWidget.closeEvent(self, e)
        else:
            e.ignore()

    @QtCore.pyqtSlot(dict)
    def updategui(self, dataMass):
        if not self.check_connect:
            self.check_connect = True
            self.textBrowser.append('### ROV Connected ###')
        # обновление интерфейса а также вывод в логи к кмд  
        self.lcdNumber.display(dataMass['term'])
        self.lcdNumber_2.display(dataMass['azim'])
        self.lcdNumber_3.display(dataMass['dept'])
        self.textBrowser_2.append(str(dataMass['log']))




class MainPost:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ex = ApplicationGUI()

    def ShowApplication(self):
        self.ex.show()
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    application = MainPost()
    application.ShowApplication()
