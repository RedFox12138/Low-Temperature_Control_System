import time
import sys
from PyQt5.QtWidgets import QMainWindow
import serial.tools.list_ports
from PyQt5.QtCore import *
from pymeasure.instruments.keithley import Keithley2450
from SRS_SIM970 import SRSSIM970
from ZauxdllTest import GBIOConnect
from demo import Ui_MainWindow
from system_monitor import get_monitor, monitor_method

# 定义你要添加的库文件路径
custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"

# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)


class SerialPage(QMainWindow, Ui_MainWindow):
    def __init__(self, comboBox_micro, status_led_micro, connect_button_micro, disconnect_button_micro,
                 comboBox_needle, status_led_needle, connect_button_needle, disconnect_button_needle,
                 lineEdit_Keithley, status_led_SIM928, connect_button_SIM928, disconnect_button_SIM928,
                 comboBox1_SIM970, comboBox2_SIM970, status_led_SIM970, connect_button_SIM970, disconnect_button_SIM970,
                 GBIO_connect_button, comboBox_relay, status_led_relay, Button_relayConnect,
                 Button_relayDisConnect, Serial_connect_refresh):
        super().__init__()
        self.lineEdit_Keithley = lineEdit_Keithley

        # 存储所有设备连接状态和UI组件
        self.devices = {
            'micro': {
                'port_combo': comboBox_micro,
                'status_led': status_led_micro,
                'connect_button': connect_button_micro,
                'disconnect_button': disconnect_button_micro,
                'connection_thread': None,
                'connected': False
            },
            'needle': {
                'port_combo': comboBox_needle,
                'status_led': status_led_needle,
                'connect_button': connect_button_needle,
                'disconnect_button': disconnect_button_needle,
                'connection_thread': None,
                'connected': False
            },
            'relay': {
                'port_combo': comboBox_relay,
                'status_led': status_led_relay,
                'connect_button': Button_relayConnect,
                'disconnect_button': Button_relayDisConnect,
                'connection_thread': None,
                'connected': False
            },
            'SIM928': {
                'address_input': self.lineEdit_Keithley,  # 修改为直接使用地址输入框
                'status_led': status_led_SIM928,
                'connect_button': connect_button_SIM928,
                'disconnect_button': disconnect_button_SIM928,
                'connection_thread': None,
                'connected': False
            },
            'SIM970': {
                'gbio_combo': comboBox1_SIM970,
                'port_combo': comboBox2_SIM970,
                'status_led': status_led_SIM970,
                'connect_button': connect_button_SIM970,
                'disconnect_button': disconnect_button_SIM970,
                'connection_thread': None,
                'connected': False
            }
        }

        # 初始化所有设备UI
        self.init_device_ui()

        # GBIO连接按钮
        self.GBIO_connect_button = GBIO_connect_button
        self.GBIO_connect_button.clicked.connect(self.GBIO_clicked)

        # 串口刷新按钮
        self.Serial_connect_refresh = Serial_connect_refresh
        self.Serial_connect_refresh.clicked.connect(self.Serial_clicked)

        # 初始化连接超时计时器
        self.timer = QTimer(self)
        self.timer.setInterval(2000)  # 设置超时时间为2秒
        self.timer.timeout.connect(self.connection_timeout)

    def init_device_ui(self):
        """初始化所有设备的UI状态"""
        # 初始化串口设备
        for device in ['micro', 'needle', 'relay']:
            self.update_serial_ports(self.devices[device]['port_combo'])
            self.devices[device]['status_led'].setStyleSheet("color: red; font-size: 20px;")
            self.devices[device]['disconnect_button'].setEnabled(False)
            self.devices[device]['connect_button'].clicked.connect(
                lambda _, d=device: self.connect_to_serial(d))
            self.devices[device]['disconnect_button'].clicked.connect(
                lambda _, d=device: self.disconnect_from_serial(d))

        # 初始化GPIB设备
        for device in ['SIM928', 'SIM970']:
            if device == 'SIM970':
                self.update_GBIO_ports(self.devices[device]['gbio_combo'])
                for num in range(1, 11):
                    self.devices[device]['port_combo'].addItem(str(num))
            self.devices[device]['status_led'].setStyleSheet("color: red; font-size: 20px;")
            self.devices[device]['disconnect_button'].setEnabled(False)
            self.devices[device]['connect_button'].clicked.connect(
                lambda _, d=device: self.connect_to_serial(d))
            self.devices[device]['disconnect_button'].clicked.connect(
                lambda _, d=device: self.disconnect_from_serial(d))

    def GBIO_clicked(self):
        """处理GBIO连接按钮点击事件"""
        GBIOConnect()  # 先执行
        if 'SIM970' in self.devices:
            self.update_GBIO_ports(self.devices['SIM970']['gbio_combo'])  # 最后执行

    def Serial_clicked(self):
        """处理串口刷新按钮点击事件"""
        for device in ['micro', 'needle', 'relay']:
            self.update_serial_ports(self.devices[device]['port_combo'])

    def update_serial_ports(self, port_combo):
        """获取系统中所有可用的串口，并更新到下拉框中"""
        ports = serial.tools.list_ports.comports()
        port_combo.clear()  # 清空现有串口列表
        for port in ports:
            port_combo.addItem(port.device)  # 添加串口设备名称

    def update_GBIO_ports(self, GBIO_combo):
        """获取系统中所有可用的GBIO端口，并更新到下拉框中"""
        GBIOs = GBIOConnect.connected_gpib_devices
        GBIOs.append("default")
        GBIO_combo.clear()
        for GBIO in GBIOs:
            GBIO_combo.addItem(GBIO)  # 添加GBIO设备名称

    def connect_to_serial(self, device_type):
        """连接到选中的设备"""
        device = self.devices[device_type]

        # 检查端口是否有效
        if device_type in ['micro', 'needle', 'relay']:
            selected_port = device['port_combo'].currentText()
            if not selected_port:
                device['status_led'].setText('连接状态: 无串口可用')
                device['status_led'].setStyleSheet("color: red; font-size: 20px;")
                return
            port_number = int(selected_port[3:])  # 假设串口为 COMx 格式，取 x
        elif device_type == 'SIM970':
            selected_gbio = device['gbio_combo'].currentText()
            selected_port = device['port_combo'].currentText()
            if not selected_gbio or not selected_port:
                device['status_led'].setText('连接状态: 无端口可用')
                device['status_led'].setStyleSheet("color: red; font-size: 20px;")
                return
            port_number = int(selected_port)
            gbio_number = selected_gbio
        elif device_type == 'SIM928':
            address = device['address_input'].text().strip()  # 直接获取输入的地址
            if not address:
                device['status_led'].setText('连接状态: 请输入设备地址')
                device['status_led'].setStyleSheet("color: red; font-size: 20px;")
                return

        # 启动超时计时器
        self.timer.start()

        # 禁用按钮
        device['connect_button'].setEnabled(False)
        device['disconnect_button'].setEnabled(False)

        # 根据设备类型创建对应的连接线程
        if device_type == 'micro':
            device['connection_thread'] = SerialConnectionThread(port_number)
        elif device_type == 'needle':
            device['connection_thread'] = NeedelConnectionThread(port_number)
        elif device_type == 'relay':
            device['connection_thread'] = RelayConnectionThread(port_number)
        elif device_type == 'SIM928':
            device['connection_thread'] = SIM928ConnectionThread(address, device['address_input'])
        elif device_type == 'SIM970':
            device['connection_thread'] = SIM970ConnectionThread(port_number, gbio_number)

        # 连接信号和槽
        device['connection_thread'].connected.connect(
            lambda success, message, dt=device_type: self.handle_connection_result(dt, success, message))

        # 启动线程
        device['connection_thread'].start()

    def connection_timeout(self):
        """超时处理：2秒内没有连接成功，判定为连接失败"""
        for device_type, device in self.devices.items():
            if device['connection_thread'] and device['connection_thread'].isRunning():
                device['status_led'].setText('连接状态: 连接超时，请检查端口')
                device['status_led'].setStyleSheet("color: red; font-size: 20px;")
                device['connect_button'].setEnabled(True)
                device['disconnect_button'].setEnabled(False)
                device['connected'] = False
        self.timer.stop()

    def handle_connection_result(self, device_type, success, message):
        """处理连接成功或失败的信号"""
        device = self.devices[device_type]

        if success:
            device['status_led'].setText(f'连接状态: {message}')
            device['status_led'].setStyleSheet("color: green; font-size: 20px;")
            device['connect_button'].setEnabled(False)
            device['disconnect_button'].setEnabled(True)
            device['connected'] = True
        else:
            device['status_led'].setText(f'连接状态: {message}')
            device['status_led'].setStyleSheet("color: red; font-size: 20px;")
            device['connect_button'].setEnabled(True)
            device['disconnect_button'].setEnabled(False)
            device['connected'] = False

        self.timer.stop()

    def disconnect_from_serial(self, device_type):
        """断开设备连接"""
        device = self.devices[device_type]

        try:
            if device_type == 'micro' and SerialConnectionThread.zaux:
                SerialConnectionThread.zaux.disconnect()
            elif device_type == 'needle':
                NeedelConnectionThread.anc = None
            elif device_type == 'relay':
                RelayConnectionThread.anc = None
            elif device_type == 'SIM928' and SIM928ConnectionThread.anc:
                SIM928ConnectionThread.anc.shutdown()
                SIM928ConnectionThread.anc = None
            elif device_type == 'SIM970' and SIM970ConnectionThread.anc:
                SIM970ConnectionThread.anc.quit_vol()
                SIM970ConnectionThread.anc = None

            device['status_led'].setText('连接状态: 已断开')
            device['status_led'].setStyleSheet("color: red; font-size: 20px;")
            device['connect_button'].setEnabled(True)
            device['disconnect_button'].setEnabled(False)
            device['connected'] = False
        except Exception as e:
            device['status_led'].setText('连接状态: 断开失败')
            device['status_led'].setStyleSheet("color: red; font-size: 20px;")
            print(f"{device_type} 断开失败:", e)


# 以下是各种设备的连接线程类
class SerialConnectionThread(QThread):
    connected = pyqtSignal(bool, str)
    zaux = None
    port_com = 1

    def __init__(self, port_com):
        super().__init__()
        SerialConnectionThread.port_com = port_com
        self.setObjectName(f"SerialConnectionThread-COM{port_com}")

    @monitor_method
    def run(self):
        try:
            self.connected.emit(True, f"连接成功，端口 {SerialConnectionThread.port_com}")
        except Exception as e:
            self.connected.emit(False, f"连接失败: {str(e)}")


class NeedelConnectionThread(QThread):
    connected = pyqtSignal(bool, str)
    anc = None
    port_number = 1

    def __init__(self, port_number):
        super().__init__()
        NeedelConnectionThread.port_number = port_number
        self.setObjectName(f"NeedelConnectionThread-COM{port_number}")

    @monitor_method
    def run(self):
        try:
            bps = 115200
            port = "COM" + str(NeedelConnectionThread.port_number)
            NeedelConnectionThread.anc = serial.Serial(port, bps, timeout=0.1)
            self.connected.emit(True, f"连接成功，端口 {NeedelConnectionThread.port_number}")
        except Exception as e:
            self.connected.emit(False, f"连接失败: {str(e)}")


class RelayConnectionThread(QThread):
    connected = pyqtSignal(bool, str)
    anc = None

    def __init__(self, port_number):
        super().__init__()
        self.port_number = port_number
        self.setObjectName(f"RelayConnectionThread-COM{port_number}")

    @monitor_method
    def run(self):
        try:
            serialPort = self.port_number
            baudRate = 9600
            RelayConnectionThread.anc = serial.Serial("COM" + str(serialPort), baudRate, timeout=0.5)
            print("参数设置：串口={0} ，波特率={1}".format(serialPort, baudRate))
            self.connected.emit(True, f"连接成功，端口 {self.port_number}")
        except Exception as e:
            self.connected.emit(False, f"连接失败: {str(e)}")


class SIM928ConnectionThread(QThread):
    connected = pyqtSignal(bool, str)
    anc = None

    def __init__(self, address, address_input):
        super().__init__()
        self.address = address
        self.address_input = address_input
        self.setObjectName(f"SIM928ConnectionThread-{address}")

    @monitor_method
    def run(self):
        try:
            SIM928ConnectionThread.anc = Keithley2450(self.address)
            keithley = SIM928ConnectionThread.anc
            keithley.reset()
            time.sleep(0.1)
            self.connected.emit(True, f"连接成功，地址 {self.address}")
        except Exception as e:
            # if SIM928ConnectionThread.anc:
            #     SIM928ConnectionThread.anc.shutdown()
            self.connected.emit(False, f"连接失败: {str(e)}")


class SIM970ConnectionThread(QThread):
    connected = pyqtSignal(bool, str)
    anc = None

    def __init__(self, port_number, GBIO_number):
        super().__init__()
        self.port_number = port_number
        self.GBIO_number = GBIO_number
        self.setObjectName(f"SIM970ConnectionThread-{GBIO_number}-{port_number}")

    @monitor_method
    def run(self):
        try:
            SIM970ConnectionThread.anc = SRSSIM970(self.port_number, self.GBIO_number)
            self.connected.emit(True, f"连接成功，端口 {self.GBIO_number}")
        except Exception as e:
            self.connected.emit(False, f"连接失败: {str(e)}")
