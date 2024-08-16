from PyQt6.QtCore import pyqtSignal, Qt, QThread, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QComboBox, QMessageBox, QRadioButton, \
    QVBoxLayout
from PyQt6 import QtCore, QtGui, QtWidgets
import sys
import threading

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from models import *
from communication import *

#定义主窗口
class mainWindow(QMainWindow):
    #初始化
    def __init__(self,hexapod:Hexapod,ser:Serial,blt:Bluetooth):
        super().__init__()
        #串口线程
        self.SERthread = SERIALThread(ser)
        self.SERthread.start()
        #蓝牙线程
        self.BLTthread = BLTThread(blt)
        self.BLTthread.start()

        #初始化主窗口页面
        self.init_UI(hexapod)
        #菜单信号
        self.actionbody.triggered.connect(lambda: self.myWidget1.show_widget(hexapod))
        self.actionleg.triggered.connect(lambda: self.myWidget2.show_widget(hexapod))
        self.actionserial.triggered.connect(lambda: self.myWidget3.show_widget())
        self.actionbluetooth.triggered.connect(lambda: self.myWidget4.show_widget())
        #界面同步信号
        self.myWidget1.update_body_aignal.connect(lambda: self.mainWidget.init_control(hexapod))
        self.myWidget2.update_leg_aignal.connect(lambda: self.mainWidget.init_control(hexapod))
        #加载qss
        # with open("style/Aqua.qss", "r") as file:
        #     self.setStyleSheet(file.read())
        #显示窗口
        self.show()
    #初始化界面
    def init_UI(self, hexapod:Hexapod):
        self.setObjectName("mainWindow")
        self.setFixedSize(900, 640)
        #子窗口创建
        self.myWidget1 = myWidget1(hexapod)
        self.myWidget2 = myWidget2(hexapod)
        self.myWidget3 = myWidget3(self.SERthread)
        self.myWidget4 = myWidget4(self.BLTthread)
        #菜单棒设置
        self.menubar = QtWidgets.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 747, 22))
        self.menubar.setObjectName("menubar")
        #菜单选项1设置
        self.menu = QtWidgets.QMenu(parent=self)
        self.menu.setObjectName("menu")
        self.actionbody = QtGui.QAction(parent=self)
        self.actionbody.setObjectName("actionbody")
        self.actionleg = QtGui.QAction(parent=self)
        self.actionleg.setObjectName("actionleg")
        self.menu.addAction(self.actionbody)
        self.menu.addAction(self.actionleg)
        self.menubar.addAction(self.menu.menuAction())
        # 菜单选项2设置
        self.menu_2 = QtWidgets.QMenu(parent=self.menubar)
        self.menu_2.setObjectName("menu_2")
        self.actionserial = QtGui.QAction(parent=self)
        self.actionserial.setObjectName("actionserial")
        self.actionbluetooth = QtGui.QAction(parent=self)
        self.actionbluetooth.setObjectName("actionbluetooth")
        self.menu_2.addAction(self.actionserial)
        self.menu_2.addAction(self.actionbluetooth)
        self.menubar.addAction(self.menu_2.menuAction())
        #主窗口创建
        self.mainWidget = mainWidget(self.SERthread,self.BLTthread,hexapod)
        self.setCentralWidget(self.mainWidget)

        self.setMenuBar(self.menubar)
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
    #控件属性定义
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "六足机器人控制界面"))
        self.menu.setTitle(_translate("MainWindow", "初始化"))
        self.menu_2.setTitle(_translate("MainWindow", "通信连接"))
        self.actionbody.setText(_translate("MainWindow", "body"))
        self.actionleg.setText(_translate("MainWindow", "leg"))
        self.actionserial.setText(_translate("MainWindow", "serial"))
        self.actionbluetooth.setText(_translate("MainWindow", "bluetooth"))

#子类化QComboBox
class myComboBox(QComboBox):
    clicked = pyqtSignal()  # 自定义信号
    def mousePressEvent(self, event):
        self.clicked.emit()  # 触发自定义信号
        super().mousePressEvent(event)  # 确保默认行为仍然发生

#定义串口子线程
class SERIALThread(QThread):
    #定义返回值
    devices_list = pyqtSignal(list)
    connect_res = pyqtSignal(bool)
    disconnect_res = pyqtSignal(bool)
    is_open_signal = pyqtSignal(bool)
    is_receive_signal = pyqtSignal(bool)
    paramters_list = pyqtSignal(tuple)
    send_message = pyqtSignal(str)
    receive_message = pyqtSignal(str)
    #自定义构造函数传参
    def __init__(self, ser:Serial):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.serial = ser
        self.is_send = True
        self.is_receive = False
    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main_loop())
    #监听循环
    async def main_loop(self):
        while True:
            if self.is_receive and self.serial.is_open:
                await self.receive_data()
            await asyncio.sleep(0.1)
    #扫描可用串口
    async def scan(self):
        devices = await asyncio.to_thread(self.serial.select_com)
        self.devices_list.emit(devices)
    #连接串口
    async def connect_ser(self):
        is_open = await asyncio.to_thread(self.serial.open_serial)
        self.connect_res.emit(is_open)
    #断开串口
    async def disconnect_ser(self):
        await asyncio.to_thread(self.serial.close_serial)
        self.disconnect_res.emit(self.serial.is_open)
    #读取连接状态
    async def read_is_open(self):
        self.is_open_signal.emit(self.serial.is_open)
    #读取是否接收信息
    async def read_is_receive(self):
        self.is_receive_signal.emit(self.is_receive)
    # 停止发送
    async def stop_send(self):
        self.is_send = False
        await asyncio.sleep(1)
        self.is_send = True
    #修改接收状态
    async def update_is_receive(self,is_receive):
        self.is_receive = is_receive
    #修改参数
    async def update_paramters(self,paramters):
        await asyncio.to_thread(self.serial.update_paramters,paramters)
    #获取参数
    async def get_paramters(self):
        paramters = await asyncio.to_thread(self.serial.get_paramters)
        self.paramters_list.emit(paramters)
    #发送信息
    async def send_data(self,data):
        if self.is_send:
            await asyncio.to_thread(self.serial.send_info,data)
            data = self.serial.name + ':' + data
            self.send_message.emit(data)
    #接收信息
    async def receive_data(self):
        data = await asyncio.to_thread(self.serial.receive_data)
        if data != None:
            data = self.serial.name + ':' + data
            self.receive_message.emit(data)
    #发送coding
    async def send_coding(self,coding):
        for item in coding:
            if self.is_send:
                string, time = item
                await self.send_data(string)
                await asyncio.sleep(time)

#定义蓝牙子线程
class BLTThread(QThread):
    #定义返回值
    devices_list = pyqtSignal(list)
    connect_res = pyqtSignal(bool)
    disconnect_res = pyqtSignal(bool)
    uuid_list = pyqtSignal(tuple)
    is_open_signal = pyqtSignal(bool)
    is_receive_signal = pyqtSignal(bool)
    send_message = pyqtSignal(str)
    receive_message = pyqtSignal(str)
    #自定义构造函数传参
    def __init__(self, blt:Bluetooth):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.bluetooth = blt
        self.is_send = True
        self.is_receive = False
    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main_loop())
    # 监听循环
    async def main_loop(self):
        while True:
            if self.is_receive and self.bluetooth.is_open:
                await self.receive_data()
            await asyncio.sleep(0.1)
    #扫描可用蓝牙
    async def scan(self):
        devices = await self.bluetooth.search_devices()
        self.devices_list.emit(devices)
    #连接蓝牙
    async def connect_blt(self,address):
        await self.bluetooth.connect(address)
        self.connect_res.emit(self.bluetooth.is_open)
    #断开蓝牙
    async def disconnect_blt(self):
        await self.bluetooth.disconnect()
        self.disconnect_res.emit(self.bluetooth.is_open)
    #读取uuid
    async def read_uuid(self):
        self.uuid_list.emit((self.bluetooth.send_uuid,self.bluetooth.receive_uuid))
    #读取连接状态
    async def read_is_open(self):
        self.is_open_signal.emit(self.bluetooth.is_open)
    # 读取是否接收信息
    async def read_is_receive(self):
        self.is_receive_signal.emit(self.is_receive)
    # 停止发送
    async def stop_send(self):
        self.is_send = False
        await asyncio.sleep(1)
        self.is_send = True
    # 修改接收状态
    async def update_is_receive(self, is_receive):
        self.is_receive = is_receive
    #修改参数
    async def update_paramters(self,paramters):
        await asyncio.to_thread(self.bluetooth.update_paramters,paramters)
    #修改uuid
    async def update_uuid(self,uuid_list):
        await asyncio.to_thread(self.bluetooth.update_uuid,uuid_list)
    # 发送信息
    async def send_data(self, data):
        if self.is_send:
            await self.bluetooth.send(data)
            data = self.bluetooth.target_name + ':' + data
            self.send_message.emit(data)
    # 接收信息
    async def receive_data(self):
        data = await self.bluetooth.receive()
        number = int.from_bytes(data, byteorder='big')
        if number != 0:
            string = data.decode('utf-8')
            string = self.bluetooth.target_name+':'+string
            self.receive_message.emit(string)
    # 发送coding
    async def send_coding(self, coding):
        for item in coding:
            string, time = item
            num = int((len(string)-2)/15)
            index = 0
            string1 = "{"
            for i in range(num):
                string1 = string1+string[15*i+1:15*(i+1)+1].strip()
                index = index + 1
                if index%6 == 0 or i==num-1:
                    if self.is_send:
                        string1 = string1+"}"
                        await self.send_data(string1)
                        await asyncio.sleep(time)
                        string1 = "{"


#定义绘图子线程
class PlotThread(QThread):
    update_canvas_signal = pyqtSignal()
    def __init__(self, figure, hexapod:Hexapod):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.figure = figure
        self.hexapod = copy.deepcopy(hexapod)
    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    #更新hexapod
    async def update_hexapod(self,hexapod:Hexapod):
        self.hexapod = copy.deepcopy(hexapod)
    #更新canvas
    async def update_canvas(self,send_message):
        sequance = self.hexapod.decoding(send_message)
        new_sequance = []
        for item in sequance:
            leg_name,node_name,angle,time = item
            new_sequance.append((leg_name,node_name,angle))
        self.hexapod.update_angle_sequance(new_sequance)
        self.figure.clear()
        ax = self.figure.add_subplot(projection='3d')
        self.figure, ax = self.hexapod.visualize3d(self.figure, ax)
        self.update_canvas_signal.emit()

#定义mainWidget
class mainWidget(QWidget):
    update_horizontalScrollBar_signal = pyqtSignal()
    #初始化
    def __init__(self,SERthread:SERIALThread,BLTthread:BLTThread,hexapod:Hexapod):
        super().__init__()
        _translate = QtCore.QCoreApplication.translate
        self.init_UI()
        self.serthread = SERthread
        self.bltthread = BLTthread

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout(self.widget1)
        self.layout.addWidget(self.canvas)
        self.plotthread = PlotThread(self.figure,hexapod)
        self.plotthread.start()


        #serthread
        self.serthread.connect_res.connect(self.connect_ser)
        self.serthread.disconnect_res.connect(self.disconnect_ser)
        self.serthread.is_receive_signal.connect(self.update_ser_is_receive)
        self.serthread.send_message.connect(self.textEdit_send_message)
        self.serthread.receive_message.connect(self.textEdit_receive_message)
        self.serthread.send_message.connect(self.send_message_to_plotthread)
        #bltthreat
        self.bltthread.connect_res.connect(self.connect_blt)
        self.bltthread.disconnect_res.connect(self.disconnect_blt)
        self.bltthread.is_receive_signal.connect(self.update_blt_is_receive)
        self.bltthread.send_message.connect(self.textEdit_send_message)
        self.bltthread.receive_message.connect(self.textEdit_receive_message)
        self.bltthread.send_message.connect(self.send_message_to_plotthread)
        #plotthread
        self.plotthread.update_canvas_signal.connect(self.update_canvas)
        #更新horizontalScrollBar
        self.update_horizontalScrollBar_signal.connect(lambda: self.update_horizontalScrollBar(hexapod))
        #radioButton
        self.radioButton.clicked.connect(lambda: self.radioButton_clicked())
        self.radioButton_2.clicked.connect(lambda: self.radioButton_clicked())

        #pushButton
        self.pushButton.clicked.connect(lambda: self.pushButton_send_message(hexapod))
        self.pushButton_2.clicked.connect(lambda: self.pushButton_is_receive())
        self.pushButton_3.clicked.connect(lambda: self.pushButton_clear_send())
        self.pushButton_4.clicked.connect(lambda: self.pushButton_clear_receive())

        #horizontalScrollBar_label
        self.horizontalScrollBar.valueChanged.connect(lambda: self.label_6.setText(str(self.horizontalScrollBar.value())))
        self.horizontalScrollBar_2.valueChanged.connect(lambda: self.label_9.setText(str(self.horizontalScrollBar_2.value())))
        self.horizontalScrollBar_3.valueChanged.connect(lambda: self.label_10.setText(str(self.horizontalScrollBar_3.value())))
        self.horizontalScrollBar_4.valueChanged.connect(lambda: self.label_15.setText(str(self.horizontalScrollBar_4.value())))
        self.horizontalScrollBar_5.valueChanged.connect(lambda: self.label_14.setText(str(self.horizontalScrollBar_5.value())))
        self.horizontalScrollBar_6.valueChanged.connect(lambda: self.label_17.setText(str(self.horizontalScrollBar_6.value())))
        self.horizontalScrollBar_7.valueChanged.connect(lambda: self.label_22.setText(str(self.horizontalScrollBar_7.value())))
        self.horizontalScrollBar_8.valueChanged.connect(lambda: self.label_21.setText(str(self.horizontalScrollBar_8.value())))
        self.horizontalScrollBar_9.valueChanged.connect(lambda: self.label_24.setText(str(self.horizontalScrollBar_9.value())))
        self.horizontalScrollBar_10.valueChanged.connect(lambda: self.label_29.setText(str(self.horizontalScrollBar_10.value())))
        self.horizontalScrollBar_11.valueChanged.connect(lambda: self.label_28.setText(str(self.horizontalScrollBar_11.value())))
        self.horizontalScrollBar_12.valueChanged.connect(lambda: self.label_31.setText(str(self.horizontalScrollBar_12.value())))
        self.horizontalScrollBar_13.valueChanged.connect(lambda: self.label_36.setText(str(self.horizontalScrollBar_13.value())))
        self.horizontalScrollBar_14.valueChanged.connect(lambda: self.label_35.setText(str(self.horizontalScrollBar_14.value())))
        self.horizontalScrollBar_15.valueChanged.connect(lambda: self.label_38.setText(str(self.horizontalScrollBar_15.value())))
        self.horizontalScrollBar_16.valueChanged.connect(lambda: self.label_43.setText(str(self.horizontalScrollBar_16.value())))
        self.horizontalScrollBar_17.valueChanged.connect(lambda: self.label_42.setText(str(self.horizontalScrollBar_17.value())))
        self.horizontalScrollBar_18.valueChanged.connect(lambda: self.label_45.setText(str(self.horizontalScrollBar_18.value())))

        self.horizontalScrollBar.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(3,self.horizontalScrollBar.value(),hexapod))
        self.horizontalScrollBar_2.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(4, self.horizontalScrollBar_2.value(),hexapod))
        self.horizontalScrollBar_3.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(5, self.horizontalScrollBar_3.value(),hexapod))
        self.horizontalScrollBar_4.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(6, self.horizontalScrollBar_4.value(),hexapod))
        self.horizontalScrollBar_5.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(7, self.horizontalScrollBar_5.value(),hexapod))
        self.horizontalScrollBar_6.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(8, self.horizontalScrollBar_6.value(),hexapod))
        self.horizontalScrollBar_7.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(0, self.horizontalScrollBar_7.value(),hexapod))
        self.horizontalScrollBar_8.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(1, self.horizontalScrollBar_8.value(),hexapod))
        self.horizontalScrollBar_9.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(2, self.horizontalScrollBar_9.value(),hexapod))
        self.horizontalScrollBar_10.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(9, self.horizontalScrollBar_10.value(),hexapod))
        self.horizontalScrollBar_11.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(10, self.horizontalScrollBar_11.value(),hexapod))
        self.horizontalScrollBar_12.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(11, self.horizontalScrollBar_12.value(),hexapod))
        self.horizontalScrollBar_13.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(15, self.horizontalScrollBar_13.value(),hexapod))
        self.horizontalScrollBar_14.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(16, self.horizontalScrollBar_14.value(),hexapod))
        self.horizontalScrollBar_15.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(17, self.horizontalScrollBar_15.value(),hexapod))
        self.horizontalScrollBar_16.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(12, self.horizontalScrollBar_16.value(),hexapod))
        self.horizontalScrollBar_17.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(13, self.horizontalScrollBar_17.value(),hexapod))
        self.horizontalScrollBar_18.sliderReleased.connect(lambda: self.send_horizontalScrollBar_angle(14, self.horizontalScrollBar_18.value(),hexapod))
        #姿态控制pushButton
        self.pushButton_5.clicked.connect(lambda: self.sequance_button("forward",hexapod))
        self.pushButton_8.clicked.connect(lambda: self.sequance_button("backend",hexapod))
        self.pushButton_6.clicked.connect(lambda: self.sequance_button("left",hexapod))
        self.pushButton_7.clicked.connect(lambda: self.sequance_button("right",hexapod))
        self.pushButton_11.clicked.connect(lambda: self.sequance_button("up",hexapod))
        self.pushButton_12.clicked.connect(lambda: self.sequance_button("down",hexapod))
        self.pushButton_14.clicked.connect(lambda: self.sequance_button("alpha_sub",hexapod))
        self.pushButton_13.clicked.connect(lambda: self.sequance_button("alpha_plus",hexapod))
        self.pushButton_16.clicked.connect(lambda: self.sequance_button("beta_sub",hexapod))
        self.pushButton_15.clicked.connect(lambda: self.sequance_button("beta_plus",hexapod))
        self.pushButton_18.clicked.connect(lambda: self.sequance_button("gama_sub",hexapod))
        self.pushButton_17.clicked.connect(lambda: self.sequance_button("gama_plus",hexapod))
        #移动控制按钮
        self.pushButton_19.clicked.connect(lambda: self.move_pushButton("forward_move",hexapod))
        self.pushButton_22.clicked.connect(lambda: self.move_pushButton("backend_move", hexapod))
        self.pushButton_20.clicked.connect(lambda: self.move_pushButton("left_turn", hexapod))
        self.pushButton_21.clicked.connect(lambda: self.move_pushButton("right_turn", hexapod))

        #提交按钮
        self.pushButton_9.clicked.connect(lambda: self.submit_pushButton(hexapod))
        #复位按钮
        self.pushButton_10.clicked.connect(lambda: self.reset_pushButton(hexapod))
        self.pushButton_23.clicked.connect(lambda: self.reset_pushButton(hexapod))
        #开始按钮
        self.pushButton_24.clicked.connect(lambda: self.start_pushButton(hexapod))
        #停止按钮
        self.pushButton_25.clicked.connect(lambda: self.stop_pushButton())

        #初始化控件
        self.init_control(hexapod)
        #初始化移动控制
        self.init_move_control()


    #初始化界面
    def init_UI(self):
        self.resize(887, 621)
        #定义frame
        self.frame = QtWidgets.QFrame(self)
        self.frame.setGeometry(QtCore.QRect(10, 10, 871, 601))
        self.frame.setObjectName("frame")
        #定义frame_2
        self.frame_2 = QtWidgets.QFrame(parent=self.frame)
        self.frame_2.setGeometry(QtCore.QRect(0, 0, 361, 311))
        self.frame_2.setObjectName("frame_2")
        #定义widget1
        self.widget1 = QtWidgets.QWidget(parent=self.frame_2)
        self.widget1.setGeometry(QtCore.QRect(0, 0, 361, 291))
        self.widget1.setObjectName("widget")
        #定义label
        self.label = QtWidgets.QLabel(parent=self.frame_2)
        self.label.setGeometry(QtCore.QRect(130, 290, 91, 21))
        self.label.setObjectName("label")
        #定义frame_3
        self.frame_3 = QtWidgets.QFrame(parent=self.frame)
        self.frame_3.setGeometry(QtCore.QRect(370, 0, 491, 311))
        self.frame_3.setObjectName("frame_3")
        #定义textEdit
        self.textEdit = QtWidgets.QTextEdit(parent=self.frame_3)
        self.textEdit.setGeometry(QtCore.QRect(0, 0, 261, 221))
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        #定义textEdit_2
        self.textEdit_2 = QtWidgets.QTextEdit(parent=self.frame_3)
        self.textEdit_2.setGeometry(QtCore.QRect(270, 0, 221, 221))
        self.textEdit_2.setReadOnly(True)
        self.textEdit_2.setObjectName("textEdit_2")
        #定义label_2
        self.label_2 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_2.setGeometry(QtCore.QRect(100, 220, 61, 21))
        self.label_2.setObjectName("label_2")
        #定义label_3
        self.label_3 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_3.setGeometry(QtCore.QRect(360, 220, 61, 21))
        self.label_3.setObjectName("label_3")
        #定义frame_4
        self.frame_4 = QtWidgets.QFrame(parent=self.frame_3)
        self.frame_4.setGeometry(QtCore.QRect(0, 240, 491, 71))
        self.frame_4.setObjectName("frame_4")
        #定义radioButton
        self.radioButton = QtWidgets.QRadioButton(parent=self.frame_4)
        self.radioButton.setGeometry(QtCore.QRect(340, 10, 141, 20))
        self.radioButton.setAutoExclusive(False)
        self.radioButton.setObjectName("radioButton")
        #定义radioButton_2
        self.radioButton_2 = QtWidgets.QRadioButton(parent=self.frame_4)
        self.radioButton_2.setGeometry(QtCore.QRect(340, 30, 141, 31))
        self.radioButton.setAutoExclusive(False)
        self.radioButton_2.setObjectName("radioButton_2")
        #定义lineEdit
        self.lineEdit = QtWidgets.QLineEdit(parent=self.frame_4)
        self.lineEdit.setGeometry(QtCore.QRect(0, 40, 261, 20))
        self.lineEdit.setObjectName("lineEdit")
        #定义pushButton
        self.pushButton = QtWidgets.QPushButton(parent=self.frame_4)
        self.pushButton.setGeometry(QtCore.QRect(270, 40, 51, 24))
        self.pushButton.setObjectName("pushButton")
        #定义pushButton_2
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.frame_4)
        self.pushButton_2.setGeometry(QtCore.QRect(0, 10, 91, 24))
        self.pushButton_2.setObjectName("pushButton_2")
        #定义pushButton_3
        self.pushButton_3 = QtWidgets.QPushButton(parent=self.frame_4)
        self.pushButton_3.setGeometry(QtCore.QRect(120, 10, 75, 24))
        self.pushButton_3.setObjectName("pushButton_3")
        #定义pushButton_4
        self.pushButton_4 = QtWidgets.QPushButton(parent=self.frame_4)
        self.pushButton_4.setGeometry(QtCore.QRect(220, 10, 75, 24))
        self.pushButton_4.setObjectName("pushButton_4")
        #定义tabWidget
        self.tabWidget = QtWidgets.QTabWidget(parent=self.frame)
        self.tabWidget.setGeometry(QtCore.QRect(10, 320, 851, 271))
        self.tabWidget.setObjectName("tabWidget")
        #定义tab
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        #定义frame_5
        self.frame_5 = QtWidgets.QFrame(parent=self.tab)
        self.frame_5.setGeometry(QtCore.QRect(10, 10, 271, 111))
        self.frame_5.setObjectName("frame_5")
        #定义label_4
        self.label_4 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_4.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_4.setObjectName("label_4")
        #定义label_5
        self.label_5 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_5.setGeometry(QtCore.QRect(10, 30, 21, 20))
        self.label_5.setObjectName("label_5")
        #定义horizontalScrollBar
        self.horizontalScrollBar = QtWidgets.QScrollBar(parent=self.frame_5)
        self.horizontalScrollBar.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar.setObjectName("horizontalScrollBar")
        #定义label_6
        self.label_6 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_6.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_6.setObjectName("label_6")
        #定义label_7
        self.label_7 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_7.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_7.setObjectName("label_7")
        #定义label_8
        self.label_8 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_8.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_8.setObjectName("label_8")
        #定义horizontalScrollBar_2
        self.horizontalScrollBar_2 = QtWidgets.QScrollBar(parent=self.frame_5)
        self.horizontalScrollBar_2.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_2.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_2.setObjectName("horizontalScrollBar_2")
        #定义horizontalScrollBar_3
        self.horizontalScrollBar_3 = QtWidgets.QScrollBar(parent=self.frame_5)
        self.horizontalScrollBar_3.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_3.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_3.setObjectName("horizontalScrollBar_3")
        #定义label_9
        self.label_9 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_9.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_9.setObjectName("label_9")
        #定义label_10
        self.label_10 = QtWidgets.QLabel(parent=self.frame_5)
        self.label_10.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_10.setObjectName("label_10")
        #定义frame_6
        self.frame_6 = QtWidgets.QFrame(parent=self.tab)
        self.frame_6.setGeometry(QtCore.QRect(10, 130, 271, 111))
        self.frame_6.setObjectName("frame_6")
        #定义label_11
        self.label_11 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_11.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_11.setObjectName("label_11")
        #定义label_12
        self.label_12 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_12.setGeometry(QtCore.QRect(10, 30, 21, 16))
        self.label_12.setObjectName("label_12")
        #定义label_13
        self.label_13 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_13.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_13.setObjectName("label_13")
        #定义horizontalScrollBar_4
        self.horizontalScrollBar_4 = QtWidgets.QScrollBar(parent=self.frame_6)
        self.horizontalScrollBar_4.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar_4.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_4.setObjectName("horizontalScrollBar_4")
        #定义horizontalScrollBar_5
        self.horizontalScrollBar_5 = QtWidgets.QScrollBar(parent=self.frame_6)
        self.horizontalScrollBar_5.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_5.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_5.setObjectName("horizontalScrollBar_5")
        #定义label_14
        self.label_14 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_14.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_14.setObjectName("label_14")
        #定义label_15
        self.label_15 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_15.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_15.setObjectName("label_15")
        #定义label_16
        self.label_16 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_16.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_16.setObjectName("label_16")
        #定义label_17
        self.label_17 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_17.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_17.setObjectName("label_17")
        #定义horizontalScrollBar_6
        self.horizontalScrollBar_6 = QtWidgets.QScrollBar(parent=self.frame_6)
        self.horizontalScrollBar_6.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_6.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_6.setObjectName("horizontalScrollBar_6")
        #定义frame_7
        self.frame_7 = QtWidgets.QFrame(parent=self.tab)
        self.frame_7.setGeometry(QtCore.QRect(290, 10, 271, 111))
        self.frame_7.setObjectName("frame_7")
        #定义label_18
        self.label_18 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_18.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_18.setObjectName("label_18")
        #定义label_19
        self.label_19 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_19.setGeometry(QtCore.QRect(10, 30, 21, 16))
        self.label_19.setObjectName("label_19")
        #定义label_20
        self.label_20 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_20.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_20.setObjectName("label_20")
        #定义horizontalScrollBar_7
        self.horizontalScrollBar_7 = QtWidgets.QScrollBar(parent=self.frame_7)
        self.horizontalScrollBar_7.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar_7.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_7.setObjectName("horizontalScrollBar_7")
        #定义horizontalScrollBar_8
        self.horizontalScrollBar_8 = QtWidgets.QScrollBar(parent=self.frame_7)
        self.horizontalScrollBar_8.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_8.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_8.setObjectName("horizontalScrollBar_8")
        #定义label_21
        self.label_21 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_21.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_21.setObjectName("label_21")
        #定义label_22
        self.label_22 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_22.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_22.setObjectName("label_22")
        #定义label_23
        self.label_23 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_23.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_23.setObjectName("label_23")
        #定义label_24
        self.label_24 = QtWidgets.QLabel(parent=self.frame_7)
        self.label_24.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_24.setObjectName("label_24")
        #定义horizontalScrollBar_9
        self.horizontalScrollBar_9 = QtWidgets.QScrollBar(parent=self.frame_7)
        self.horizontalScrollBar_9.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_9.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_9.setObjectName("horizontalScrollBar_9")
        #定义frame_8
        self.frame_8 = QtWidgets.QFrame(parent=self.tab)
        self.frame_8.setGeometry(QtCore.QRect(290, 130, 271, 111))
        self.frame_8.setObjectName("frame_8")
        #定义label_25
        self.label_25 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_25.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_25.setObjectName("label_25")
        #定义label_26
        self.label_26 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_26.setGeometry(QtCore.QRect(10, 30, 21, 16))
        self.label_26.setObjectName("label_26")
        #定义label_27
        self.label_27 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_27.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_27.setObjectName("label_27")
        #定义horizontalScrollBar_10
        self.horizontalScrollBar_10 = QtWidgets.QScrollBar(parent=self.frame_8)
        self.horizontalScrollBar_10.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar_10.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_10.setObjectName("horizontalScrollBar_10")
        #定义horizontalScrollBar_11
        self.horizontalScrollBar_11 = QtWidgets.QScrollBar(parent=self.frame_8)
        self.horizontalScrollBar_11.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_11.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_11.setObjectName("horizontalScrollBar_11")
        #定义label_28
        self.label_28 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_28.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_28.setObjectName("label_28")
        #定义label_29
        self.label_29 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_29.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_29.setObjectName("label_29")
        #定义label_30
        self.label_30 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_30.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_30.setObjectName("label_30")
        #定义label_31
        self.label_31 = QtWidgets.QLabel(parent=self.frame_8)
        self.label_31.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_31.setObjectName("label_31")
        #定义horizontalScrollBar_12
        self.horizontalScrollBar_12 = QtWidgets.QScrollBar(parent=self.frame_8)
        self.horizontalScrollBar_12.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_12.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_12.setObjectName("horizontalScrollBar_12")
        #定义frame_9
        self.frame_9 = QtWidgets.QFrame(parent=self.tab)
        self.frame_9.setGeometry(QtCore.QRect(570, 10, 271, 111))
        self.frame_9.setObjectName("frame_9")
        #定义label_32
        self.label_32 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_32.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_32.setObjectName("label_32")
        #定义label_33
        self.label_33 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_33.setGeometry(QtCore.QRect(10, 30, 21, 16))
        self.label_33.setObjectName("label_33")
        #定义label_34
        self.label_34 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_34.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_34.setObjectName("label_34")
        #定义horizontalScrollBar_13
        self.horizontalScrollBar_13 = QtWidgets.QScrollBar(parent=self.frame_9)
        self.horizontalScrollBar_13.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar_13.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_13.setObjectName("horizontalScrollBar_13")
        #定义horizontalScrollBar_14
        self.horizontalScrollBar_14 = QtWidgets.QScrollBar(parent=self.frame_9)
        self.horizontalScrollBar_14.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_14.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_14.setObjectName("horizontalScrollBar_14")
        #定义label_35
        self.label_35 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_35.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_35.setObjectName("label_35")
        #定义label_36
        self.label_36 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_36.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_36.setObjectName("label_36")
        #定义label_37
        self.label_37 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_37.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_37.setObjectName("label_37")
        #定义label_38
        self.label_38 = QtWidgets.QLabel(parent=self.frame_9)
        self.label_38.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_38.setObjectName("label_38")
        #定义horizontalScrollBar_15
        self.horizontalScrollBar_15 = QtWidgets.QScrollBar(parent=self.frame_9)
        self.horizontalScrollBar_15.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_15.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_15.setObjectName("horizontalScrollBar_15")
        #定义frame_10
        self.frame_10 = QtWidgets.QFrame(parent=self.tab)
        self.frame_10.setGeometry(QtCore.QRect(570, 130, 271, 111))
        self.frame_10.setObjectName("frame_10")
        #定义label_39
        self.label_39 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_39.setGeometry(QtCore.QRect(90, 0, 81, 20))
        self.label_39.setObjectName("label_39")
        #定义label_40
        self.label_40 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_40.setGeometry(QtCore.QRect(10, 30, 21, 16))
        self.label_40.setObjectName("label_40")
        #定义label_41
        self.label_41 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_41.setGeometry(QtCore.QRect(10, 60, 21, 16))
        self.label_41.setObjectName("label_41")
        #定义horizontalScrollBar_16
        self.horizontalScrollBar_16 = QtWidgets.QScrollBar(parent=self.frame_10)
        self.horizontalScrollBar_16.setGeometry(QtCore.QRect(40, 30, 151, 16))
        self.horizontalScrollBar_16.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_16.setObjectName("horizontalScrollBar_16")
        #定义horizontalScrollBar_17
        self.horizontalScrollBar_17 = QtWidgets.QScrollBar(parent=self.frame_10)
        self.horizontalScrollBar_17.setGeometry(QtCore.QRect(40, 60, 151, 16))
        self.horizontalScrollBar_17.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_17.setObjectName("horizontalScrollBar_17")
        #定义label_42
        self.label_42 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_42.setGeometry(QtCore.QRect(200, 60, 61, 16))
        self.label_42.setObjectName("label_42")
        #定义label_43
        self.label_43 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_43.setGeometry(QtCore.QRect(200, 30, 61, 16))
        self.label_43.setObjectName("label_43")
        #定义label_44
        self.label_44 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_44.setGeometry(QtCore.QRect(10, 90, 21, 16))
        self.label_44.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_44.setObjectName("label_44")
        #定义label_45
        self.label_45 = QtWidgets.QLabel(parent=self.frame_10)
        self.label_45.setGeometry(QtCore.QRect(200, 90, 61, 16))
        self.label_45.setObjectName("label_45")
        #定义horizontalScrollBar_18
        self.horizontalScrollBar_18 = QtWidgets.QScrollBar(parent=self.frame_10)
        self.horizontalScrollBar_18.setGeometry(QtCore.QRect(40, 90, 151, 16))
        self.horizontalScrollBar_18.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalScrollBar_18.setObjectName("horizontalScrollBar_18")

        self.tabWidget.addTab(self.tab, "")
        #定义tab_2
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        #定义frmae_11
        self.frame_11 = QtWidgets.QFrame(parent=self.tab_2)
        self.frame_11.setGeometry(QtCore.QRect(10, 10, 451, 231))
        self.frame_11.setObjectName("frame_11")
        #定义label_46
        self.label_46 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_46.setGeometry(QtCore.QRect(90, 30, 31, 31))
        self.label_46.setObjectName("label_46")
        #定义pushButton_5
        self.pushButton_5 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_5.setGeometry(QtCore.QRect(90, 60, 31, 31))
        self.pushButton_5.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("image/arrowhead_up.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_5.setIcon(icon)
        self.pushButton_5.setObjectName("pushButton_5")
        #定义pushButton_6
        self.pushButton_6 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_6.setGeometry(QtCore.QRect(40, 110, 31, 31))
        self.pushButton_6.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("image/arrowhead_right.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_6.setIcon(icon1)
        self.pushButton_6.setObjectName("pushButton_6")
        #定义pushButton_7
        self.pushButton_7 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_7.setGeometry(QtCore.QRect(140, 110, 31, 31))
        self.pushButton_7.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("image/arrowhead_left.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_7.setIcon(icon2)
        self.pushButton_7.setObjectName("pushButton_7")
        #定义pushButton_8
        self.pushButton_8 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_8.setGeometry(QtCore.QRect(90, 160, 31, 31))
        self.pushButton_8.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("image/arrowhead_down.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_8.setIcon(icon3)
        self.pushButton_8.setObjectName("pushButton_8")
        #定义label_54
        self.label_54 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_54.setGeometry(QtCore.QRect(10, 110, 31, 31))
        self.label_54.setObjectName("label_54")
        #定义label_55
        self.label_55 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_55.setGeometry(QtCore.QRect(90, 190, 31, 31))
        self.label_55.setObjectName("label_55")
        #定义label_56
        self.label_56 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_56.setGeometry(QtCore.QRect(170, 110, 31, 31))
        self.label_56.setObjectName("label_56")
        #定义pushButton_11
        self.pushButton_11 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_11.setGeometry(QtCore.QRect(230, 60, 31, 31))
        self.pushButton_11.setText("")
        self.pushButton_11.setIcon(icon)
        self.pushButton_11.setObjectName("pushButton_11")
        #定义pushButton_12
        self.pushButton_12 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_12.setGeometry(QtCore.QRect(230, 160, 31, 31))
        self.pushButton_12.setText("")
        self.pushButton_12.setIcon(icon3)
        self.pushButton_12.setObjectName("pushButton_12")
        #定义label_50
        self.label_50 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_50.setGeometry(QtCore.QRect(230, 30, 31, 31))
        self.label_50.setObjectName("label_50")
        #定义label_57
        self.label_57 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_57.setGeometry(QtCore.QRect(230, 190, 31, 31))
        self.label_57.setObjectName("label_57")
        #定义pushButton_13
        self.pushButton_13 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_13.setGeometry(QtCore.QRect(400, 60, 31, 31))
        self.pushButton_13.setText("")
        self.pushButton_13.setIcon(icon2)
        self.pushButton_13.setObjectName("pushButton_13")
        #定义pushButton_14
        self.pushButton_14 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_14.setGeometry(QtCore.QRect(340, 60, 31, 31))
        self.pushButton_14.setText("")
        self.pushButton_14.setIcon(icon1)
        self.pushButton_14.setObjectName("pushButton_14")
        #定义label_58
        self.label_58 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_58.setGeometry(QtCore.QRect(310, 60, 31, 31))
        self.label_58.setObjectName("label_58")
        #定义label_59
        self.label_59 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_59.setGeometry(QtCore.QRect(340, 30, 31, 31))
        self.label_59.setObjectName("label_59")
        #定义label_60
        self.label_60 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_60.setGeometry(QtCore.QRect(400, 30, 31, 31))
        self.label_60.setObjectName("label_60")
        #定义label_61
        self.label_61 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_61.setGeometry(QtCore.QRect(310, 110, 31, 31))
        self.label_61.setObjectName("label_61")
        #定义pushButton_15
        self.pushButton_15 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_15.setGeometry(QtCore.QRect(400, 110, 31, 31))
        self.pushButton_15.setText("")
        self.pushButton_15.setIcon(icon2)
        self.pushButton_15.setObjectName("pushButton_15")
        #定义pushButton_16
        self.pushButton_16 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_16.setGeometry(QtCore.QRect(340, 110, 31, 31))
        self.pushButton_16.setText("")
        self.pushButton_16.setIcon(icon1)
        self.pushButton_16.setObjectName("pushButton_16")
        #定义label_62
        self.label_62 = QtWidgets.QLabel(parent=self.frame_11)
        self.label_62.setGeometry(QtCore.QRect(310, 160, 31, 31))
        self.label_62.setObjectName("label_62")
        #定义pushButton_17
        self.pushButton_17 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_17.setGeometry(QtCore.QRect(400, 160, 31, 31))
        self.pushButton_17.setText("")
        self.pushButton_17.setIcon(icon2)
        self.pushButton_17.setObjectName("pushButton_17")
        #定义pushButton_18
        self.pushButton_18 = QtWidgets.QPushButton(parent=self.frame_11)
        self.pushButton_18.setGeometry(QtCore.QRect(340, 160, 31, 31))
        self.pushButton_18.setText("")
        self.pushButton_18.setIcon(icon1)
        self.pushButton_18.setObjectName("pushButton_18")
        #定义frame_12
        self.frame_12 = QtWidgets.QFrame(parent=self.tab_2)
        self.frame_12.setGeometry(QtCore.QRect(470, 10, 371, 231))
        self.frame_12.setObjectName("frame_12")
        #定义pushButton_9
        self.pushButton_9 = QtWidgets.QPushButton(parent=self.frame_12)
        self.pushButton_9.setGeometry(QtCore.QRect(120, 190, 51, 24))
        self.pushButton_9.setObjectName("pushButton_9")
        #定义pushButton_10
        self.pushButton_10 = QtWidgets.QPushButton(parent=self.frame_12)
        self.pushButton_10.setGeometry(QtCore.QRect(260, 190, 51, 24))
        self.pushButton_10.setObjectName("pushButton_10")
        #定义label_47
        self.label_47 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_47.setGeometry(QtCore.QRect(40, 30, 31, 16))
        self.label_47.setObjectName("label_47")
        #定义label_48
        self.label_48 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_48.setGeometry(QtCore.QRect(40, 80, 31, 20))
        self.label_48.setObjectName("label_48")
        #定义label_49
        self.label_49 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_49.setGeometry(QtCore.QRect(40, 140, 31, 16))
        self.label_49.setObjectName("label_49")
        #定义lineEdit_2
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_2.setGeometry(QtCore.QRect(100, 30, 51, 20))
        self.lineEdit_2.setObjectName("lineEdit_2")
        #定义lineEdit_3
        self.lineEdit_3 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_3.setGeometry(QtCore.QRect(100, 80, 51, 20))
        self.lineEdit_3.setObjectName("lineEdit_3")
        #定义lineEdit_4
        self.lineEdit_4 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_4.setGeometry(QtCore.QRect(100, 140, 51, 20))
        self.lineEdit_4.setObjectName("lineEdit_4")
        #定义lineEdit_5
        self.lineEdit_5 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_5.setGeometry(QtCore.QRect(280, 140, 51, 20))
        self.lineEdit_5.setObjectName("lineEdit_5")
        #定义label_51
        self.label_51 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_51.setGeometry(QtCore.QRect(220, 140, 31, 16))
        self.label_51.setObjectName("label_51")
        #定义label_52
        self.label_52 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_52.setGeometry(QtCore.QRect(220, 80, 31, 20))
        self.label_52.setObjectName("label_52")
        #定义label_53
        self.label_53 = QtWidgets.QLabel(parent=self.frame_12)
        self.label_53.setGeometry(QtCore.QRect(220, 30, 31, 16))
        self.label_53.setObjectName("label_53")
        #定义lineEdit_6
        self.lineEdit_6 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_6.setGeometry(QtCore.QRect(280, 80, 51, 20))
        self.lineEdit_6.setObjectName("lineEdit_6")
        #定义lineEdit_7
        self.lineEdit_7 = QtWidgets.QLineEdit(parent=self.frame_12)
        self.lineEdit_7.setGeometry(QtCore.QRect(280, 30, 51, 20))
        self.lineEdit_7.setObjectName("lineEdit_7")

        self.tabWidget.addTab(self.tab_2, "")
        #定义tab_3
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        #定义frame_13
        self.frame_13 = QtWidgets.QFrame(parent=self.tab_3)
        self.frame_13.setGeometry(QtCore.QRect(10, 10, 531, 231))
        self.frame_13.setObjectName("frame_13")
        #定义lanel_63
        self.label_63 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_63.setGeometry(QtCore.QRect(380, 20, 31, 31))
        self.label_63.setObjectName("label_63")
        #定义pushButton_19
        self.pushButton_19 = QtWidgets.QPushButton(parent=self.frame_13)
        self.pushButton_19.setGeometry(QtCore.QRect(380, 50, 31, 31))
        self.pushButton_19.setText("")
        self.pushButton_19.setIcon(icon)
        self.pushButton_19.setObjectName("pushButton_19")
        #定义pushButton_20
        self.pushButton_20 = QtWidgets.QPushButton(parent=self.frame_13)
        self.pushButton_20.setGeometry(QtCore.QRect(330, 100, 31, 31))
        self.pushButton_20.setText("")
        self.pushButton_20.setIcon(icon1)
        self.pushButton_20.setObjectName("pushButton_20")
        #定义pushButton_21
        self.pushButton_21 = QtWidgets.QPushButton(parent=self.frame_13)
        self.pushButton_21.setGeometry(QtCore.QRect(430, 100, 31, 31))
        self.pushButton_21.setText("")
        self.pushButton_21.setIcon(icon2)
        self.pushButton_21.setObjectName("pushButton_21")
        #定义pushButton_22
        self.pushButton_22 = QtWidgets.QPushButton(parent=self.frame_13)
        self.pushButton_22.setGeometry(QtCore.QRect(380, 150, 31, 31))
        self.pushButton_22.setText("")
        self.pushButton_22.setIcon(icon3)
        self.pushButton_22.setObjectName("pushButton_22")
        #定义label_64
        self.label_64 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_64.setGeometry(QtCore.QRect(300, 100, 31, 31))
        self.label_64.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_64.setObjectName("label_64")
        #定义label_65
        self.label_65 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_65.setGeometry(QtCore.QRect(380, 180, 31, 31))
        self.label_65.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_65.setObjectName("label_65")
        #定义label_66
        self.label_66 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_66.setGeometry(QtCore.QRect(460, 100, 31, 31))
        self.label_66.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_66.setObjectName("label_66")
        #定义comboBox
        self.comboBox = QtWidgets.QComboBox(parent=self.frame_13)
        self.comboBox.setGeometry(QtCore.QRect(30, 40, 91, 22))
        self.comboBox.setObjectName("comboBox")
        #定义label_67
        self.label_67 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_67.setGeometry(QtCore.QRect(30, 10, 71, 21))
        self.label_67.setObjectName("label_67")
        #定义label_68
        self.label_68 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_68.setGeometry(QtCore.QRect(30, 80, 71, 21))
        self.label_68.setObjectName("label_68")
        #定义label_69
        self.label_69 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_69.setGeometry(QtCore.QRect(30, 150, 61, 21))
        self.label_69.setObjectName("label_69")
        #定义doubleSpinBox
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.frame_13)
        self.doubleSpinBox.setGeometry(QtCore.QRect(30, 180, 91, 22))
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        #定义doubleSpinBox_2
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(parent=self.frame_13)
        self.doubleSpinBox_2.setGeometry(QtCore.QRect(30, 110, 91, 22))
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        #定义label_78
        self.label_78 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_78.setGeometry(QtCore.QRect(140, 80, 61, 21))
        self.label_78.setObjectName("label_78")
        #定义label_79
        self.label_79 = QtWidgets.QLabel(parent=self.frame_13)
        self.label_79.setGeometry(QtCore.QRect(140, 150, 54, 20))
        self.label_79.setObjectName("label_79")
        #定义doubleSpinBox_3
        self.doubleSpinBox_3 = QtWidgets.QDoubleSpinBox(parent=self.frame_13)
        self.doubleSpinBox_3.setGeometry(QtCore.QRect(140, 110, 81, 22))
        self.doubleSpinBox_3.setObjectName("doubleSpinBox_3")
        #定义doubleSpinBox_4
        self.doubleSpinBox_4 = QtWidgets.QDoubleSpinBox(parent=self.frame_13)
        self.doubleSpinBox_4.setGeometry(QtCore.QRect(140, 180, 81, 22))
        self.doubleSpinBox_4.setObjectName("doubleSpinBox_4")
        #定义pushButton_23
        self.pushButton_23 = QtWidgets.QPushButton(parent=self.tab_3)
        self.pushButton_23.setGeometry(QtCore.QRect(760, 210, 51, 24))
        self.pushButton_23.setObjectName("pushButton_23")
        #定义label_70
        self.label_70 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_70.setGeometry(QtCore.QRect(610, 10, 131, 21))
        self.label_70.setObjectName("label_70")
        #定义label_71
        self.label_71 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_71.setGeometry(QtCore.QRect(560, 40, 54, 21))
        self.label_71.setObjectName("label_71")
        #定义label_72
        self.label_72 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_72.setGeometry(QtCore.QRect(650, 40, 61, 21))
        self.label_72.setObjectName("label_72")
        #定义label_73
        self.label_73 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_73.setGeometry(QtCore.QRect(750, 40, 54, 21))
        self.label_73.setObjectName("label_73")
        #定义label_74
        self.label_74 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_74.setGeometry(QtCore.QRect(560, 80, 54, 21))
        self.label_74.setObjectName("label_74")
        #定义label_75
        self.label_75 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_75.setGeometry(QtCore.QRect(560, 110, 54, 21))
        self.label_75.setObjectName("label_75")
        #定义label_76
        self.label_76 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_76.setGeometry(QtCore.QRect(560, 140, 54, 21))
        self.label_76.setObjectName("label_76")
        #定义label_77
        self.label_77 = QtWidgets.QLabel(parent=self.tab_3)
        self.label_77.setGeometry(QtCore.QRect(560, 170, 54, 21))
        self.label_77.setObjectName("label_77")
        #定义spinBox
        self.spinBox = QtWidgets.QSpinBox(parent=self.tab_3)
        self.spinBox.setGeometry(QtCore.QRect(651, 80, 61, 22))
        self.spinBox.setObjectName("spinBox")
        #定义spinBox_2
        self.spinBox_2 = QtWidgets.QSpinBox(parent=self.tab_3)
        self.spinBox_2.setGeometry(QtCore.QRect(651, 110, 61, 22))
        self.spinBox_2.setObjectName("spinBox_2")
        #定义spinBox_3
        self.spinBox_3 = QtWidgets.QSpinBox(parent=self.tab_3)
        self.spinBox_3.setGeometry(QtCore.QRect(651, 140, 61, 22))
        self.spinBox_3.setObjectName("spinBox_3")
        #定义spinBox_4
        self.spinBox_4 = QtWidgets.QSpinBox(parent=self.tab_3)
        self.spinBox_4.setGeometry(QtCore.QRect(651, 170, 61, 22))
        self.spinBox_4.setObjectName("spinBox_4")
        #定义lineEdit_8
        self.lineEdit_8 = QtWidgets.QLineEdit(parent=self.tab_3)
        self.lineEdit_8.setGeometry(QtCore.QRect(750, 80, 51, 20))
        self.lineEdit_8.setObjectName("lineEdit_8")
        #定义lineEdit_9
        self.lineEdit_9 = QtWidgets.QLineEdit(parent=self.tab_3)
        self.lineEdit_9.setGeometry(QtCore.QRect(750, 110, 51, 20))
        self.lineEdit_9.setObjectName("lineEdit_9")
        #定义lineEdit_10
        self.lineEdit_10 = QtWidgets.QLineEdit(parent=self.tab_3)
        self.lineEdit_10.setGeometry(QtCore.QRect(750, 140, 51, 20))
        self.lineEdit_10.setObjectName("lineEdit_10")
        #定义lineEdit_11
        self.lineEdit_11 = QtWidgets.QLineEdit(parent=self.tab_3)
        self.lineEdit_11.setGeometry(QtCore.QRect(750, 170, 51, 20))
        self.lineEdit_11.setObjectName("lineEdit_11")
        #定义pushButton_14
        self.pushButton_24 = QtWidgets.QPushButton(parent=self.tab_3)
        self.pushButton_24.setGeometry(QtCore.QRect(560, 210, 51, 24))
        self.pushButton_24.setObjectName("pushButton_24")
        #定义pushButton_25
        self.pushButton_25 = QtWidgets.QPushButton(parent=self.tab_3)
        self.pushButton_25.setGeometry(QtCore.QRect(660, 210, 51, 24))
        self.pushButton_25.setObjectName("pushButton_25")

        self.tabWidget.addTab(self.tab_3, "")

        self.retranslateUi()
    #字体设置
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Form", "Form"))
        # 设置label
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setText(_translate("Form", "状态实时显示"))
        # 设置label_2
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setText(_translate("Form", "数据发送"))
        # 设置label_3
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setText(_translate("Form", "数据接收"))
        # 设置radioButton
        self.radioButton.setFont(font)
        self.radioButton.setText(_translate("Form", "连接串口"))
        # 设置radioButton_2
        self.radioButton_2.setFont(font)
        self.radioButton_2.setText(_translate("Form", "连接蓝牙"))
        # 设置pushButton
        self.pushButton.setFont(font)
        self.pushButton.setText(_translate("Form", "发送"))
        # 设置pushButton_2
        self.pushButton_2.setFont(font)
        self.pushButton_2.setText(_translate("Form", "打开数据接收"))
        # 设置pushButton_3
        self.pushButton_3.setFont(font)
        self.pushButton_3.setText(_translate("Form", "清空发送"))
        # 设置pushButton_4
        self.pushButton_4.setFont(font)
        self.pushButton_4.setText(_translate("Form", "清空接收"))
        # 设置label_4
        font1 = QtGui.QFont()
        font1.setFamily("Arial")
        font1.setPointSize(10)
        self.label_4.setFont(font1)
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_4.setText(_translate("Form", "FrontRight"))
        # 设置label_5
        self.label_5.setFont(font1)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setText(_translate("Form", "α"))
        # 设置label_6
        self.label_6.setFont(font1)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setText(_translate("Form", "TextLabel"))
        # 设置label_7
        self.label_7.setFont(font1)
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_7.setText(_translate("Form", "β"))
        # 设置label_8
        self.label_8.setFont(font1)
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_8.setText(_translate("Form", "γ"))
        # 设置label_9
        self.label_9.setFont(font1)
        self.label_9.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_9.setText(_translate("Form", "TextLabel"))
        # 设置label_10
        self.label_10.setFont(font1)
        self.label_10.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_10.setText(_translate("Form", "TextLabel"))
        # 设置label_11
        self.label_11.setFont(font1)
        self.label_11.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_11.setText(_translate("Form", "FrontLeft"))
        # 设置label_12
        self.label_12.setFont(font1)
        self.label_12.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_12.setText(_translate("Form", "α"))
        # 设置label_13
        self.label_13.setFont(font1)
        self.label_13.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_13.setText(_translate("Form", "β"))
        # 设置label_14
        self.label_14.setFont(font1)
        self.label_14.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_14.setText(_translate("Form", "TextLabel"))
        # 设置label_15
        self.label_15.setFont(font1)
        self.label_15.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_15.setText(_translate("Form", "TextLabel"))
        # 设置label_16
        self.label_16.setFont(font1)
        self.label_16.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_16.setText(_translate("Form", "γ"))
        # 设置label_17
        self.label_17.setFont(font1)
        self.label_17.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_17.setText(_translate("Form", "TextLabel"))
        # 设置label_18
        self.label_18.setFont(font1)
        self.label_18.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_18.setText(_translate("Form", "MiddleRight"))
        # 设置label_19
        self.label_19.setFont(font1)
        self.label_19.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_19.setText(_translate("Form", "α"))
        # 设置label_20
        self.label_20.setFont(font1)
        self.label_20.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_20.setText(_translate("Form", "β"))
        # 设置label_21
        self.label_21.setFont(font1)
        self.label_21.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_21.setText(_translate("Form", "TextLabel"))
        # 设置label_22
        self.label_22.setFont(font1)
        self.label_22.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_22.setText(_translate("Form", "TextLabel"))
        # 设置label_23
        self.label_23.setFont(font1)
        self.label_23.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_23.setText(_translate("Form", "γ"))
        # 设置label_24
        self.label_24.setFont(font1)
        self.label_24.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_24.setText(_translate("Form", "TextLabel"))
        # 设置label_25
        self.label_25.setFont(font1)
        self.label_25.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_25.setText(_translate("Form", "MiddleLeft"))
        # 设置label_26
        self.label_26.setFont(font1)
        self.label_26.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_26.setText(_translate("Form", "α"))
        # 设置label_27
        self.label_27.setFont(font1)
        self.label_27.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_27.setText(_translate("Form", "β"))
        # 设置label_28
        self.label_28.setFont(font1)
        self.label_28.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_28.setText(_translate("Form", "TextLabel"))
        # 设置label_29
        self.label_29.setFont(font1)
        self.label_29.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_29.setText(_translate("Form", "TextLabel"))
        # 设置label_30
        self.label_30.setFont(font1)
        self.label_30.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_30.setText(_translate("Form", "γ"))
        # 设置label_31
        self.label_31.setFont(font1)
        self.label_31.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_31.setText(_translate("Form", "TextLabel"))
        # 设置label_32
        self.label_32.setFont(font1)
        self.label_32.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_32.setText(_translate("Form", "RearRight"))
        # 设置label_33
        self.label_33.setFont(font1)
        self.label_33.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_33.setText(_translate("Form", "α"))
        # 设置label_34
        self.label_34.setFont(font1)
        self.label_34.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_34.setText(_translate("Form", "β"))
        # 设置label_35
        self.label_35.setFont(font1)
        self.label_35.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_35.setText(_translate("Form", "TextLabel"))
        # 设置label_36
        self.label_36.setFont(font1)
        self.label_36.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_36.setText(_translate("Form", "TextLabel"))
        # 设置label_37
        self.label_37.setFont(font1)
        self.label_37.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_37.setText(_translate("Form", "γ"))
        # 设置label_38
        self.label_38.setFont(font1)
        self.label_38.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_38.setText(_translate("Form", "TextLabel"))
        # 设置label_39
        self.label_39.setFont(font1)
        self.label_39.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_39.setText(_translate("Form", "RearLeft"))
        # 设置label_40
        self.label_40.setFont(font1)
        self.label_40.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_40.setText(_translate("Form", "α"))
        # 设置label_41
        self.label_41.setFont(font1)
        self.label_41.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_41.setText(_translate("Form", "β"))
        # 设置label_42
        self.label_42.setFont(font1)
        self.label_42.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_42.setText(_translate("Form", "TextLabel"))
        # 设置label_43
        self.label_43.setFont(font1)
        self.label_43.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_43.setText(_translate("Form", "TextLabel"))
        # 设置label_44
        self.label_44.setFont(font1)
        self.label_44.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_44.setText(_translate("Form", "γ"))
        # 设置label_45
        self.label_45.setFont(font1)
        self.label_45.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_45.setText(_translate("Form", "TextLabel"))
        # 设置label_46
        self.label_46.setFont(font)
        self.label_46.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_46.setText(_translate("Form", "前"))
        # 设置label_54
        self.label_54.setFont(font)
        self.label_54.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_54.setText(_translate("Form", "左"))
        # 设置label_55
        self.label_55.setFont(font)
        self.label_55.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_55.setText(_translate("Form", "后"))
        # 设置label_56
        self.label_56.setFont(font)
        self.label_56.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_56.setText(_translate("Form", "右"))
        # 设置label_50
        self.label_50.setFont(font)
        self.label_50.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_50.setText(_translate("Form", "上"))
        # 设置label_57
        self.label_57.setFont(font)
        self.label_57.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_57.setText(_translate("Form", "下"))
        # 设置label_58
        self.label_58.setFont(font)
        self.label_58.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_58.setText(_translate("Form", "x"))
        # 设置label_59
        self.label_59.setFont(font)
        self.label_59.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_59.setText(_translate("Form", "逆"))
        # 设置label_60
        self.label_60.setFont(font)
        self.label_60.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_60.setText(_translate("Form", "顺"))
        # 设置label_61
        self.label_61.setFont(font1)
        self.label_61.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_61.setText(_translate("Form", "y"))
        # 设置label_62
        self.label_62.setFont(font1)
        self.label_62.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_62.setText(_translate("Form", "z"))
        # 设置pushButton_9
        self.pushButton_9.setFont(font)
        self.pushButton_9.setText(_translate("Form", "提交"))
        # 设置pushButton_10
        self.pushButton_10.setFont(font)
        self.pushButton_10.setText(_translate("Form", "复位"))
        # 设置label_47
        self.label_47.setFont(font1)
        self.label_47.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_47.setText(_translate("Form", "x"))
        # 设置label_48
        self.label_48.setFont(font1)
        self.label_48.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_48.setText(_translate("Form", "y"))
        # 设置label_49
        self.label_49.setFont(font1)
        self.label_49.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_49.setText(_translate("Form", "z"))
        # 设置label_51
        self.label_51.setFont(font1)
        self.label_51.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_51.setText(_translate("Form", "γ"))
        # 设置label_52
        self.label_52.setFont(font1)
        self.label_52.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_52.setText(_translate("Form", "β"))
        # 设置label_53
        self.label_53.setFont(font1)
        self.label_53.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_53.setText(_translate("Form", "α"))
        # 设置label_63
        self.label_63.setFont(font)
        self.label_63.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_63.setText(_translate("Form", "前进"))
        # 设置label_64
        self.label_64.setFont(font)
        self.label_64.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_64.setText(_translate("Form", "左转"))
        # 设置label_65
        self.label_65.setFont(font)
        self.label_65.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_65.setText(_translate("Form", "后退"))
        # 设置label_66
        self.label_66.setFont(font)
        self.label_66.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_66.setText(_translate("Form", "右转"))
        # 设置label_67
        self.label_67.setFont(font)
        self.label_67.setText(_translate("Form", "步态选择"))
        # 设置label_68
        self.label_68.setFont(font)
        self.label_68.setText(_translate("Form", "行走距离"))
        # 设置label_78
        self.label_78.setFont(font)
        self.label_78.setText(_translate("Form", "行走时间"))
        # 设置label_79
        self.label_79.setFont(font)
        self.label_79.setText(_translate("Form", "转动时间"))
        # 设置label_69
        self.label_69.setFont(font)
        self.label_69.setText(_translate("Form", "转动角度"))
        # 设置pushButton_23
        self.pushButton_23.setFont(font)
        self.pushButton_23.setText(_translate("Form", "复位"))
        # 设置pushButton_24
        self.pushButton_24.setFont(font)
        self.pushButton_24.setText(_translate("Form", "开始"))
        # 设置pushButton_25
        self.pushButton_25.setFont(font)
        self.pushButton_25.setText(_translate("Form", "停止"))
        # 设置label_70
        self.label_70.setFont(font)
        self.label_70.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_70.setText(_translate("Form", "自定义循环动作"))
        # 设置label_71
        self.label_71.setFont(font)
        self.label_71.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_71.setText(_translate("Form", "动作"))
        # 设置label_72
        self.label_72.setFont(font)
        self.label_72.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_72.setText(_translate("Form", "循环次数"))
        # 设置label_73
        self.label_73.setFont(font)
        self.label_73.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_73.setText(_translate("Form", "序号"))
        # 设置label_74
        self.label_74.setFont(font)
        self.label_74.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_74.setText(_translate("Form", "前进"))
        # 设置label_75
        self.label_75.setFont(font)
        self.label_75.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_75.setText(_translate("Form", "后退"))
        # 设置label_76
        self.label_76.setFont(font)
        self.label_76.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_76.setText(_translate("Form", "左转"))
        # 设置label_77
        self.label_77.setFont(font)
        self.label_77.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_77.setText(_translate("Form", "右转"))

        # 设置tabWidget
        self.tabWidget.setFont(font)
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.TabShape.Triangular)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", "自定义控制"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "姿态控制"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("Form", "移动控制"))
    #初始化控件
    def init_control(self,hexapod:Hexapod):
        self.init_horizontalScrollBar(hexapod)
        self.init_canvas(hexapod)
        self.init_lineEdit(hexapod)
        asyncio.run_coroutine_threadsafe(self.plotthread.update_hexapod(hexapod),self.plotthread.loop)

    #初始化horizontalScrollBar
    def init_horizontalScrollBar(self,hexapod:Hexapod):
        self.horizontalScrollBar.setMinimum(hexapod.legs[1].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar.setMaximum(hexapod.legs[1].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar.setValue(hexapod.legs[1].angles[0]*180/math.pi)
        self.horizontalScrollBar_2.setMinimum(hexapod.legs[1].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_2.setMaximum(hexapod.legs[1].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_2.setValue(hexapod.legs[1].angles[1]*180/math.pi)
        self.horizontalScrollBar_3.setMinimum(hexapod.legs[1].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_3.setMaximum(hexapod.legs[1].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_3.setValue(hexapod.legs[1].angles[2]*180/math.pi)

        self.horizontalScrollBar_4.setMinimum(hexapod.legs[2].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar_4.setMaximum(hexapod.legs[2].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar_4.setValue(hexapod.legs[2].angles[0]*180/math.pi)
        self.horizontalScrollBar_5.setMinimum(hexapod.legs[2].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_5.setMaximum(hexapod.legs[2].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_5.setValue(hexapod.legs[2].angles[1]*180/math.pi)
        self.horizontalScrollBar_6.setMinimum(hexapod.legs[2].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_6.setMaximum(hexapod.legs[2].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_6.setValue(hexapod.legs[2].angles[2]*180/math.pi)

        self.horizontalScrollBar_7.setMinimum(hexapod.legs[0].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar_7.setMaximum(hexapod.legs[0].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar_7.setValue(hexapod.legs[0].angles[0]*180/math.pi)
        self.horizontalScrollBar_8.setMinimum(hexapod.legs[0].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_8.setMaximum(hexapod.legs[0].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_8.setValue(hexapod.legs[0].angles[1]*180/math.pi)
        self.horizontalScrollBar_9.setMinimum(hexapod.legs[0].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_9.setMaximum(hexapod.legs[0].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_9.setValue(hexapod.legs[0].angles[2]*180/math.pi)

        self.horizontalScrollBar_10.setMinimum(hexapod.legs[3].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar_10.setMaximum(hexapod.legs[3].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar_10.setValue(hexapod.legs[3].angles[0]*180/math.pi)
        self.horizontalScrollBar_11.setMinimum(hexapod.legs[3].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_11.setMaximum(hexapod.legs[3].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_11.setValue(hexapod.legs[3].angles[1]*180/math.pi)
        self.horizontalScrollBar_12.setMinimum(hexapod.legs[3].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_12.setMaximum(hexapod.legs[3].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_12.setValue(hexapod.legs[3].angles[2]*180/math.pi)

        self.horizontalScrollBar_13.setMinimum(hexapod.legs[5].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar_13.setMaximum(hexapod.legs[5].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar_13.setValue(hexapod.legs[5].angles[0]*180/math.pi)
        self.horizontalScrollBar_14.setMinimum(hexapod.legs[5].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_14.setMaximum(hexapod.legs[5].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_14.setValue(hexapod.legs[5].angles[1]*180/math.pi)
        self.horizontalScrollBar_15.setMinimum(hexapod.legs[5].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_15.setMaximum(hexapod.legs[5].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_15.setValue(hexapod.legs[5].angles[2]*180/math.pi)

        self.horizontalScrollBar_16.setMinimum(hexapod.legs[4].angle_limits[0][0]*180/math.pi)
        self.horizontalScrollBar_16.setMaximum(hexapod.legs[4].angle_limits[0][1]*180/math.pi)
        self.horizontalScrollBar_16.setValue(hexapod.legs[4].angles[0]*180/math.pi)
        self.horizontalScrollBar_17.setMinimum(hexapod.legs[4].angle_limits[1][0]*180/math.pi)
        self.horizontalScrollBar_17.setMaximum(hexapod.legs[4].angle_limits[1][1]*180/math.pi)
        self.horizontalScrollBar_17.setValue(hexapod.legs[4].angles[1]*180/math.pi)
        self.horizontalScrollBar_18.setMinimum(hexapod.legs[4].angle_limits[2][0]*180/math.pi)
        self.horizontalScrollBar_18.setMaximum(hexapod.legs[4].angle_limits[2][1]*180/math.pi)
        self.horizontalScrollBar_18.setValue(hexapod.legs[4].angles[2]*180/math.pi)

        self.init_horizontalScrollBar_label()
    #初始化horizontalScrollBar_label
    def init_horizontalScrollBar_label(self):
        self.label_6.setText(str(self.horizontalScrollBar.value()))
        self.label_9.setText(str(self.horizontalScrollBar_2.value()))
        self.label_10.setText(str(self.horizontalScrollBar_3.value()))

        self.label_15.setText(str(self.horizontalScrollBar_4.value()))
        self.label_14.setText(str(self.horizontalScrollBar_5.value()))
        self.label_17.setText(str(self.horizontalScrollBar_6.value()))

        self.label_22.setText(str(self.horizontalScrollBar_7.value()))
        self.label_21.setText(str(self.horizontalScrollBar_8.value()))
        self.label_24.setText(str(self.horizontalScrollBar_9.value()))

        self.label_29.setText(str(self.horizontalScrollBar_10.value()))
        self.label_28.setText(str(self.horizontalScrollBar_11.value()))
        self.label_31.setText(str(self.horizontalScrollBar_12.value()))

        self.label_36.setText(str(self.horizontalScrollBar_13.value()))
        self.label_35.setText(str(self.horizontalScrollBar_14.value()))
        self.label_38.setText(str(self.horizontalScrollBar_15.value()))

        self.label_43.setText(str(self.horizontalScrollBar_16.value()))
        self.label_42.setText(str(self.horizontalScrollBar_17.value()))
        self.label_45.setText(str(self.horizontalScrollBar_18.value()))
    #初始化lineEdit
    def init_lineEdit(self,hexapod:Hexapod):
        self.lineEdit_2.setText(str(hexapod.body.axis_x))
        self.lineEdit_3.setText(str(hexapod.body.axis_y))
        self.lineEdit_4.setText(str(hexapod.body.axis_z))
        self.lineEdit_7.setText(str(hexapod.body.axis_alpha))
        self.lineEdit_6.setText(str(hexapod.body.axis_beta))
        self.lineEdit_5.setText(str(hexapod.body.axis_gama))
    #初始化移动控制
    def init_move_control(self):
        items = ["三角步态","波动步态"]
        self.comboBox.addItems(items)
        self.comboBox.setCurrentIndex(0)
        self.doubleSpinBox.setMinimum(0)
        self.doubleSpinBox.setMaximum(30)
        self.doubleSpinBox.setValue(20.0)
        self.doubleSpinBox_2.setValue(5.0)
        self.doubleSpinBox_3.setMinimum(0)
        self.doubleSpinBox_3.setValue(3)
        self.doubleSpinBox_4.setMinimum(0)
        self.doubleSpinBox_4.setValue(3)

    #radioButton点击信号
    def radioButton_clicked(self):
        if self.sender() == self.radioButton:
            if self.radioButton.isChecked():
                self.radioButton.setEnabled(False)
                asyncio.run_coroutine_threadsafe(self.serthread.connect_ser(),self.serthread.loop)
                self.radioButton.setText("正在连接串口...")
            else:
                self.radioButton.setEnabled(False)
                asyncio.run_coroutine_threadsafe(self.serthread.disconnect_ser(), self.serthread.loop)
                self.radioButton.setText("正在关闭串口...")
        elif self.sender() == self.radioButton_2:
            if self.radioButton_2.isChecked():
                self.radioButton_2.setEnabled(False)
                asyncio.run_coroutine_threadsafe(self.bltthread.connect_blt(self.bltthread.bluetooth.target_address),
                                                 self.bltthread.loop)
                self.radioButton_2.setText("正在连接蓝牙...")
            else:
                self.radioButton_2.setEnabled(False)
                asyncio.run_coroutine_threadsafe(self.bltthread.disconnect_blt(), self.bltthread.loop)
                self.radioButton_2.setText("正在关闭蓝牙...")
    # 打开串口
    def connect_ser(self, connect_res):
        is_open = connect_res
        if is_open:
            self.radioButton.setText('串口已连接(' + self.serthread.serial.name + ')')
            self.radioButton.setChecked(True)
        else:
            QMessageBox.warning(self, 'Warning', '串口连接失败')
            self.radioButton.setText("连接串口")
            self.radioButton.setChecked(False)
        self.radioButton.setEnabled(True)
    # 关闭串口
    def disconnect_ser(self, disconnect_res):
        is_open = disconnect_res
        if is_open:
            QMessageBox.warning(self, 'Warning', '串口断开失败')
            self.radioButton.setText('串口已连接(' + self.serthread.serial.name + ')')
            self.radioButton.setChecked(True)
        else:
            self.radioButton.setText('连接串口')
            self.radioButton.setChecked(False)
        self.radioButton.setEnabled(True)
    # 打开蓝牙
    def connect_blt(self, connect_res):
        is_open = connect_res
        if is_open:
            self.radioButton_2.setText('蓝牙已连接('+self.bltthread.bluetooth.target_name+')')
            self.radioButton_2.setChecked(True)
        else:
            QMessageBox.warning(self, 'Warning', '蓝牙连接失败')
            self.radioButton_2.setText("连接蓝牙")
            self.radioButton_2.setChecked(False)
        self.radioButton_2.setEnabled(True)
    # 关闭蓝牙
    def disconnect_blt(self, disconnect_res):
        is_open = disconnect_res
        if is_open:
            QMessageBox.warning(self, 'Warning', '蓝牙断开失败')
            self.radioButton_2.setText('蓝牙已连接('+self.bltthread.bluetooth.target_name+')')
            self.radioButton_2.setChecked(True)
        else:
            self.radioButton_2.setText('连接蓝牙')
            self.radioButton_2.setChecked(False)
        self.radioButton_2.setEnabled(True)
    #是否打开数据接收
    def pushButton_is_receive(self):
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.read_is_receive(), self.serthread.loop)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.read_is_receive(), self.bltthread.loop)
    #修改串口接收状态
    def update_ser_is_receive(self, is_receive_signal):
        if not is_receive_signal:
            self.pushButton_2.setText("关闭数据接收")
            is_receive = True
            asyncio.run_coroutine_threadsafe(self.serthread.update_is_receive(is_receive), self.serthread.loop)
        else:
            self.pushButton_2.setText("打开数据接收")
            is_receive = False
            asyncio.run_coroutine_threadsafe(self.serthread.update_is_receive(is_receive), self.serthread.loop)
    #修改蓝牙接收状态
    def update_blt_is_receive(self,is_receive_signal):
        if not is_receive_signal:
            self.pushButton_2.setText("关闭数据接收")
            is_receive = True
            asyncio.run_coroutine_threadsafe(self.bltthread.update_is_receive(is_receive), self.bltthread.loop)
        else:
            self.pushButton_2.setText("打开数据接收")
            is_receive = False
            asyncio.run_coroutine_threadsafe(self.bltthread.update_is_receive(is_receive), self.bltthread.loop)
    #发送数据
    def pushButton_send_message(self,hexapod:Hexapod):
        data = self.lineEdit.text()
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.send_data(data), self.serthread.loop)
            sequance = hexapod.decoding(data)
            new_sequance = []
            for item in sequance:
                leg_name, node_name, angle, time = item
                new_sequance.append((leg_name, node_name, angle))
            hexapod.update_angle_sequance(new_sequance)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.send_data(data), self.bltthread.loop)
            sequance = hexapod.decoding(data)
            new_sequance = []
            for item in sequance:
                leg_name, node_name, angle, time = item
                new_sequance.append((leg_name, node_name, angle))
            hexapod.update_angle_sequance(new_sequance)
    #更新数据发送面板
    def textEdit_send_message(self,send_message):
        self.textEdit.append(send_message)
    #更新数据接收面板
    def textEdit_receive_message(self,receive_message):
        self.textEdit_2.append(receive_message)
    #清空数据发送
    def pushButton_clear_send(self):
        self.textEdit.clear()
    #清空数据接收
    def pushButton_clear_receive(self):
        self.textEdit_2.clear()
    #发送自定义角度
    def send_horizontalScrollBar_angle(self,index,angle,hexapod):
        index1 = str(index).zfill(3)
        pwm = int(angle/90*1000+1500)
        pwm = str(pwm).zfill(4)
        data = "#"+index1+"P"+pwm+"T0300!"
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.send_data(data), self.serthread.loop)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.send_data(data), self.bltthread.loop)
        leg_num = int(index/3)
        leg_name = LEG_ID_NAMES[leg_num]
        node_num = index % 3
        sequance = []
        if node_num == 0:
            sequance.append((leg_name,'alpha',angle/90*math.pi/2))
        if node_num == 1:
            sequance.append((leg_name,'beta',angle/90*math.pi/2))
        if node_num == 2:
            sequance.append((leg_name,'gama',angle/90*math.pi/2))
        hexapod.update_angle_sequance(sequance)

    #初始化canvas
    def init_canvas(self,hexapod:Hexapod):
        self.figure.clear()
        ax = self.figure.add_subplot(projection='3d')
        self.figure, ax = hexapod.visualize3d(self.figure, ax)
        self.canvas.draw()
    #发送send_message
    def send_message_to_plotthread(self,send_message):
        asyncio.run_coroutine_threadsafe(self.plotthread.update_canvas(send_message),self.plotthread.loop)
        self.update_horizontalScrollBar_signal.emit()
    #更新
    def update_horizontalScrollBar(self,hexapod:Hexapod):
        self.init_horizontalScrollBar(hexapod)
        self.init_horizontalScrollBar_label()
    # 更新canvas
    def update_canvas(self):
        self.canvas.draw()
        self.canvas.flush_events()


    #发送姿态按钮
    def sequance_button(self,action,hexapod:Hexapod):
        distance = 1
        angle_step = 1
        if action == "forward":
            try:
                hexapod.move_body(transform=(0,distance,0,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_3.setText(str(round(hexapod.body.axis_y, 2)))
        elif action == "backend":
            try:
                hexapod.move_body(transform=(0,-distance,0,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_3.setText(str(round(hexapod.body.axis_y, 2)))
        elif action == "left":
            try:
                hexapod.move_body(transform=(-distance,0,0,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_2.setText(str(round(hexapod.body.axis_x, 2)))
        elif action == "right":
            try:
                hexapod.move_body(transform=(distance,0,0,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_2.setText(str(round(hexapod.body.axis_x, 2)))
        elif action == "up":
            try:
                hexapod.move_body(transform=(0,0,distance,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_4.setText(str(round(hexapod.body.axis_z, 2)))
        elif action == "down":
            try:
                hexapod.move_body(transform=(0,0,-distance,0,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_4.setText(str(round(hexapod.body.axis_z, 2)))
        elif action == "alpha_plus":
            try:
                hexapod.move_body(transform=(0,0,0,angle_step*math.pi/180,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_7.setText(str(round(hexapod.body.axis_alpha*180/math.pi, 2)))
        elif action == "alpha_sub":
            try:
                hexapod.move_body(transform=(0,0,0,-angle_step*math.pi/180,0,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_7.setText(str(round(hexapod.body.axis_alpha*180/math.pi, 2)))
        elif action == "beta_plus":
            try:
                hexapod.move_body(transform=(0,0,0,0,angle_step*math.pi/180,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_6.setText(str(round(hexapod.body.axis_beta*180/math.pi, 2)))
        elif action == "beta_sub":
            try:
                hexapod.move_body(transform=(0,0,0,0,-angle_step*math.pi/180,0))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_6.setText(str(round(hexapod.body.axis_beta*180/math.pi, 2)))
        elif action == "gama_plus":
            try:
                hexapod.move_body(transform=(0,0,0,0,0,angle_step*math.pi/180))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_5.setText(str(round(hexapod.body.axis_gama*180/math.pi, 2)))
        elif action == "gama_sub":
            try:
                hexapod.move_body(transform=(0,0,0,0,0,-angle_step*math.pi/180))
                coding = hexapod.encoding()
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
            self.lineEdit_5.setText(str(round(hexapod.body.axis_gama*180/math.pi, 2)))
    #移动按钮
    def move_pushButton(self,action,hexapod:Hexapod):
        forward_distance = self.doubleSpinBox_2.value()
        forward_total_time = self.doubleSpinBox_3.value()
        rotate_angle = self.doubleSpinBox.value()*math.pi/180
        rotate_total_time = self.doubleSpinBox_4.value()
        if action == "forward_move":
            if self.comboBox.currentIndex()==0:
                try:
                    hexapod.tripod_forward(forward_distance=forward_distance,total_time=forward_total_time)
                    coding = hexapod.encoding()
                    if coding == []:
                        QMessageBox.warning(self, "Warning", "无法找到有效动作")
                    if self.radioButton.isChecked():
                        asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                    if self.radioButton_2.isChecked():
                        asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
                except:
                    pass
            elif self.comboBox.currentIndex()==1:
                try:
                    hexapod.wave_forward(forward_distance=forward_distance,total_time=forward_total_time)
                    coding = hexapod.encoding()
                    if coding == []:
                        QMessageBox.warning(self, "Warning", "无法找到有效动作")
                    if self.radioButton.isChecked():
                        asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                    if self.radioButton_2.isChecked():
                        asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
                except:
                    pass
        elif action == "backend_move":
            if self.comboBox.currentIndex()==0:
                try:
                    hexapod.tripod_forward(forward_distance=-forward_distance,total_time=forward_total_time)
                    coding = hexapod.encoding()
                    if coding == []:
                        QMessageBox.warning(self, "Warning", "无法找到有效动作")
                    if self.radioButton.isChecked():
                        asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                    if self.radioButton_2.isChecked():
                        asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
                except:
                    pass
            elif self.comboBox.currentIndex()==1:
                try:
                    hexapod.wave_forward(forward_distance=-forward_distance,total_time=forward_total_time)
                    coding = hexapod.encoding()
                    if coding == []:
                        QMessageBox.warning(self, "Warning", "无法找到有效动作")
                    if self.radioButton.isChecked():
                        asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                    if self.radioButton_2.isChecked():
                        asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
                except:
                    pass
        elif action == "left_turn":
            try:
                hexapod.rotate_move(rotate_angle=rotate_angle,total_time=rotate_total_time)
                coding = hexapod.encoding()
                if coding == []:
                    QMessageBox.warning(self, "Warning", "无法找到有效动作")
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass
        elif action == "right_turn":
            try:
                hexapod.rotate_move(rotate_angle=-rotate_angle,total_time=rotate_total_time)
                coding = hexapod.encoding()
                if coding == []:
                    QMessageBox.warning(self, "Warning", "无法找到有效动作")
                if self.radioButton.isChecked():
                    asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
                if self.radioButton_2.isChecked():
                    asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
            except:
                pass

    #提交按钮
    def submit_pushButton(self,hexapod:Hexapod):
        target_x = float(self.lineEdit_2.text())
        target_y = float(self.lineEdit_3.text())
        target_z = float(self.lineEdit_4.text())
        target_alpha = float(self.lineEdit_7.text())*math.pi/180
        target_beta = float(self.lineEdit_6.text())*math.pi/180
        target_gama = float(self.lineEdit_5.text())*math.pi/180
        current_x = hexapod.body.axis_x
        current_y = hexapod.body.axis_y
        current_z = hexapod.body.axis_z
        current_alpha = hexapod.body.axis_alpha
        current_beta = hexapod.body.axis_beta
        current_gama = hexapod.body.axis_gama
        transform = (target_x-current_x,target_y-current_y,target_z-current_z,target_alpha-current_alpha,
                     target_beta-current_beta,target_gama-current_gama)
        try:
            hexapod.move_body(transform=transform)
            coding = hexapod.encoding()
            if coding==[]:
                QMessageBox.warning(self, "Warning", "无法找到有效动作")
            if self.radioButton.isChecked():
                asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
            if self.radioButton_2.isChecked():
                asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
        except:
            pass
        self.init_lineEdit(hexapod)
        self.init_horizontalScrollBar(hexapod)
        self.init_horizontalScrollBar_label()
    #复位按钮
    def reset_pushButton(self,hexapod:Hexapod):
        hexapod.reset()
        coding = hexapod.encoding()
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
        self.init_lineEdit(hexapod)
        self.init_horizontalScrollBar(hexapod)
        self.init_horizontalScrollBar_label()
    #开始按钮
    def start_pushButton(self,hexapod:Hexapod):
        forward_distance = self.doubleSpinBox_2.value()
        forward_total_time = self.doubleSpinBox_3.value()
        rotate_angle = self.doubleSpinBox.value() * math.pi / 180
        rotate_total_time = self.doubleSpinBox_4.value()
        index = []
        if self.lineEdit_8.text().isdigit():
            index.append(int(self.lineEdit_8.text()))
        if self.lineEdit_9.text().isdigit():
            index.append(int(self.lineEdit_9.text()))
        if self.lineEdit_10.text().isdigit():
            index.append(int(self.lineEdit_10.text()))
        if self.lineEdit_11.text().isdigit():
            index.append(int(self.lineEdit_11.text()))
        index.sort()
        for i in range(len(index)):
            if self.lineEdit_8.text() == str(index[i]):
                num = self.spinBox.value()
                if self.comboBox.currentIndex()==0:
                    for j in range(num):
                        try:
                            hexapod.tripod_forward(forward_distance=forward_distance,total_time=forward_total_time)
                        except:
                            pass
                elif self.comboBox.currentIndex()==1:
                    for j in range(num):
                        try:
                            hexapod.wave_forward(forward_distance=forward_distance,total_time=forward_total_time)
                        except:
                            pass
            elif self.lineEdit_9.text() == str(index[i]):
                num = self.spinBox_2.value()
                if self.comboBox.currentIndex() == 0:
                    for j in range(num):
                        try:
                            hexapod.tripod_forward(forward_distance=-forward_distance, total_time=forward_total_time)
                        except:
                            pass
                elif self.comboBox.currentIndex() == 1:
                    for j in range(num):
                        try:
                            hexapod.wave_forward(forward_distance=-forward_distance, total_time=forward_total_time)
                        except:
                            pass
            elif self.lineEdit_10.text() == str(index[i]):
                num = self.spinBox_3.value()
                for j in range(num):
                    try:
                        hexapod.rotate_move(rotate_angle=rotate_angle, total_time=rotate_total_time)
                    except:
                        pass
            elif self.lineEdit_11.text() == str(index[i]):
                num = self.spinBox_4.value()
                for j in range(num):
                    try:
                        hexapod.rotate_move(rotate_angle=-rotate_angle, total_time=rotate_total_time)
                    except:
                        pass
        coding = hexapod.encoding()
        if coding == []:
            QMessageBox.warning(self, "Warning", "无法找到有效动作")
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.send_coding(coding), self.serthread.loop)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.send_coding(coding), self.bltthread.loop)
    # 停止按钮
    def stop_pushButton(self):
        if self.radioButton.isChecked():
            asyncio.run_coroutine_threadsafe(self.serthread.stop_send(), self.serthread.loop)
        if self.radioButton_2.isChecked():
            asyncio.run_coroutine_threadsafe(self.bltthread.stop_send(), self.bltthread.loop)


#定义myWidget1(修改body参数)
class myWidget1(QWidget):
    update_body_aignal = pyqtSignal(Hexapod)
    #初始化
    def __init__(self,hexapod:Hexapod):
        super().__init__()
        _translate = QtCore.QCoreApplication.translate
        self.widget = QtWidgets.QWidget()
        # 设置窗口模态，使其打开时中止应用程序交互
        self.widget.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_UI(self.widget)
        self.init_doubleSpinBox(hexapod)
        self.pushButton.clicked.connect(lambda: self.confirm(hexapod))
        self.pushButton_2.clicked.connect(lambda: self.cancle())
        #加载qss
        with open("style/myWidget1.qss", "r") as file:
            self.widget.setStyleSheet(file.read())
    #初始化控件
    def init_UI(self, widget:QWidget):
        widget.setObjectName("myWidget1")
        widget.setFixedSize(520, 400)
        #定义frame
        self.frame = QtWidgets.QFrame(parent=widget)
        self.frame.setGeometry(QtCore.QRect(10, 10, 500, 340))
        self.frame.setObjectName("frame")
        #定义frame_2
        self.frame_2 = QtWidgets.QFrame(parent=self.frame)
        self.frame_2.setGeometry(QtCore.QRect(10, 10, 320, 320))
        self.frame_2.setStyleSheet("QFrame {\n"
                                   "    background-color: rgb(255,255,255);\n"
                                   "}")
        self.frame_2.setObjectName("frame_2")
        #定义图片label
        self.label = QtWidgets.QLabel(parent=self.frame_2)
        self.label.setGeometry(QtCore.QRect(20, 50, 289, 256))
        self.label.setPixmap(QtGui.QPixmap("image/body_size.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        #定义label_13
        self.label_13 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_13.setGeometry(QtCore.QRect(100, 10, 120, 30))
        self.label_13.setObjectName("label_13")
        #定义frame_3
        self.frame_3 = QtWidgets.QFrame(parent=self.frame)
        self.frame_3.setGeometry(QtCore.QRect(340, 10, 150, 320))
        self.frame_3.setObjectName("frame_3")
        #定义frame_3 Widget
        self.widget1 = QtWidgets.QWidget(parent=self.frame_3)
        self.widget1.setGeometry(QtCore.QRect(20, 10, 111, 295))
        self.widget1.setObjectName("widget1")
        #定义垂直布局控件
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget1)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        #定义表单布局控件
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.formLayout.setVerticalSpacing(6)
        self.formLayout.setObjectName("formLayout")
        #定义f label
        self.label_2 = QtWidgets.QLabel(parent=self.widget1)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        #定义小数数字选择控件
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox.setMaximum(999.99)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox)
        #定义s label
        self.label_3 = QtWidgets.QLabel(parent=self.widget1)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)
        #定义小数数字选择控件
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_2.setMaximum(999.99)
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_2)
        #定义m label
        self.label_4 = QtWidgets.QLabel(parent=self.widget1)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4)
        #定义小数数字选择控件
        self.doubleSpinBox_3 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_3.setMaximum(999.99)
        self.doubleSpinBox_3.setObjectName("doubleSpinBox_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_3)
        #定义尺寸参数 label
        self.label_5 = QtWidgets.QLabel(parent=self.widget1)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)
        self.verticalLayout.addLayout(self.formLayout)
        #定义表单控件2
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.formLayout_2.setHorizontalSpacing(6)
        self.formLayout_2.setVerticalSpacing(7)
        self.formLayout_2.setObjectName("formLayout_2")
        #定义坐标参数 label
        self.label_6 = QtWidgets.QLabel(parent=self.widget1)
        self.label_6.setObjectName("label_6")
        self.verticalLayout.addWidget(self.label_6)
        #定义x label
        self.label_7 = QtWidgets.QLabel(parent=self.widget1)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_7)
        # 定义y label
        self.label_8 = QtWidgets.QLabel(parent=self.widget1)
        self.label_8.setObjectName("label_8")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_8)
        # 定义z label
        self.label_9 = QtWidgets.QLabel(parent=self.widget1)
        self.label_9.setObjectName("label_9")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_9)
        #定义小数数字选择控件
        self.doubleSpinBox_4 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_4.setObjectName("doubleSpinBox_4")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_4)
        # 定义小数数字选择控件
        self.doubleSpinBox_5 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_5.setObjectName("doubleSpinBox_5")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_5)
        # 定义小数数字选择控件
        self.doubleSpinBox_6 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_6.setObjectName("doubleSpinBox_6")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_6)
        #定义α label
        self.label_10 = QtWidgets.QLabel(parent=self.widget1)
        self.label_10.setObjectName("label_10")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_10)
        #定义β label
        self.label_11 = QtWidgets.QLabel(parent=self.widget1)
        self.label_11.setObjectName("label_11")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_11)
        #定义γ label
        self.label_12 = QtWidgets.QLabel(parent=self.widget1)
        self.label_12.setObjectName("label_12")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_12)
        # 定义小数数字选择控件
        self.doubleSpinBox_7 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_7.setObjectName("doubleSpinBox_7")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_7)
        # 定义小数数字选择控件
        self.doubleSpinBox_8 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_8.setObjectName("doubleSpinBox_8")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_8)
        # 定义小数数字选择控件
        self.doubleSpinBox_9 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_9.setObjectName("doubleSpinBox_9")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.doubleSpinBox_9)
        self.verticalLayout.addLayout(self.formLayout_2)
        #定义widget2
        self.widget2 = QtWidgets.QWidget(parent=widget)
        self.widget2.setGeometry(QtCore.QRect(140, 360, 261, 30))
        self.widget2.setObjectName("widget2")
        #定义水平布局控件
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        #定义确认按钮
        self.pushButton = QtWidgets.QPushButton(parent=self.widget2)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        #定义弹簧控件
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        #定义取消按钮
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.widget2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)

        self.retranslateUi(self.widget)
        QtCore.QMetaObject.connectSlotsByName(self.widget)
    #控件字体设置
    def retranslateUi(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("Widget", "修改body参数"))
        #label_2字体设置
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setStrikeOut(False)
        self.label_2.setFont(font)
        self.label_2.setText(_translate("Widget", "f"))
        # label_3字体设置
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setFont(font)
        self.label_3.setText(_translate("Widget", "s"))
        # label_4字体设置
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_4.setText(_translate("Widget", "m"))
        # label_5字体设置
        font1 = QtGui.QFont()
        font1.setFamily("微软雅黑")
        font1.setPointSize(11)
        font1.setBold(False)
        self.label_5.setFont(font1)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setText(_translate("Widget", "尺寸参数"))
        # label_6字体设置
        self.label_6.setFont(font1)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setText(_translate("Widget", "坐标参数"))
        # label_7字体设置
        self.label_7.setFont(font)
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_7.setText(_translate("Widget", "x"))
        # label_8字体设置
        self.label_8.setFont(font)
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_8.setText(_translate("Widget", "y"))
        # label_9字体设置
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_9.setText(_translate("Widget", "z"))
        # label_10字体设置
        self.label_10.setFont(font)
        self.label_10.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_10.setText(_translate("Widget", "α"))
        # label_11字体设置
        self.label_11.setFont(font)
        self.label_11.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_11.setText(_translate("Widget", "β"))
        # label_12字体设置
        self.label_12.setFont(font)
        self.label_12.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_12.setText(_translate("Widget", "γ"))
        # label_13字体设置
        self.label_13.setFont(font1)
        self.label_13.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_13.setText(_translate("Widget", "尺寸示意图"))
        # pushButton字体设置
        font2 = QtGui.QFont()
        font2.setFamily("微软雅黑")
        font2.setPointSize(11)
        self.pushButton.setFont(font2)
        self.pushButton.setText(_translate("Widget", "确认"))
        # pushButton字体设置
        self.pushButton_2.setFont(font2)
        self.pushButton_2.setText(_translate("Widget", "取消"))
    #初始化doublespinbox
    def init_doubleSpinBox(self,hexapod:Hexapod):
        self.doubleSpinBox.setValue(hexapod.body.f)
        self.doubleSpinBox_2.setValue(hexapod.body.s)
        self.doubleSpinBox_3.setValue(hexapod.body.m)
        self.doubleSpinBox_4.setValue(hexapod.body.axis_x)
        self.doubleSpinBox_5.setValue(hexapod.body.axis_y)
        self.doubleSpinBox_6.setValue(hexapod.body.axis_z)
        self.doubleSpinBox_7.setValue(hexapod.body.axis_alpha)
        self.doubleSpinBox_8.setValue(hexapod.body.axis_beta)
        self.doubleSpinBox_9.setValue(hexapod.body.axis_gama)
    #确认更改
    def confirm(self,hexapod:Hexapod):
        size = (self.doubleSpinBox.value(),self.doubleSpinBox_2.value(),self.doubleSpinBox_3.value())
        hexapod.change_body_size(size)
        attitude = (self.doubleSpinBox_4.value(),self.doubleSpinBox_5.value(),self.doubleSpinBox_6.value(),
                    self.doubleSpinBox_7.value(),self.doubleSpinBox_8.value(),self.doubleSpinBox_9.value())
        hexapod.change_body_attitude(attitude)
        self.update_body_aignal.emit(hexapod)
        self.widget.close()
    #取消更改
    def cancle(self):
        self.widget.close()
    #打开页面
    def show_widget(self,hexapod:Hexapod):
        self.init_doubleSpinBox(hexapod)
        self.widget.show()

#定义myWidget2(修改leg参数)
class myWidget2(QWidget):
    update_leg_aignal = pyqtSignal(Hexapod)
    #初始化
    def __init__(self,hexapod:Hexapod):
        super().__init__()
        _translate = QtCore.QCoreApplication.translate
        self.widget = QtWidgets.QWidget()
        # 设置窗口模态，使其打开时中止应用程序交互
        self.widget.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_UI(self.widget)
        self.init_ComboBox_DoubleSpinBox(hexapod)
        self.comboBox.currentIndexChanged.connect(lambda: self.update_comBoBox(hexapod))
        self.pushButton.clicked.connect(lambda: self.save_button(hexapod))
        self.pushButton_2.clicked.connect(lambda: self.cancle())
        # 加载qss
        with open("style/myWidget2.qss", "r") as file:
            self.widget.setStyleSheet(file.read())

    #初始化界面
    def init_UI(self,widget):
        widget.setObjectName("Widget")
        widget.setFixedSize(550, 670)
        #定义frame
        self.frame = QtWidgets.QFrame(parent=widget)
        self.frame.setGeometry(QtCore.QRect(10, 10, 531, 611))
        self.frame.setObjectName("frame")
        #定义frame_2
        self.frame_2 = QtWidgets.QFrame(parent=self.frame)
        self.frame_2.setGeometry(QtCore.QRect(10, 10, 341, 431))
        self.frame_2.setObjectName("frame_2")
        #定义label
        self.label = QtWidgets.QLabel(parent=self.frame_2)
        self.label.setGeometry(QtCore.QRect(10, 30, 321, 201))
        self.label.setPixmap(QtGui.QPixmap("image/leg_size.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        #定义label_2
        self.label_2 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_2.setGeometry(QtCore.QRect(130, -1, 101, 31))
        self.label_2.setObjectName("label_2")
        #定义label_11
        self.label_11 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_11.setGeometry(QtCore.QRect(140, 230, 91, 31))
        self.label_11.setObjectName("label_11")
        #定义label_12
        self.label_12 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_12.setGeometry(QtCore.QRect(13, 265, 321, 161))
        self.label_12.setPixmap(QtGui.QPixmap("image/leg_pos.png"))
        self.label_12.setScaledContents(True)
        self.label_12.setObjectName("label_12")
        #定义frame_3
        self.frame_3 = QtWidgets.QFrame(parent=self.frame)
        self.frame_3.setGeometry(QtCore.QRect(360, 10, 161, 431))
        self.frame_3.setObjectName("frame_3")
        #定义lable_3
        self.label_3 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_3.setGeometry(QtCore.QRect(50, 60, 71, 20))
        self.label_3.setObjectName("label_3")
        #定义label_7
        self.label_7 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_7.setGeometry(QtCore.QRect(20, 180, 121, 20))
        self.label_7.setObjectName("label_7")
        #定义lable_13
        self.label_13 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_13.setGeometry(QtCore.QRect(40, 0, 81, 31))
        self.label_13.setObjectName("label_13")
        #定义comboBox
        self.comboBox = QtWidgets.QComboBox(parent=self.frame_3)
        self.comboBox.setGeometry(QtCore.QRect(20, 30, 131, 22))
        self.comboBox.setObjectName("comboBox")
        #定义label_14
        self.label_14 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_14.setGeometry(QtCore.QRect(30, 300, 101, 21))
        self.label_14.setObjectName("label_14")
        #定义widget1
        self.widget1 = QtWidgets.QWidget(parent=self.frame_3)
        self.widget1.setGeometry(QtCore.QRect(0, 80, 161, 91))
        self.widget1.setObjectName("widget1")
        #定义网格布局
        self.gridLayout = QtWidgets.QGridLayout(self.widget1)
        self.gridLayout.setContentsMargins(5, 0, 5, 0)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        #定义label_4
        self.label_4 = QtWidgets.QLabel(parent=self.widget1)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1)
        #定义doubleSpinBox
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox.setMaximum(999.99)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.gridLayout.addWidget(self.doubleSpinBox, 0, 1, 1, 1)
        #定义label_5
        self.label_5 = QtWidgets.QLabel(parent=self.widget1)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        #定义doubleSpinBox_2
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_2.setMaximum(999.99)
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        self.gridLayout.addWidget(self.doubleSpinBox_2, 1, 1, 1, 1)
        #定义label_6
        self.label_6 = QtWidgets.QLabel(parent=self.widget1)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)
        #定义doubleSpinBox_3
        self.doubleSpinBox_3 = QtWidgets.QDoubleSpinBox(parent=self.widget1)
        self.doubleSpinBox_3.setMaximum(999.99)
        self.doubleSpinBox_3.setObjectName("doubleSpinBox_3")
        self.gridLayout.addWidget(self.doubleSpinBox_3, 2, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 4)
        #定义widget2
        self.widget2 = QtWidgets.QWidget(parent=self.frame_3)
        self.widget2.setGeometry(QtCore.QRect(0, 200, 161, 91))
        self.widget2.setObjectName("widget2")
        #定义网格布局控件
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget2)
        self.gridLayout_2.setContentsMargins(5, 0, 5, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        #定义label_8
        self.label_8 = QtWidgets.QLabel(parent=self.widget2)
        self.label_8.setObjectName("label_8")
        self.gridLayout_2.addWidget(self.label_8, 0, 0, 1, 1)
        #定义doubleSpinBox_4
        self.doubleSpinBox_4 = QtWidgets.QDoubleSpinBox(parent=self.widget2)
        self.doubleSpinBox_4.setObjectName("doubleSpinBox_4")
        self.gridLayout_2.addWidget(self.doubleSpinBox_4, 0, 1, 1, 1)
        #定义lable_9
        self.label_9 = QtWidgets.QLabel(parent=self.widget2)
        self.label_9.setObjectName("label_9")
        self.gridLayout_2.addWidget(self.label_9, 1, 0, 1, 1)
        #定义doubleSpinBox_5
        self.doubleSpinBox_5 = QtWidgets.QDoubleSpinBox(parent=self.widget2)
        self.doubleSpinBox_5.setObjectName("doubleSpinBox_5")
        self.gridLayout_2.addWidget(self.doubleSpinBox_5, 1, 1, 1, 1)
        #定义label_10
        self.label_10 = QtWidgets.QLabel(parent=self.widget2)
        self.label_10.setObjectName("label_10")
        self.gridLayout_2.addWidget(self.label_10, 2, 0, 1, 1)
        #定义doubleSpinBox_6
        self.doubleSpinBox_6 = QtWidgets.QDoubleSpinBox(parent=self.widget2)
        self.doubleSpinBox_6.setObjectName("doubleSpinBox_6")
        self.gridLayout_2.addWidget(self.doubleSpinBox_6, 2, 1, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 4)
        #定义widget3
        self.widget3 = QtWidgets.QWidget(parent=self.frame_3)
        self.widget3.setGeometry(QtCore.QRect(0, 320, 161, 91))
        self.widget3.setObjectName("widget2")
        #定义网格布局控件
        self.gridLayout_3 = QtWidgets.QGridLayout(self.widget3)
        self.gridLayout_3.setContentsMargins(6, 0, 6, 0)
        self.gridLayout_3.setVerticalSpacing(6)
        self.gridLayout_3.setObjectName("gridLayout_3")
        #定义lable_15
        self.label_15 = QtWidgets.QLabel(parent=self.widget3)
        self.label_15.setObjectName("label_15")
        self.gridLayout_3.addWidget(self.label_15, 0, 0, 1, 1)
        #定义doubleSpinBox_7
        self.doubleSpinBox_7 = QtWidgets.QDoubleSpinBox(parent=self.widget3)
        self.doubleSpinBox_7.setObjectName("doubleSpinBox_7")
        self.gridLayout_3.addWidget(self.doubleSpinBox_7, 0, 1, 1, 1)
        #定义lable_16
        self.label_16 = QtWidgets.QLabel(parent=self.widget3)
        self.label_16.setObjectName("label_16")
        self.gridLayout_3.addWidget(self.label_16, 1, 0, 1, 1)
        #定义doubleSpinBox_8
        self.doubleSpinBox_8 = QtWidgets.QDoubleSpinBox(parent=self.widget3)
        self.doubleSpinBox_8.setObjectName("doubleSpinBox_8")
        self.gridLayout_3.addWidget(self.doubleSpinBox_8, 1, 1, 1, 1)
        #定义label_17
        self.label_17 = QtWidgets.QLabel(parent=self.widget3)
        self.label_17.setObjectName("label_17")
        self.gridLayout_3.addWidget(self.label_17, 2, 0, 1, 1)
        #定义doubleSpinBox_9
        self.doubleSpinBox_9 = QtWidgets.QDoubleSpinBox(parent=self.widget3)
        self.doubleSpinBox_9.setObjectName("doubleSpinBox_9")
        self.gridLayout_3.addWidget(self.doubleSpinBox_9, 2, 1, 1, 1)

        self.gridLayout_3.setColumnStretch(0, 1)
        self.gridLayout_3.setColumnStretch(1, 4)
        #定义frame_4
        self.frame_4 = QtWidgets.QFrame(parent=self.frame)
        self.frame_4.setGeometry(QtCore.QRect(10, 450, 511, 151))
        self.frame_4.setObjectName("frame_4")
        #定义label_18
        self.label_18 = QtWidgets.QLabel(parent=self.frame_4)
        self.label_18.setGeometry(QtCore.QRect(100, 0, 101, 20))
        self.label_18.setObjectName("label_18")
        #定义label_19
        self.label_19 = QtWidgets.QLabel(parent=self.frame_4)
        self.label_19.setGeometry(QtCore.QRect(350, 0, 101, 20))
        self.label_19.setObjectName("label_19")
        #定义widget4
        self.widget4 = QtWidgets.QWidget(parent=self.frame_4)
        self.widget4.setGeometry(QtCore.QRect(1, 30, 281, 121))
        self.widget4.setObjectName("widget3")
        #定义网格布局控件
        self.gridLayout_5 = QtWidgets.QGridLayout(self.widget4)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        #定义label_25
        self.label_25 = QtWidgets.QLabel(parent=self.widget4)
        self.label_25.setObjectName("label_25")
        self.gridLayout_5.addWidget(self.label_25, 0, 0, 1, 1)
        #定义doubleSpinBox_16
        self.doubleSpinBox_16 = QtWidgets.QDoubleSpinBox(parent=self.widget4)
        self.doubleSpinBox_16.setMinimum(-999.9)
        self.doubleSpinBox_16.setMaximum(999.9)
        self.doubleSpinBox_16.setObjectName("doubleSpinBox_16")
        self.gridLayout_5.addWidget(self.doubleSpinBox_16, 0, 1, 1, 1)
        #定义label_28
        self.label_28 = QtWidgets.QLabel(parent=self.widget4)
        self.label_28.setObjectName("label_28")
        self.gridLayout_5.addWidget(self.label_28, 0, 2, 1, 1)
        #定义doubleSpinBox_19
        self.doubleSpinBox_19 = QtWidgets.QDoubleSpinBox(parent=self.widget4)
        self.doubleSpinBox_19.setMinimum(-90)
        self.doubleSpinBox_19.setMaximum(90)
        self.doubleSpinBox_19.setObjectName("doubleSpinBox_19")
        self.gridLayout_5.addWidget(self.doubleSpinBox_19, 0, 3, 1, 1)
        #定义label_26
        self.label_26 = QtWidgets.QLabel(parent=self.widget4)
        self.label_26.setObjectName("label_26")
        self.gridLayout_5.addWidget(self.label_26, 1, 0, 1, 1)
        #定义doubleSpinBox_17
        self.doubleSpinBox_17 = QtWidgets.QDoubleSpinBox(parent=self.widget4)
        self.doubleSpinBox_17.setMinimum(-999.9)
        self.doubleSpinBox_17.setMaximum(999.9)
        self.doubleSpinBox_17.setObjectName("doubleSpinBox_17")
        self.gridLayout_5.addWidget(self.doubleSpinBox_17, 1, 1, 1, 1)
        #定义label_29
        self.label_29 = QtWidgets.QLabel(parent=self.widget4)
        self.label_29.setObjectName("label_29")
        self.gridLayout_5.addWidget(self.label_29, 1, 2, 1, 1)
        #定义doubleSpinBox_20
        self.doubleSpinBox_20 = QtWidgets.QDoubleSpinBox(parent=self.widget4)
        self.doubleSpinBox_20.setMinimum(-90)
        self.doubleSpinBox_20.setMaximum(90)
        self.doubleSpinBox_20.setObjectName("doubleSpinBox_20")
        self.gridLayout_5.addWidget(self.doubleSpinBox_20, 1, 3, 1, 1)
        #定义label_27
        self.label_27 = QtWidgets.QLabel(parent=self.widget4)
        self.label_27.setObjectName("label_27")
        self.gridLayout_5.addWidget(self.label_27, 2, 0, 1, 1)
        #定义doubleSpinBox_18
        self.doubleSpinBox_18 = QtWidgets.QDoubleSpinBox(parent=self.widget3)
        self.doubleSpinBox_18.setMinimum(-999.9)
        self.doubleSpinBox_18.setMaximum(999.9)
        self.doubleSpinBox_18.setObjectName("doubleSpinBox_18")
        self.gridLayout_5.addWidget(self.doubleSpinBox_18, 2, 1, 1, 1)
        #定义label_30
        self.label_30 = QtWidgets.QLabel(parent=self.widget3)
        self.label_30.setObjectName("label_30")
        self.gridLayout_5.addWidget(self.label_30, 2, 2, 1, 1)
        #定义doubleSpinBox_21
        self.doubleSpinBox_21 = QtWidgets.QDoubleSpinBox(parent=self.widget3)
        self.doubleSpinBox_21.setMinimum(-90)
        self.doubleSpinBox_21.setMaximum(90)
        self.doubleSpinBox_21.setObjectName("doubleSpinBox_21")
        self.gridLayout_5.addWidget(self.doubleSpinBox_21, 2, 3, 1, 1)
        #定义网格布局控件
        self.gridLayout_5.setColumnStretch(0, 1)
        self.gridLayout_5.setColumnStretch(1, 4)
        self.gridLayout_5.setColumnStretch(2, 1)
        self.gridLayout_5.setColumnStretch(3, 4)
        #定义widget5
        self.widget5 = QtWidgets.QWidget(parent=self.frame_4)
        self.widget5.setGeometry(QtCore.QRect(290, 30, 221, 121))
        self.widget5.setObjectName("widget5")
        #定义网格布局控件
        self.gridLayout_4 = QtWidgets.QGridLayout(self.widget5)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setSpacing(6)
        self.gridLayout_4.setObjectName("gridLayout_4")
        #定义label_21
        self.label_21 = QtWidgets.QLabel(parent=self.widget5)
        self.label_21.setObjectName("label_21")
        self.gridLayout_4.addWidget(self.label_21, 1, 0, 1, 1)
        #定义doubleSpinBox_12
        self.doubleSpinBox_12 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_12.setMinimum(-90)
        self.doubleSpinBox_12.setMaximum(0)
        self.doubleSpinBox_12.setObjectName("doubleSpinBox_12")
        self.gridLayout_4.addWidget(self.doubleSpinBox_12, 1, 1, 1, 1)
        #定义label_20
        self.label_20 = QtWidgets.QLabel(parent=self.widget5)
        self.label_20.setObjectName("label_20")
        self.gridLayout_4.addWidget(self.label_20, 0, 0, 1, 1)
        #定义label_22
        self.label_22 = QtWidgets.QLabel(parent=self.widget5)
        self.label_22.setObjectName("label_22")
        self.gridLayout_4.addWidget(self.label_22, 2, 0, 1, 1)
        #定义doubleSpinBox_14
        self.doubleSpinBox_14 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_14.setMinimum(-90)
        self.doubleSpinBox_14.setMaximum(0)
        self.doubleSpinBox_14.setObjectName("doubleSpinBox_14")
        self.gridLayout_4.addWidget(self.doubleSpinBox_14, 2, 1, 1, 1)
        #定义doubleSpinBox_13
        self.doubleSpinBox_13 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_13.setMinimum(0)
        self.doubleSpinBox_13.setMaximum(90)
        self.doubleSpinBox_13.setObjectName("doubleSpinBox_13")
        self.gridLayout_4.addWidget(self.doubleSpinBox_13, 1, 2, 1, 1)
        #定义doubleSpinBox_10
        self.doubleSpinBox_10 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_10.setMinimum(-90)
        self.doubleSpinBox_10.setMaximum(0)
        self.doubleSpinBox_10.setObjectName("doubleSpinBox_10")
        self.gridLayout_4.addWidget(self.doubleSpinBox_10, 0, 1, 1, 1)
        #定义doubleSpinBox_11
        self.doubleSpinBox_11 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_11.setMinimum(0)
        self.doubleSpinBox_11.setMaximum(90)
        self.doubleSpinBox_11.setObjectName("doubleSpinBox_11")
        self.gridLayout_4.addWidget(self.doubleSpinBox_11, 0, 2, 1, 1)
        #定义doubleSpinBox_15
        self.doubleSpinBox_15 = QtWidgets.QDoubleSpinBox(parent=self.widget5)
        self.doubleSpinBox_15.setMinimum(0)
        self.doubleSpinBox_15.setMaximum(90)
        self.doubleSpinBox_15.setObjectName("doubleSpinBox_15")
        self.gridLayout_4.addWidget(self.doubleSpinBox_15, 2, 2, 1, 1)

        self.gridLayout_4.setColumnStretch(0, 1)
        self.gridLayout_4.setColumnStretch(1, 4)
        self.gridLayout_4.setColumnStretch(2, 4)
        #定义pushButton
        self.pushButton = QtWidgets.QPushButton(parent=widget)
        self.pushButton.setGeometry(QtCore.QRect(150, 630, 75, 24))
        self.pushButton.setObjectName("pushButton")
        #定义pushButton_2
        self.pushButton_2 = QtWidgets.QPushButton(parent=widget)
        self.pushButton_2.setGeometry(QtCore.QRect(350, 630, 75, 24))
        self.pushButton_2.setObjectName("pushButton_2")

        self.retranslateUi(widget)
        QtCore.QMetaObject.connectSlotsByName(widget)

    #字体设置
    def retranslateUi(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("widget", "修改leg参数"))
        # 设置label_2
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setText(_translate("widget", "尺寸示意图"))
        # 设置label_11
        self.label_11.setFont(font)
        self.label_11.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_11.setText(_translate("widget", "位置示意图"))
        # 设置label_3
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setText(_translate("widget", "尺寸参数"))
        # 设置lable_7
        self.label_7.setFont(font)
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_7.setText(_translate("widget", "角度初始值"))
        # 设置lable_13
        self.label_13.setFont(font)
        self.label_13.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_13.setText(_translate("widget", "腿部选择"))
        # 设置lable_14
        self.label_14.setFont(font)
        self.label_14.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_14.setText(_translate("widget", "角度补偿值"))
        # 设置lable_4
        font1 = QtGui.QFont()
        font1.setFamily("Arial")
        font1.setPointSize(10)
        self.label_4.setFont(font1)
        self.label_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_4.setText(_translate("widget", "L0"))
        # 设置lable_5
        self.label_5.setFont(font1)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setText(_translate("widget", "L1"))
        # 设置lable_6
        self.label_6.setFont(font1)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_6.setText(_translate("widget", "L2"))
        # 设置lable_8
        self.label_8.setFont(font1)
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_8.setText(_translate("widget", "α"))
        # 设置lable_9
        self.label_9.setFont(font1)
        self.label_9.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_9.setText(_translate("widget", "β"))
        # 设置lable_10
        self.label_10.setFont(font1)
        self.label_10.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_10.setText(_translate("widget", "γ"))
        # 设置lable_15
        self.label_15.setFont(font1)
        self.label_15.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_15.setText(_translate("widget", "α‘"))
        # 设置lable_16
        self.label_16.setFont(font1)
        self.label_16.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_16.setText(_translate("widget", "β’"))
        # 设置lable_17
        self.label_17.setFont(font1)
        self.label_17.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_17.setText(_translate("widget", "γ‘"))
        # 设置lable_18
        self.label_18.setFont(font)
        self.label_18.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_18.setText(_translate("widget", "基准坐标"))
        # 设置lable_19
        self.label_19.setFont(font)
        self.label_19.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_19.setText(_translate("widget", "角度范围"))
        # 设置lable_25
        self.label_25.setFont(font1)
        self.label_25.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_25.setText(_translate("widget", "P0_x"))
        # 设置lable_28
        self.label_28.setFont(font1)
        self.label_28.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_28.setText(_translate("widget", "P0_α"))
        # 设置lable_26
        self.label_26.setFont(font1)
        self.label_26.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_26.setText(_translate("widget", "P0_y"))
        # 设置lable_29
        self.label_29.setFont(font1)
        self.label_29.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_29.setText(_translate("widget", "P0_β"))
        # 设置lable_27
        self.label_27.setFont(font1)
        self.label_27.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_27.setText(_translate("widget", "P0_z"))
        # 设置lable_30
        self.label_30.setFont(font1)
        self.label_30.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_30.setText(_translate("widget", "P0_γ"))
        # 设置lable_21
        self.label_21.setFont(font1)
        self.label_21.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_21.setText(_translate("widget", "β"))
        # 设置lable_20
        self.label_20.setFont(font1)
        self.label_20.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_20.setText(_translate("widget", "α"))
        # 设置lable_22
        self.label_22.setFont(font1)
        self.label_22.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_22.setText(_translate("widget", "γ"))
        # 设置pushButton
        self.pushButton.setFont(font)
        self.pushButton.setText(_translate("widget", "保存"))
        # 设置pushButton_2
        self.pushButton_2.setFont(font)
        self.pushButton_2.setText(_translate("widget", "退出"))
    #初始化控件
    def init_ComboBox_DoubleSpinBox(self,hexapod:Hexapod):
        self.comboBox.clear()
        leg_name_list = ["MiddleRight","FrontRight","FrontLeft","MiddleLeft","RearLeft","RearRight"]
        self.comboBox.addItems(leg_name_list)
        self.comboBox.setCurrentIndex(0)
        index = self.comboBox.currentIndex()
        self.doubleSpinBox.setValue(hexapod.legs[index].lengths[0])
        self.doubleSpinBox_2.setValue(hexapod.legs[index].lengths[1])
        self.doubleSpinBox_3.setValue(hexapod.legs[index].lengths[2])

        self.doubleSpinBox_4.setMinimum(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_4.setMaximum(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_4.setValue(hexapod.legs[index].angles[0]*180/math.pi)
        self.doubleSpinBox_5.setMinimum(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_5.setMaximum(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_5.setValue(hexapod.legs[index].angles[1]*180/math.pi)
        self.doubleSpinBox_6.setMinimum(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_6.setMaximum(hexapod.legs[index].angle_limits[2][1]*180/math.pi)
        self.doubleSpinBox_6.setValue(hexapod.legs[index].angles[2]*180/math.pi)

        self.doubleSpinBox_7.setMinimum(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_7.setMaximum(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_7.setValue(hexapod.legs[index].angle_bias[0]*180/math.pi)
        self.doubleSpinBox_8.setMinimum(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_8.setMaximum(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_8.setValue(hexapod.legs[index].angle_bias[1]*180/math.pi)
        self.doubleSpinBox_9.setMinimum(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_9.setMaximum(hexapod.legs[index].angle_limits[2][1]*180/math.pi)
        self.doubleSpinBox_9.setValue(hexapod.legs[index].angle_bias[2]*180/math.pi)

        self.doubleSpinBox_10.setValue(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_11.setValue(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_12.setValue(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_13.setValue(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_14.setValue(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_15.setValue(hexapod.legs[index].angle_limits[2][1]*180/math.pi)

        self.doubleSpinBox_16.setValue(hexapod.legs[index].axis_x)
        self.doubleSpinBox_17.setValue(hexapod.legs[index].axis_y)
        self.doubleSpinBox_18.setValue(hexapod.legs[index].axis_z)
        self.doubleSpinBox_19.setValue(hexapod.legs[index].axis_alpha*180/math.pi)
        self.doubleSpinBox_20.setValue(hexapod.legs[index].axis_beta*180/math.pi)
        self.doubleSpinBox_21.setValue(hexapod.legs[index].axis_gama*180/math.pi)
    #更新DoubleSpinBox
    def update_comBoBox(self,hexapod:Hexapod):
        index = self.comboBox.currentIndex()
        self.doubleSpinBox.setValue(hexapod.legs[index].lengths[0])
        self.doubleSpinBox_2.setValue(hexapod.legs[index].lengths[1])
        self.doubleSpinBox_3.setValue(hexapod.legs[index].lengths[2])

        self.doubleSpinBox_4.setMinimum(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_4.setMaximum(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_4.setValue(hexapod.legs[index].angles[0]*180/math.pi)
        self.doubleSpinBox_5.setMinimum(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_5.setMaximum(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_5.setValue(hexapod.legs[index].angles[1]*180/math.pi)
        self.doubleSpinBox_6.setMinimum(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_6.setMaximum(hexapod.legs[index].angle_limits[2][1]*180/math.pi)
        self.doubleSpinBox_6.setValue(hexapod.legs[index].angles[2]*180/math.pi)

        self.doubleSpinBox_7.setMinimum(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_7.setMaximum(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_7.setValue(hexapod.legs[index].angle_bias[0]*180/math.pi)
        self.doubleSpinBox_8.setMinimum(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_8.setMaximum(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_8.setValue(hexapod.legs[index].angle_bias[1]*180/math.pi)
        self.doubleSpinBox_9.setMinimum(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_9.setMaximum(hexapod.legs[index].angle_limits[2][1]*180/math.pi)
        self.doubleSpinBox_9.setValue(hexapod.legs[index].angle_bias[2]*180/math.pi)

        self.doubleSpinBox_10.setValue(hexapod.legs[index].angle_limits[0][0]*180/math.pi)
        self.doubleSpinBox_11.setValue(hexapod.legs[index].angle_limits[0][1]*180/math.pi)
        self.doubleSpinBox_12.setValue(hexapod.legs[index].angle_limits[1][0]*180/math.pi)
        self.doubleSpinBox_13.setValue(hexapod.legs[index].angle_limits[1][1]*180/math.pi)
        self.doubleSpinBox_14.setValue(hexapod.legs[index].angle_limits[2][0]*180/math.pi)
        self.doubleSpinBox_15.setValue(hexapod.legs[index].angle_limits[2][1]*180/math.pi)

        self.doubleSpinBox_16.setValue(hexapod.legs[index].axis_x)
        self.doubleSpinBox_17.setValue(hexapod.legs[index].axis_y)
        self.doubleSpinBox_18.setValue(hexapod.legs[index].axis_z)
        self.doubleSpinBox_19.setValue(hexapod.legs[index].axis_alpha*180/math.pi)
        self.doubleSpinBox_20.setValue(hexapod.legs[index].axis_beta*180/math.pi)
        self.doubleSpinBox_21.setValue(hexapod.legs[index].axis_gama*180/math.pi)
    #保存设置
    def save_button(self,hexapod:Hexapod):
        index = self.comboBox.currentIndex()
        L0 = self.doubleSpinBox.value()
        L1 = self.doubleSpinBox_2.value()
        L2 = self.doubleSpinBox_3.value()
        lengths = [L0,L1,L2]
        hexapod.legs[index].update_lengths(lengths)

        alpha = self.doubleSpinBox_4.value()*math.pi/180
        beta = self.doubleSpinBox_5.value()*math.pi/180
        gama = self.doubleSpinBox_6.value()*math.pi/180
        angle = [alpha,beta,gama]
        hexapod.legs[index].update_pose(angle)

        alpha_bias = self.doubleSpinBox_7.value()*math.pi/180
        beta_bias = self.doubleSpinBox_8.value()*math.pi/180
        gama_bias = self.doubleSpinBox_9.value()*math.pi/180
        angle_bias = [alpha_bias,beta_bias,gama_bias]
        hexapod.legs[index].update_angle_bias(angle_bias)

        alpha_min = self.doubleSpinBox_10.value()*math.pi/180
        alpha_max = self.doubleSpinBox_11.value()*math.pi/180
        beta_min = self.doubleSpinBox_12.value()*math.pi/180
        beta_max = self.doubleSpinBox_13.value()*math.pi/180
        gama_min = self.doubleSpinBox_14.value()*math.pi/180
        gama_max = self.doubleSpinBox_15.value()*math.pi/180
        angle_limits = [(alpha_min,alpha_max),(beta_min,beta_max),(gama_min,gama_max)]
        hexapod.legs[0].update_angle_limits(angle_limits)

        P0_x = self.doubleSpinBox_16.value()
        P0_y = self.doubleSpinBox_17.value()
        P0_z = self.doubleSpinBox_18.value()
        P0_alpha = self.doubleSpinBox_19.value()*math.pi/180
        P0_beta = self.doubleSpinBox_20.value()*math.pi/180
        P0_gama = self.doubleSpinBox_21.value()*math.pi/180
        datumaxis = (P0_x,P0_y,P0_z,P0_alpha,P0_beta,P0_gama)
        hexapod.legs[index].update_datumaxis(datumaxis)

        self.update_leg_aignal.emit(hexapod)
    #打开页面
    def show_widget(self,hexapod:Hexapod):
        self.init_ComboBox_DoubleSpinBox(hexapod)
        self.widget.show()
    #关闭页面
    def cancle(self):
        self.widget.close()

#定义myWidget3(修改串口参数)
class myWidget3(QWidget):
    #初始化
    def __init__(self,SERthread:SERIALThread):
        super().__init__()
        _translate = QtCore.QCoreApplication.translate
        self.widget = QtWidgets.QWidget()
        #设置窗口模态，使其打开时中止应用程序交互
        self.widget.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_UI(self.widget)
        self.thread = SERthread
        self.init_Control()
        self.comboBox.clicked.connect(lambda: self.find_com())
        self.radioButton.clicked.connect(lambda: self.change_serial_status())
        self.pushButton.clicked.connect(lambda: self.close_widget())
    # 初始化控件
    def init_UI(self, widget: QWidget):
        widget.setObjectName("myWidget3")
        widget.setFixedSize(240, 275)
        #定义frame
        self.frame = QtWidgets.QFrame(parent=widget)
        self.frame.setGeometry(QtCore.QRect(20, 10, 201, 61))
        self.frame.setObjectName("frame")
        #定义label(串口选择)
        self.label = QtWidgets.QLabel(parent=self.frame)
        self.label.setGeometry(QtCore.QRect(0, 0, 61, 21))
        self.label.setObjectName("label")
        #定义comboBox
        self.comboBox = myComboBox(parent=self.frame)
        self.comboBox.setGeometry(QtCore.QRect(0, 30, 201, 22))
        self.comboBox.setObjectName("comboBox")
        #定义frame_2
        self.frame_2 = QtWidgets.QFrame(parent=widget)
        self.frame_2.setGeometry(QtCore.QRect(20, 70, 201, 131))
        self.frame_2.setObjectName("frame_2")
        #定义widget1
        self.widget1 = QtWidgets.QWidget(parent=self.frame_2)
        self.widget1.setGeometry(QtCore.QRect(0, 10, 201, 116))
        self.widget1.setObjectName("widget")
        #定义表单布局控件
        self.formLayout = QtWidgets.QFormLayout(self.widget1)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setHorizontalSpacing(20)
        self.formLayout.setVerticalSpacing(10)
        self.formLayout.setObjectName("formLayout")
        #定义label_2(波特率)
        self.label_2 = QtWidgets.QLabel(parent=self.widget1)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        #定义comboBox_2
        self.comboBox_2 = QtWidgets.QComboBox(parent=self.widget1)
        self.comboBox_2.setObjectName("comboBox_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.comboBox_2)
        # 定义label_3(停止位)
        self.label_3 = QtWidgets.QLabel(parent=self.widget1)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)
        # 定义comboBox_3
        self.comboBox_3 = QtWidgets.QComboBox(parent=self.widget1)
        self.comboBox_3.setObjectName("comboBox_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.comboBox_3)
        # 定义label_4(数据位)
        self.label_4 = QtWidgets.QLabel(parent=self.widget1)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4)
        # 定义comboBox_4
        self.comboBox_4 = QtWidgets.QComboBox(parent=self.widget1)
        self.comboBox_4.setObjectName("comboBox_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.comboBox_4)
        # 定义label_4(校验位)
        self.label_5 = QtWidgets.QLabel(parent=self.widget1)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_5)
        # 定义comboBox_5
        self.comboBox_5 = QtWidgets.QComboBox(parent=self.widget1)
        self.comboBox_5.setObjectName("comboBox_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.comboBox_5)
        #定义frame_3
        self.frame_3 = QtWidgets.QFrame(parent=widget)
        self.frame_3.setGeometry(QtCore.QRect(20, 199, 201, 31))
        self.frame_3.setObjectName("frame_3")
        #定义widget2
        self.widget2 = QtWidgets.QWidget(parent=self.frame_3)
        self.widget2.setGeometry(QtCore.QRect(0, 3, 201, 31))
        self.widget2.setObjectName("widget2")
        #定义水平布局控件
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        #定义label_6(串口操作)
        self.label_6 = QtWidgets.QLabel(parent=self.widget2)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout.addWidget(self.label_6)
        #定义radioButton
        self.radioButton = QtWidgets.QRadioButton(parent=self.widget2)
        self.radioButton.setObjectName("radioButton")
        self.horizontalLayout.addWidget(self.radioButton)
        #定义pushButton
        self.pushButton = QtWidgets.QPushButton(parent=widget)
        self.pushButton.setGeometry(QtCore.QRect(80, 240, 75, 24))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(widget)
        QtCore.QMetaObject.connectSlotsByName(widget)
    #控件字体设置
    def retranslateUi(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("Widget", "串口连接"))
        # label字体设置
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setText(_translate("Widget", "串口选择"))
        # label_2字体设置
        self.label_2.setFont(font)
        self.label_2.setText(_translate("Widget", "波特率"))
        # label_3字体设置
        self.label_3.setFont(font)
        self.label_3.setText(_translate("Widget", "停止位"))
        # label_4字体设置
        self.label_4.setFont(font)
        self.label_4.setText(_translate("Widget", "数据位"))
        # label_5字体设置
        self.label_5.setFont(font)
        self.label_5.setText(_translate("Widget", "校验位"))
        # label_6字体设置
        self.label_6.setFont(font)
        self.label_6.setText(_translate("Widget", "串口操作"))
        # radioButton字体设置
        self.radioButton.setFont(font)
        self.radioButton.setText(_translate("Widget", "打开串口"))
        # pushButton字体设置
        self.pushButton.setFont(font)
        self.pushButton.setText(_translate("Widget", "退出窗口"))
    #初始化控件
    def init_Control(self):
        asyncio.run_coroutine_threadsafe(self.thread.scan(), self.thread.loop)
        asyncio.run_coroutine_threadsafe(self.thread.get_paramters(), self.thread.loop)
        asyncio.run_coroutine_threadsafe(self.thread.read_is_open(), self.thread.loop)
    #更新参数comboBox
    def update_para_comboBox(self,paramters):
        name, port, baudrate, bytesize, stopbites, parity = paramters
        baudrateList = [2400, 4800, 9600, 14400, 19200, 38400, 43000, 57600, 76800, 115200, 128000, 230400, 256000,
                        460800, 921600]
        self.comboBox_2.clear()
        self.comboBox_2.addItems([str(item) for item in baudrateList])
        baudrateIndex = [index for index, value in enumerate(baudrateList) if value == baudrate]
        self.comboBox_2.setCurrentIndex(baudrateIndex[0])
        stopbitesList = [1, 1.5, 2]
        self.comboBox_3.clear()
        self.comboBox_3.addItems([str(item) for item in stopbitesList])
        stopbitesIndex = [index for index, value in enumerate(stopbitesList) if value == stopbites]
        self.comboBox_3.setCurrentIndex(stopbitesIndex[0])
        bytesizeList = [5, 6, 7, 8]
        self.comboBox_4.clear()
        self.comboBox_4.addItems([str(item) for item in bytesizeList])
        bytesizeIndex = [index for index, value in enumerate(bytesizeList) if value == bytesize]
        self.comboBox_4.setCurrentIndex(bytesizeIndex[0])
        parityList = ['None', 'Odd', 'Even']
        self.comboBox_5.clear()
        self.comboBox_5.addItems(parityList)
        parityIndex = [index for index, value in enumerate(parityList) if value[0] == parity]
        self.comboBox_5.setCurrentIndex(parityIndex[0])
    #更新pushButton
    def update_pushButton(self,is_open_signal):
        if is_open_signal:
            self.radioButton.setChecked(True)
            self.radioButton.setText('关闭串口')
        else:
            self.radioButton.setChecked(False)
            self.radioButton.setText('打开串口')
    #搜索可用串口
    def find_com(self):
        self.comboBox.setEnabled(False)
        asyncio.run_coroutine_threadsafe(self.thread.scan(), self.thread.loop)
    #更新搜索comboBox
    def update_select_comboBox(self,devices_list):
        self.comboBox.clear()
        self.comboBox.addItems([item.description for item in devices_list])
        self.comboBox.setEnabled(True)
        self.devices_list = devices_list
    #打开关闭串口
    def change_serial_status(self):
        if self.radioButton.isChecked():
            index = self.comboBox.currentIndex()
            name = self.devices_list[index].name
            port = self.devices_list[index].device
            baudrate = int(self.comboBox_2.currentText())
            stopbites = float(self.comboBox_3.currentText())
            bytesize = int(self.comboBox_4.currentText())
            parity = self.comboBox_5.currentText()
            paramters = (name,port,baudrate,bytesize,stopbites,parity)
            self.radioButton.setEnabled(False)
            asyncio.run_coroutine_threadsafe(self.thread.update_paramters(paramters), self.thread.loop)
            asyncio.run_coroutine_threadsafe(self.thread.connect_ser(), self.thread.loop)
        else:
            self.radioButton.setEnabled(False)
            asyncio.run_coroutine_threadsafe(self.thread.disconnect_ser(), self.thread.loop)
    # 打开串口
    def connect_ser(self, connect_res):
        is_open = connect_res
        if is_open:
            self.radioButton.setText('关闭串口')
        else:
            QMessageBox.warning(self, 'Warning', '串口打开失败')
            self.radioButton.setChecked(False)
        self.radioButton.setEnabled(True)
    # 关闭串口
    def disconnect_ser(self, disconnect_res):
        is_open = disconnect_res
        if is_open:
            QMessageBox.warning(self, 'Warning', '串口关闭失败')
            self.radioButton.setChecked(True)
        else:
            self.radioButton.setText('打开串口')
        self.radioButton.setEnabled(True)

    #打开页面
    def show_widget(self):
        self.thread.devices_list.connect(self.update_select_comboBox)
        self.thread.connect_res.connect(self.connect_ser)
        self.thread.disconnect_res.connect(self.disconnect_ser)
        self.thread.paramters_list.connect(self.update_para_comboBox)
        self.thread.is_open_signal.connect(self.update_pushButton)
        self.init_Control()
        self.widget.show()
    #关闭页面
    def close_widget(self):
        self.thread.devices_list.disconnect(self.update_select_comboBox)
        self.thread.connect_res.disconnect(self.connect_ser)
        self.thread.disconnect_res.disconnect(self.disconnect_ser)
        self.thread.paramters_list.disconnect(self.update_para_comboBox)
        self.thread.is_open_signal.disconnect(self.update_pushButton)
        self.widget.close()

#定义myWidget4(修改蓝牙参数)
class myWidget4(QWidget):
    #初始化
    def __init__(self, BLTthread:BLTThread):
        super().__init__()
        _translate = QtCore.QCoreApplication.translate
        self.widget = QtWidgets.QWidget()
        # 设置窗口模态，使其打开时中止应用程序交互
        self.widget.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_UI(self.widget)
        self.thread = BLTthread
        self.init_Control()

        self.comboBox.currentIndexChanged.connect(lambda: self.update_label())
        self.pushButton_3.clicked.connect(lambda: self.search_bluetooth())
        self.radioButton.clicked.connect(lambda: self.connect_button())
        self.pushButton.clicked.connect(lambda: self.save_button())
        self.pushButton_2.clicked.connect(lambda: self.close_widget())

    #初始化界面
    def init_UI(self, widget: QWidget):
        widget.setObjectName("myWidget4")
        widget.setFixedSize(245, 400)
        #定义frame
        self.frame = QtWidgets.QFrame(parent=widget)
        self.frame.setGeometry(QtCore.QRect(19, 9, 211, 61))
        self.frame.setObjectName("frame")
        #定义label(蓝牙选择)
        self.label = QtWidgets.QLabel(parent=self.frame)
        self.label.setGeometry(QtCore.QRect(0, 0, 51, 21))
        self.label.setObjectName("label")
        #定义comboBox
        self.comboBox = myComboBox(parent=self.frame)
        self.comboBox.setGeometry(QtCore.QRect(0, 30, 211, 22))
        self.comboBox.setObjectName("comboBox")
        #定义pushButton_3
        self.pushButton_3 = QtWidgets.QPushButton(parent=self.frame)
        self.pushButton_3.setGeometry(QtCore.QRect(150, 0, 61, 24))
        self.pushButton_3.setObjectName("pushButton_3")
        #定义frame_2
        self.frame_2 = QtWidgets.QFrame(parent=widget)
        self.frame_2.setGeometry(QtCore.QRect(20, 70, 211, 111))
        self.frame_2.setObjectName("frame_2")
        #定义label_2(蓝牙属性)
        self.label_2 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_2.setGeometry(QtCore.QRect(0, 0, 61, 16))
        self.label_2.setObjectName("label_2")
        #定义label_3(设备名称)
        self.label_3 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_3.setGeometry(QtCore.QRect(0, 30, 71, 16))
        self.label_3.setObjectName("label_3")
        #定义label_4
        self.label_4 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_4.setGeometry(QtCore.QRect(80, 30, 131, 16))
        self.label_4.setObjectName("label_4")
        #定义label_5(设备地址)
        self.label_5 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_5.setGeometry(QtCore.QRect(0, 60, 61, 16))
        self.label_5.setObjectName("label_5")
        #定义label_6
        self.label_6 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_6.setGeometry(QtCore.QRect(80, 60, 131, 16))
        self.label_6.setObjectName("label_6")
        #定义label_7(信号强度)
        self.label_7 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_7.setGeometry(QtCore.QRect(0, 90, 61, 16))
        self.label_7.setObjectName("label_7")
        #定义label_8
        self.label_8 = QtWidgets.QLabel(parent=self.frame_2)
        self.label_8.setGeometry(QtCore.QRect(80, 90, 131, 16))
        self.label_8.setObjectName("label_8")
        #定义frame_3
        self.frame_3 = QtWidgets.QFrame(parent=widget)
        self.frame_3.setGeometry(QtCore.QRect(19, 179, 211, 141))
        self.frame_3.setObjectName("frame_3")
        #定义label_9(蓝牙设置)
        self.label_9 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_9.setGeometry(QtCore.QRect(0, 10, 71, 16))
        self.label_9.setObjectName("label_9")
        #定义label_10(send_uuid)
        self.label_10 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_10.setGeometry(QtCore.QRect(0, 40, 71, 16))
        self.label_10.setObjectName("label_10")
        #定义label_11(receive_uuid)
        self.label_11 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_11.setGeometry(QtCore.QRect(0, 90, 91, 16))
        self.label_11.setObjectName("label_11")
        #定义lineEdit
        self.lineEdit = QtWidgets.QLineEdit(parent=self.frame_3)
        self.lineEdit.setGeometry(QtCore.QRect(0, 60, 211, 20))
        self.lineEdit.setObjectName("lineEdit")
        #定义lineEdit_2
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=self.frame_3)
        self.lineEdit_2.setGeometry(QtCore.QRect(0, 110, 211, 20))
        self.lineEdit_2.setObjectName("lineEdit_2")
        #定义frame_4
        self.frame_4 = QtWidgets.QFrame(parent=widget)
        self.frame_4.setGeometry(QtCore.QRect(19, 319, 211, 31))
        self.frame_4.setObjectName("frame_4")
        #定义label_12(蓝牙操作)
        self.label_12 = QtWidgets.QLabel(parent=self.frame_4)
        self.label_12.setGeometry(QtCore.QRect(0, 10, 61, 16))
        self.label_12.setObjectName("label_12")
        #定义radioButton
        self.radioButton = QtWidgets.QRadioButton(parent=self.frame_4)
        self.radioButton.setGeometry(QtCore.QRect(110, 10, 95, 20))
        self.radioButton.setObjectName("radioButton")
        #定义frame_5
        self.frame_5 = QtWidgets.QFrame(parent=widget)
        self.frame_5.setGeometry(QtCore.QRect(19, 349, 211, 41))
        self.frame_5.setObjectName("frame_5")
        #定义pushButton
        self.pushButton = QtWidgets.QPushButton(parent=self.frame_5)
        self.pushButton.setGeometry(QtCore.QRect(20, 10, 61, 24))
        self.pushButton.setObjectName("pushButton")
        #定义pushButton_2
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.frame_5)
        self.pushButton_2.setGeometry(QtCore.QRect(130, 10, 61, 24))
        self.pushButton_2.setObjectName("pushButton_2")

        self.retranslateUi(widget)
        QtCore.QMetaObject.connectSlotsByName(widget)
    # 控件字体设置
    def retranslateUi(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("Widget", "蓝牙连接"))
        # 设置label
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setText(_translate("Widget", "蓝牙选择"))
        # 设置label_2
        self.label_2.setFont(font)
        self.label_2.setText(_translate("Widget", "蓝牙属性"))
        # 设置label_3
        self.label_3.setFont(font)
        self.label_3.setText(_translate("Widget", "设备名称："))
        # 设置label_4
        font1 = QtGui.QFont()
        font1.setFamily("Arial")
        font1.setPointSize(10)
        self.label_4.setFont(font1)
        self.label_4.setText(_translate("Widget", ""))
        # 设置label_5
        self.label_5.setFont(font)
        self.label_5.setText(_translate("Widget", "设备地址："))
        # 设置label_6
        self.label_6.setFont(font1)
        self.label_6.setText(_translate("Widget", ""))
        # 设置label_7
        self.label_7.setFont(font)
        self.label_7.setText(_translate("Widget", "信号强度："))
        # 设置label_8
        self.label_8.setFont(font1)
        self.label_8.setText(_translate("Widget", ""))
        # 设置label_9
        self.label_9.setFont(font)
        self.label_9.setText(_translate("Widget", "蓝牙设置"))
        # 设置label_10
        self.label_10.setFont(font1)
        self.label_10.setText(_translate("Widget", "send_uuid"))
        # 设置label_11
        self.label_11.setFont(font1)
        self.label_11.setText(_translate("Widget", "receive_uuid"))
        # 设置label_12
        self.label_12.setFont(font)
        self.label_12.setText(_translate("Widget", "蓝牙操作"))
        # 设置radioButton
        self.radioButton.setFont(font)
        self.radioButton.setText(_translate("Widget", "连接"))
        # 设置pushButton
        self.pushButton.setFont(font)
        self.pushButton.setText(_translate("Widget", "保存设置"))
        # 设置pushButton_2
        self.pushButton_2.setFont(font)
        self.pushButton_2.setText(_translate("Widget", "退出"))
        # 设置pushButton_3
        self.pushButton_3.setFont(font)
        self.pushButton_3.setText(_translate("Widget", "搜索蓝牙"))
    # 初始化控件
    def init_Control(self):
        self.devices = []
        self.comboBox.clear()
        self.thread.uuid_list.connect(self.update_lineEdit)
        asyncio.run_coroutine_threadsafe(self.thread.read_uuid(), self.thread.loop)
        self.thread.is_open_signal.connect(self.update_radioButton)
        asyncio.run_coroutine_threadsafe(self.thread.read_is_open(), self.thread.loop)
    #更新lineEdit
    def update_lineEdit(self, uuid_list):
        send_uuid, receive_uuid = uuid_list
        self.lineEdit.setText(send_uuid)
        self.lineEdit_2.setText(receive_uuid)
    #更新radioButton
    def update_radioButton(self,is_open_sugnal):
        if is_open_sugnal:
            self.radioButton.setChecked(True)
            self.radioButton.setText('断开连接')
        else:
            self.radioButton.setChecked(False)
            self.radioButton.setText('连接')
    #搜索蓝牙
    def search_bluetooth(self):
        self.pushButton_3.setEnabled(False)
        self.pushButton_3.setText("搜索中...")
        asyncio.run_coroutine_threadsafe(self.thread.scan(), self.thread.loop)
    #更新comboBox
    def update_combobox(self,devices):
        self.comboBox.currentIndexChanged.disconnect()
        self.comboBox.clear()
        self.devices = [item for item in devices if item.name]
        self.comboBox.addItems([item.name for item in self.devices])
        self.comboBox.setCurrentIndex(-1)
        self.comboBox.currentIndexChanged.connect(lambda: self.update_label())
        self.pushButton_3.setEnabled(True)
        self.pushButton_3.setText("搜索蓝牙")
    #更新label
    def update_label(self):
        index = self.comboBox.currentIndex()
        if index >= 0 and index < len(self.devices):
            self.label_4.setText(str(self.devices[index].name))
            self.label_6.setText(str(self.devices[index].address))
            self.label_8.setText(str(self.devices[index].rssi)+"(dbm)")
    #连接蓝牙按钮
    def connect_button(self):
        self.radioButton.setEnabled(False)
        if self.radioButton.isChecked():
            target_name = self.label_4.text()
            target_address = self.label_6.text()
            send_uuid = self.lineEdit.text()
            receive_uuid = self.lineEdit_2.text()
            paramters = (target_address,target_name,send_uuid,receive_uuid)
            asyncio.run_coroutine_threadsafe(self.thread.update_paramters(paramters), self.thread.loop)
            asyncio.run_coroutine_threadsafe(self.thread.connect_blt(self.thread.bluetooth.target_address), self.thread.loop)
            self.radioButton.setText("正在连接...")
        else:
            asyncio.run_coroutine_threadsafe(self.thread.disconnect_blt(), self.thread.loop)
            self.radioButton.setText("正在断开...")
    #打开蓝牙
    def connect_blt(self,connect_res):
        is_open = connect_res
        if is_open:
            self.radioButton.setText('断开连接')
        else:
            QMessageBox.warning(self, 'Warning', '蓝牙连接失败')
            self.radioButton.setText("连接")
            self.radioButton.setChecked(False)
        self.radioButton.setEnabled(True)
    #关闭蓝牙
    def disconnect_blt(self,disconnect_res):
        is_open = disconnect_res
        if is_open:
            QMessageBox.warning(self, 'Warning', '断开连接失败')
            self.radioButton.setText("断开连接")
            self.radioButton.setChecked(True)
        else:
            self.radioButton.setText('连接')
        self.radioButton.setEnabled(True)
    #保存设置
    def save_button(self):
        send_uuid = self.lineEdit.text()
        receive_uuid = self.lineEdit_2.text()
        uuid_list = (send_uuid,receive_uuid)
        asyncio.run_coroutine_threadsafe(self.thread.update_uuid(uuid_list), self.thread.loop)

    # 打开页面
    def show_widget(self):
        self.thread.devices_list.connect(self.update_combobox)
        self.thread.connect_res.connect(self.connect_blt)
        self.thread.disconnect_res.connect(self.disconnect_blt)
        self.init_Control()
        self.widget.show()
    # 关闭页面
    def close_widget(self):
        self.thread.devices_list.disconnect(self.update_combobox)
        self.thread.connect_res.disconnect(self.connect_blt)
        self.thread.disconnect_res.disconnect(self.disconnect_blt)
        self.save_button()
        self.widget.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hexapod = Hexapod()
    ser = Serial()
    blt = Bluetooth()
    ui = mainWindow(hexapod,ser,blt)

    sys.exit(app.exec())