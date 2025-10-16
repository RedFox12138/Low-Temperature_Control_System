from PyQt5.QtWidgets import QMainWindow

from demo import Ui_MainWindow


class StopClass(QMainWindow, Ui_MainWindow):
    stop_num = 0
    def __init__(self,Button_needle1Stop):
        super().__init__()
        Button_needle1Stop.clicked.connect(self.STOP_MOVE)

    def STOP_MOVE(self):
        StopClass.stop_num = 1