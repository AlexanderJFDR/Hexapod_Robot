from interface import *
from models import *
from communication import *


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hexapod = Hexapod()
    ser = Serial()
    blt = Bluetooth()
    ui = mainWindow(hexapod,ser,blt)

    sys.exit(app.exec())