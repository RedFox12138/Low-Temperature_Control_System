import importlib
import sys
import time

import MainPage
from ANC300 import Positioner
import math

from Position import getPosition
from SerialLock import SerialLock
from locationClass import locationClass
from SerialPage import NeedelConnectionThread, SIM928ConnectionThread
from StopClass import StopClass
# 导入全局温度配置
from TemperatureConfig import is_low

ax = {'x':1,'y':2,'z':3,'x2':4,'y2':5,'z2':6}

def _safe_serial_write(anc, data, max_retries=3):
    """安全的串口写入，带重试机制"""
    for attempt in range(max_retries):
        try:
            anc.write(data)
            time.sleep(0.01)  # 写入后短暂延迟，避免缓冲区溢出
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"串口写入失败（重试{max_retries}次）: {e}")
                return False
            time.sleep(0.05)  # 重试前等待
    return False

def ReturnNeedleMove(direction,distance,indicatorLight,isclick=False,flag=False,equipment=0):
    # 根据全局配置选择参数
    if is_low():
        frequencyXY = '2000'
        frequencyZ = '500'
        voltage = '200'
    else:
        frequencyXY = '300'
        frequencyZ = '100'
        voltage = '100'

    directionArray = [[2,3,1],[6,5,4]]
    with SerialLock.serial_lock:
        try:
            anc = NeedelConnectionThread.anc
            if anc is None or not anc.is_open:
                print("串口未连接或已关闭")
                return False
            
            indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(True))
            
            # 预先构建所有命令
            commands = []
            if direction == 0:
                commands = [
                    f'[ch{directionArray[equipment][0]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+0{frequencyXY}Hz]'.encode(),
                    f'[-:0000{distance}] '.encode()
                ]
            elif direction == 1:
                commands = [
                    f'[ch{directionArray[equipment][0]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+0{frequencyXY}Hz]'.encode(),
                    f'[+:0000{distance}] '.encode()
                ]
            elif direction == 2:
                move_cmd = f'[+:0000{distance}] '.encode() if equipment == 1 else f'[-:0000{distance}] '.encode()
                commands = [
                    f'[ch{directionArray[equipment][1]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+0{frequencyXY}Hz]'.encode(),
                    move_cmd
                ]
            elif direction == 3:
                move_cmd = f'[-:0000{distance}] '.encode() if equipment == 1 else f'[+:0000{distance}] '.encode()
                commands = [
                    f'[ch{directionArray[equipment][1]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+0{frequencyXY}Hz]'.encode(),
                    move_cmd
                ]
            elif direction == 4:
                commands = [
                    f'[ch{directionArray[equipment][2]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+00{frequencyZ}Hz]'.encode(),
                    f'[-:0000{distance}] '.encode()
                ]
            elif direction == 5:
                commands = [
                    f'[ch{directionArray[equipment][2]}:1]'.encode(),
                    b'[cap:013nF]',
                    f'[volt:+{voltage}V]'.encode(),
                    f'[freq:+00{frequencyZ}Hz]'.encode(),
                    f'[+:0000{distance}] '.encode()
                ]
            
            # 批量写入所有命令
            all_success = True
            for cmd in commands:
                if not _safe_serial_write(anc, cmd):
                    all_success = False
                    break
            
            if not all_success:
                print("串口命令写入失败")
                indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
                return False
            
            # 等待命令执行完成
            if flag:
                time.sleep((distance + 1) / 300)
            else:
                time.sleep(0.8)

            if not isclick:
                indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
            
            return True
            
        except Exception as e:
            print(f"ReturnNeedleMove 异常: {e}")
            indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
            return False


def WhileMove(direction,indicatorLight,equipment=0,distance=1000):
    # 根据全局配置选择参数
    if is_low():
        frequencyXY = '2000'
        frequencyZ = '1000'
        voltage = '200'
    else:
        frequencyXY = '300'
        frequencyZ = '500'
        voltage = '100'

    directionArray = [[2,3,1],[6,5,4]]
    # 初始化串口命令 - 使用安全写入
    with SerialLock.serial_lock:
        try:
            anc = NeedelConnectionThread.anc
            if anc is None or not anc.is_open:
                print("串口未连接或已关闭")
                return False
            
            indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(True))
            
            # 批量停止所有通道
            stop_cmds = [
                b'[ch1:0]', b'[ch2:0]', b'[ch3:0]',
                b'[ch4:0]', b'[ch5:0]', b'[ch6:0]'
            ]
            for cmd in stop_cmds:
                if not _safe_serial_write(anc, cmd):
                    print("停止通道命令失败")
                    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
                    return False
            time.sleep(0.1)
        except Exception as e:
            print(f"WhileMove 初始化失败: {e}")
            indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
            return False
    
    # distance = min(1000,distance)
    if direction == 0 or direction == 1:
        with SerialLock.serial_lock:
            setup_cmds = [
                f'[ch{directionArray[equipment][0]}:1]'.encode(),
                b'[cap:013nF]',
                f'[volt:+{voltage}V]'.encode(),
                f'[freq:+0{frequencyXY}Hz]'.encode()
            ]
            for cmd in setup_cmds:
                if not _safe_serial_write(anc, cmd):
                    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
                    return False
            time.sleep(0.1)
        
        num_str = '[-:0000' if direction ==0 else '[+:0000'
        while StopClass.stop_num == 0:
            # 🔒 每次写入时加锁，避免长时间持锁
            with SerialLock.serial_lock:
                _safe_serial_write(anc, (num_str + str(distance) + '] ').encode())
            time.sleep(0.1)  # 在锁外sleep
    
    elif direction == 2 or direction == 3:
        with SerialLock.serial_lock:
            setup_cmds = [
                f'[ch{directionArray[equipment][1]}:1]'.encode(),
                b'[cap:013nF]',
                f'[volt:+{voltage}V]'.encode(),
                f'[freq:+0{frequencyXY}Hz]'.encode()
            ]
            for cmd in setup_cmds:
                if not _safe_serial_write(anc, cmd):
                    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
                    return False
            time.sleep(0.1)
        
        num_str1 = '[+:0000' if direction == 2 else '[-:0000'
        num_str2 = '[-:0000' if direction == 2 else '[+:0000'
        while StopClass.stop_num == 0:
            # 🔒 每次写入时加锁，避免长时间持锁
            with SerialLock.serial_lock:
                if equipment==1:
                    _safe_serial_write(anc, (num_str1 + str(distance) + '] ').encode())
                else :
                    _safe_serial_write(anc, (num_str2 + str(distance) + '] ').encode())
            time.sleep(0.1)  # 在锁外sleep
    
    #Z轴, 4按压,5抬升
    elif direction == 4 or direction == 5:
        with SerialLock.serial_lock:
            setup_cmds = [
                f'[ch{directionArray[equipment][2]}:1]'.encode(),
                b'[cap:013nF]',
                f'[volt:+{voltage}V]'.encode(),
                f'[freq:+0{frequencyZ}Hz]'.encode()
            ]
            for cmd in setup_cmds:
                if not _safe_serial_write(anc, cmd):
                    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
                    return False
            time.sleep(0.2)
        
        num_str = '[+:0000' if direction == 4 else '[-:0000'
        while StopClass.stop_num == 0:
            # 🔒 每次写入时加锁，避免长时间持锁
            with SerialLock.serial_lock:
                _safe_serial_write(anc, (num_str + str(distance) + '] ').encode())
            time.sleep(0.2)  # 在锁外sleep
            keithley = SIM928ConnectionThread.anc
            current = keithley.current
            print(current)

    # 🔄 无论哪个分支，结束后都要重置 stop_num
    StopClass.stop_num = 0
    locationClass.locationX, locationClass.locationY, locationClass.locationZ = getPosition()
    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
    return True

def voltage_and_frequency(xv,yv,xf,yf):
    anc = NeedelConnectionThread.anc
    anc.setv(ax['x'], xv)
    anc.setv(ax['y'], yv)
    anc.setf(ax['x'], xf)
    anc.setf(ax['y'], yf)
