import math
#Body参数
BODY_SIZE=(5,10,10)
BODY_ATTITUDE=(0,0,10,0,0,0)
#Leg参数
LEG_LENGTH=[10,10,10]
LEG_ANGLE=[0,0,0]
ANGLE_BIAS=[0,0,0]
ANGLE_LIMITS=[(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)]
#Hexapod参数
HEXAPOD_LEG_LENGTH=[[10,10,10],[10,10,10],[10,10,10],[10,10,10],[10,10,10],[10,10,10]]
HEXAPOD_LEG_ANGLE=[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
HEXAPOD_LEG_ANGLE1=[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
HEXAPOD_ANGLE_BIAS=[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
HEXAPOD_ANGLE_LIMITS=[[(-math.pi/2,math.pi/2),(-math.pi/2, math.pi/2),(-math.pi/2, math.pi/2)],
                      [(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)],
                      [(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)],
                      [(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)],
                      [(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)],
                      [(-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2), (-math.pi/2, math.pi/2)]]
HEXAPOD_LEG_ROT=((0,0,0),(0,0,math.pi/6),(0,0,5*math.pi/6),(0,0,math.pi),(0,0,-5*math.pi/6),(0,0,-math.pi/6))
LEG_ID_NAMES = {0: "MiddleRight", 1:"FrontRight", 2:"FrontLeft",
                3: "MiddleLeft", 4:"RearLeft", 5:"RearRight"}
STATE_NAMES = {0: ""}
#串口参数
PORT = 'COM3'
BAUDRATE = 115200
BYTESIZE = 8
STOPBITES = 1
#蓝牙参数
TARGETADDRESS = '98:DA:F0:00:77:FD'
TARGETNAME = 'BT18-T'
BLUETOOTHPORT = 1
SENDUUID = '0000ffe2-0000-1000-8000-00805f9b34fb'
RECEIVEUUID = '0000ffe1-0000-1000-8000-00805f9b34fb'
