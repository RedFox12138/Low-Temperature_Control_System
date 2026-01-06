# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 12:44:10 2024

@author: liu zhen
"""

import serial
import time

class Positioner_scanning(object):
    """Python class for Multifields Scanning Stages, written by Liu Zhen"""
    def __init__(self, port, bps=115200, timeout=0.1):
        """
        初始化扫描定位器
        :param port: 串口端口，如 'COM3'
        :param bps: 波特率，默认 115200
        :param timeout: 超时时间(秒)，默认 0.1
        """
        self.serial = serial.Serial(port, bps, timeout=timeout)
        time.sleep(0.1)  # 等待串口稳定
  
    def write(self, string):
        """发送命令到设备"""
        if isinstance(string, str):
            string = string.encode('utf-8')
        self.serial.write(string)
        time.sleep(0.05)  # 给设备处理时间

    def read_v(self):
        """查询电压"""
        return self.query('[v?]')
    
    def read_pul(self):
        """查询脉冲"""
        return self.query('[read:pulse?]')
    
    def query(self, command):
        """发送查询命令并读取响应"""
        if isinstance(command, str):
            command = command.encode('utf-8')
        self.serial.write(command)
        time.sleep(0.05)
        response = self.serial.readline()
        return response.decode('utf-8', errors='ignore').strip()
        
    def read(self):
        """读取设备响应"""
        response = self.serial.readline()
        return response.decode('utf-8', errors='ignore').strip()
      
    def print(self, string):
        """打印并发送命令"""
        print(string)
        self.write(string)

    def numb(self, CH):
        write_str = '[numb:%d:4096]' % (CH)
        self.write(write_str)

    def nch(self,CH):
        write_str = '[nch:%d]' % (CH)
        self.write(write_str)

    def set_target(self, CH,cap_v):
        write_str = '[target:ch%d:%6f]' % (CH,cap_v)
        # print(write_str)
        self.write(write_str)     
        
    def cap(self, CAP):
        write_str = '[cap:%dnF]' % (CAP)
        print(write_str)
        self.write(write_str) 
                
    def volt(self, VOLT):
        write_str = '[volt:+%3.0fV]' % (VOLT)
        print(write_str)
        self.write(write_str) 

    def pulse(self, PUL):
        write_str = '[+:%6.0f]' % (PUL)
        print(write_str)
        self.write(write_str) 

    def back(self, BA):
        write_str = '[-:%6.0f]' % (BA)
        print(write_str)
        self.write(write_str) 

    def reset(self):
        """停止设备"""
        self.write('[stop]')
    
    def close(self):
        """关闭串口连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def is_open(self):
        """检查串口是否打开"""
        return self.serial.is_open if self.serial else False
    
    def flush(self):
        """清空输入输出缓冲区"""
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

    #set status of DC-IN input
    def setdci(self, AID, switch): 
        write_str = 'setdci %d %s' % (AID, switch)
        #switch can select 'on' or 'off'
        #print(write_str)
        self.write(write_str)        
        
    def stepu(self, AID, C):
        write_str = 'stepu %d %d' % (AID, C)
        print(write_str)
        self.write(write_str) 

    def stepd(self, AID, C):
        write_str = 'stepd %d %d' % (AID, C)
        print(write_str)
        self.write(write_str)



        
        
        