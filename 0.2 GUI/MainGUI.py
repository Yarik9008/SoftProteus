from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QButtonGroup
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QIcon, QPixmap
import keyboard
from Server import *
from Design import *
import threading
import sys
import sqlite3


DEBUG = False


class ThreadServer(QtCore.QObject):
    commandserver = QtCore.pyqtSignal(dict)

    def __init__(self, hostmod):
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

        self.deli = [1, 1, 1, 1]
        self.lodi = MedaLogging()
        
        
        self.Server = ServerPult(self.lodi, hostmod)  # поднимаем сервер
        #self.lodi.info('ServerMainPult - init')

        self.keboardjoi = MyControllerKeyboard()
        self.DataPult = self.keboardjoi.DataPult

        self.Controllps4 = MyController()  # поднимаем контролеер
        self.DataPult = self.Controllps4.DataPult
        self.Controllps4.deli = self.deli

        self.RateCommandOut = 0.2
        self.telemetria = False
        self.cmdMod = False
        self.checkKILL = False
        self.correctCom = True

        self.lodi.info('MainPost-init')

    def RunController(self):
        '''запуск на прослушивание контроллера ps4'''
        self.lodi.info('MyController-listen')
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

            QtCore.QThread.msleep(250)


class ApplicationGUI(QMainWindow, Ui_SoftProteus_2_0):
    def __init__(self):
        # импорт и создание интерфейса
        super().__init__()
        self.setupUi(self)

        self.check_connect = False
        self.modeHost = 'local'
        self.mode = 'work'
        # создание обьекта для работы с базой данных 
        self.db = MedaSQL()
        ### изначальное обнуление всех иконок ###
        self.lineEdit.returnPressed.connect(self.append_text)


        self.progressBar.setValue(0)
        self.Camera.setEnabled(False)
        self.Connect.setEnabled(False)
        self.Joystick.setEnabled(False)
        self.HOST_Edit.setEnabled(False)
        self.PORT_Edit.setEnabled(False)

        self.doubleSpinBox.setMinimum(1.0)
        self.doubleSpinBox.setMaximum(10.0)
        self.doubleSpinBox.setSingleStep(0.2)

        self.doubleSpinBox_2.setMinimum(1.0)
        self.doubleSpinBox_2.setMaximum(10.0)
        self.doubleSpinBox_2.setSingleStep(0.2)

        self.doubleSpinBox_3.setMinimum(1.0)
        self.doubleSpinBox_3.setMaximum(10.0)
        self.doubleSpinBox_3.setSingleStep(0.2)

        self.doubleSpinBox_4.setMinimum(1.0)
        self.doubleSpinBox_4.setMaximum(10.0)
        self.doubleSpinBox_4.setSingleStep(0.2)

        self.modehostgropp = QButtonGroup()
        self.modehostgropp.addButton(self.RealHost)
        self.modehostgropp.addButton(self.LocalHost)
        self.LocalHost.setChecked(True)
        self.HOST_Edit.setText('127.0.0.1')
        self.PORT_Edit.setText('1111')
        self.RealHost.toggled.connect(lambda: self.host_state(self.RealHost))
        self.LocalHost.toggled.connect(lambda: self.host_state(self.LocalHost))

        self.modecommandgropp = QButtonGroup()
        self.modecommandgropp.addButton(self.Keyboard)
        self.modecommandgropp.addButton(self.Joistik)
        self.Keyboard.toggled.connect(lambda: self.command_state(self.Keyboard))
        self.Joistik.toggled.connect(lambda: self.command_state(self.Joistik))
        #self.Keyboard.setChecked(True)


        self.modegropp = QButtonGroup()
        self.Work.setChecked(True)
        self.modegropp.addButton(self.min)
        self.modegropp.addButton(self.Work)
        self.modegropp.addButton(self.Nitro)
        self.min.toggled.connect(lambda: self.mode_state(self.min))
        self.Work.toggled.connect(lambda: self.mode_state(self.Work))
        self.Nitro.toggled.connect(lambda: self.mode_state(self.Nitro))

        self.SaveSettings.clicked.connect(self.save_mode)
        self.ReadSettings.clicked.connect(self.read_mode)
        
        self.textBrowser_2.setTextColor(QColor(0, 255, 0))
        self.textBrowser.setTextColor(QColor(0, 255, 0))
        self.textBrowser.append('### Start Programm ###')
        self.Connect_2.clicked.connect(self.start_server)

        ### создание потоков и привязка ###
        self.thread = QtCore.QThread()
        
    def read_mode(self):
        mass = self.db.request_mode(self.mode)
        self.doubleSpinBox_2.setValue(mass[0])
        self.doubleSpinBox_3.setValue(mass[1])
        self.doubleSpinBox.setValue(mass[2])
        self.doubleSpinBox_4.setValue(mass[3])
        
    def save_mode(self):
        lx = self.doubleSpinBox_2.value()
        ly = self.doubleSpinBox_3.value()
        rx = self.doubleSpinBox.value()
        ry = self.doubleSpinBox_4.value()
        self.db.modification_mode(self.mode,[lx,ly,rx,ry])

    def mode_state(self,mode):
        #print(mode.text())
        if mode.text() == 'Min ' and mode.isChecked():
            self.threadserver.deli = self.db.request_mode('min')
            self.mode = 'min'
        elif mode.text() == 'Work'and mode.isChecked():
            self.threadserver.deli = self.db.request_mode('work')
            self.mode = 'work'
        elif mode.text() == 'Nitro' and mode.isChecked():
            self.threadserver.deli = self.db.request_mode('nitro')
            self.mode = 'nitro'
            

    def command_state(self, mode):
        if mode.text() == "Keyboard" and mode.isChecked():
            self.textBrowser.append('### start-keyboard ###')
            self.start_keyboard()
        elif mode.text() == "Joistik" and mode.isChecked():
            self.textBrowser.append('### start-joistik ###')
            self.start_joi()

    def host_state(self, mode):
        if mode.text() == "LocalHost" and mode.isChecked():
            self.HOST_Edit.setText('127.0.0.1')
            self.PORT_Edit.setText('1111')
            self.modeHost = 'local'
            self.textBrowser.append(f'Host mode: lokal "127.0.0.1:1115"')

        elif mode.text() == "RealHost" and mode.isChecked():
            self.HOST_Edit.setText('192.168.1.107')
            self.PORT_Edit.setText('1235')
            self.modeHost = 'real'
            self.textBrowser.append(f'Host mode: real "192.168.1.107:1235"')

    def append_text(self):
        # блок ответсвенный за работу с "коммандной строкой для управления аппаратом"
        # список доступных комманд с описание см в README.md
        text = str(self.lineEdit.text())
        self.textBrowser.setTextColor(QColor(0, 255, 0))

        if text.lower() == 'close':
            self.close()
        elif text.lower() == 'version':
            # сообщение отладочного уровня отображаются синим цветом
            text = 'Soft-Proteus version: 0.2'
            self.textBrowser.setTextColor(QColor(0, 0, 255))
        else:
            # сообщения ошибочного уровня отображаются красным цветом
            self.textBrowser.setTextColor(QColor(255, 0, 0))
            text = f'Command not found: "{text}"'
        # TODO дописать несколько комманд для управления аппаратом

        # добавление комманды в окно отображение комманд
        self.textBrowser.append(text)
        self.lineEdit.clear()

    def start_server(self):
        # запуск сервера
        self.check_connect = True
        self.threadserver = ThreadServer(self.modeHost)
        self.threadserver.moveToThread(self.thread)
        self.threadserver.commandserver.connect(self.updategui)
        self.thread.started.connect(self.threadserver.run)
        self.textBrowser.append('### Connecting ###')
        self.thread.start()

    def start_joi(self):
        self.threadJoi = threading.Thread(
            target=self.threadserver.RunController)
        self.threadJoi.start()
 
    def start_keyboard(self):
        self.threadKey = threading.Thread(
        target = self.threadserver.keboardjoi.mainKeyboard)
        self.threadKey.start()


    def closeEvent(self, e):
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
        self.progressBar.setProperty("value", int(dataMass['charg']))


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
