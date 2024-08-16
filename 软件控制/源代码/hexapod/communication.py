import asyncio
import struct

import serial
import time
import serial.tools.list_ports
from bleak import BleakScanner, BleakClient

from constant import *
#定义串口类
class Serial:
    #初始化
    def __init__(self, name='None', port=PORT, baudrate=BAUDRATE, bytesize=BYTESIZE, stopbites=STOPBITES):
        self.name = name
        self.is_open = False
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbites = stopbites
        self.parity = 'N'
        self.serial = None
    #搜索串口
    def select_com(self):
        return serial.tools.list_ports.comports()
    #修改串口号
    def change_port(self,new_port):
        self.port = new_port
    #修改波特率
    def change_baudrate(self,new_baudrate):
        self.baudrate = new_baudrate
    #修改数据位
    def change_bytesize(self,new_bytesize):
        self.bytesize = new_bytesize
    #修改停止位
    def change_stopbites(self,new_stopbites):
        self.stopbites = new_stopbites
    #修改检验位
    def change_parity(self,new_parity):
        self.parity = new_parity[0]
    #修改名称
    def change_name(self,new_name):
        self.name = new_name
    #修改参数
    def update_paramters(self,paramters):
        name, port, baudrate, bytesize, stopbites, parity = paramters
        self.change_name(name)
        self.change_port(port)
        self.change_baudrate(baudrate)
        self.change_bytesize(bytesize)
        self.change_stopbites(stopbites)
        self.change_parity(parity)
    #打开串口
    def open_serial(self):
        try:
            self.serial = serial.Serial(port=self.port,baudrate=self.baudrate,bytesize=self.bytesize,
                                        parity=self.parity,stopbits=self.stopbites)
            self.name = self.serial.name
            self.is_open = True
            return True
        except serial.SerialException:
            return False
    #关闭串口
    def close_serial(self):
        try:
            self.serial.close()
            self.is_open = False
            return True
        except serial.SerialException:
            return False
    #获取参数
    def get_paramters(self):
        name = self.name
        port = self.port
        baudrate = self.baudrate
        bytesize = self.bytesize
        stopbites = self.stopbites
        parity = self.parity
        paramters = (name, port, baudrate, bytesize, stopbites, parity)
        return paramters
    #串口发送数据
    def send_info(self, data):
        self.serial.write(data.encode('utf-8'))
    #串口接收数据
    def receive_data(self):
        if self.serial.in_waiting > 0:
            data = self.serial.read_all().decode('utf-8').strip()
            return data
        return None

#蓝牙类
class Bluetooth:
    #初始化
    def __init__(self,targetAddress=TARGETADDRESS,targetName=TARGETNAME,send_uuid=SENDUUID,
                 receive_uuid=RECEIVEUUID):
        self.client_socket = None
        self.is_open = False
        self.target_address = targetAddress
        self.target_name = targetName
        self.send_uuid = send_uuid
        self.receive_uuid = receive_uuid
    #搜索可用蓝牙
    async def search_devices(self):
        devices = await BleakScanner.discover()
        return devices
    #连接蓝牙
    async def connect(self, address):
        try:
            self.client_socket = BleakClient(address)
            await self.client_socket.connect()
            self.is_open = True
            return True
        except:
            return False
    #发送数据
    async def send(self, message):
        if self.client_socket and self.client_socket.is_connected:
            await self.client_socket.write_gatt_char(self.send_uuid, message.encode())
    #接收数据
    async def receive(self):
        if self.client_socket and self.client_socket.is_connected:
            data = await self.client_socket.read_gatt_char(self.receive_uuid)
            return data
    #断开连接
    async def disconnect(self):
        if self.client_socket and self.client_socket.is_connected:
            await self.client_socket.disconnect()
            self.is_open = False
            return True
        else:
            return False
    #更新参数
    def update_paramters(self,paramters):
        target_address, terget_name, send_uuid, receive_uuid = paramters
        self.target_address = target_address
        self.target_name = terget_name
        self.send_uuid = send_uuid
        self.receive_uuid = receive_uuid
    #更新uuid
    def update_uuid(self,uuid_list):
        send_uuid, receive_uuid = uuid_list
        self.send_uuid = send_uuid
        self.receive_uuid = receive_uuid

async def main1(bluetooth):
    # device = asyncio.run(bluetooth.search_devices())
    # print([item.name for item in device])
    # print([item.address for item in device])
    # print([item.rssi for item in device])
    await bluetooth.connect(TARGETADDRESS)
    print(bluetooth.client_socket.is_connected)
    await bluetooth.send('#000P1500T1000!')
    await asyncio.sleep(5)
    # asyncio.run(bluetooth.receive())

async def main2(bluetooth):
    await bluetooth.disconnect()
    print(bluetooth.client_socket.is_connected)

if __name__ == "__main__":
    ser = Serial()
    devices = ser.select_com()
    list = ser.open_serial()
    ser.close_serial()
    ser.open_serial()
    ser.get_paramters()
    print(list)
    # bluetooth = Bluetooth()
    # asyncio.run(main1(bluetooth))
    #
    # asyncio.run(main2(bluetooth))

