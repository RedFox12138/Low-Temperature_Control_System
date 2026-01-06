import time
from Scan.Multifields_Scanning_Stage import Positioner_scanning

def ScanY(x,is_low=False):
    if is_low:
        if x<= -150:
            x=-150
        if x>= 150:
            x=150
    else:
        if x<= 0:
            x = 0
        if x>=75:
            x=75

    # 使用 COM 端口连接，波特率 115200
    MFS = Positioner_scanning('COM3')  # 根据实际设备端口修改 COM 号
    MFS.nch(12)
    MFS.write('[start]')
    MFS.set_target(1, x)
    time.sleep(0.3)
    MFS.write('[stop]')
    # 关闭串口连接
    MFS.close()

def ScanX(y,is_low=False):
    if is_low:
        if y <= -150:
            y = -150
        if y >= 150:
            y = 150
    else:
        if y <= 0:
            y = 0
        if y >= 75:
            y = 75
    # 使用 COM 端口连接，波特率 115200
    MFS = Positioner_scanning('COM3')  # 根据实际设备端口修改 COM 号
    MFS.nch(12)
    MFS.write('[start]')
    MFS.set_target(2, y)
    time.sleep(0.3)
    MFS.write('[stop]')
    # 关闭串口连接
    MFS.close()

