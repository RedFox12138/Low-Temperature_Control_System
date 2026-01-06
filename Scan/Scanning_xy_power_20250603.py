# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 15:11:24 2025

@author: LIUZHEN
"""

import sys
import os



import numpy as np
import scipy.io as sio
from scipy.optimize import fmin
import matplotlib.pyplot as plt
import time
from time import sleep
import datetime
import re

from Multifields_Scanning_Stage import Positioner_scanning

# 使用 COM 端口连接，波特率 115200
MFS = Positioner_scanning('COM3')  # 根据实际设备端口修改 COM 号

waveLength = 1550
powerList= []
vol_x= []
vol_y= []
xposition = []
yposition = []
powerList_y = []
powerList_x = []
averagey =[]
averagex =[]
count_list_ch1=[]
count_list_ch2=[]
iii=0


# MFS.nch(12)
# MFS.write('[start]')
# time.sleep(0.1)

# vlist_x = np.arange(0,70,5)
# # print(vlist_x)
# for xx in vlist_x:
#     MFS.set_target(1,xx)
#     time.sleep(0.1)

# MFS.set_target(1,18)


# vlist_x = np.arange(0,60,5)
# # print(vlist_x)
# for xx in vlist_x:
#     MFS.set_target(1,xx)
#     time.sleep(0.1)


##---------------------------运行x轴---------------------------------##

MFS.nch(12)
MFS.write('[start]')
time.sleep(0.5)

# MFS.set_target(2,0)

vlist_x = np.arange(0,75,5)
# print(vlist_x)
for xx in vlist_x:
    MFS.set_target(1,xx)
    time.sleep(0.5)

# MFS.set_target(1,-150)

vlist_x = np.arange(75,0,-5)
print(vlist_x)
for xx in vlist_x:
    MFS.set_target(1,xx)
    time.sleep(0.05)
    print('x输出的电压为',xx)
    vol_x.append(xx)
    time.sleep(0.02)
    iii+=1
    print('当前已循环次数',iii)
    time.sleep(0.02)

            
##---------------------------运行y轴---------------------------------##
#     MFS.nch(12)
#     MFS.write('[start]')
#     time.sleep(0.02)
#
#     vlist_x = np.arange(0,-100,-10)
#     # print(vlist_x)
#     for xx in vlist_x:
#         MFS.set_target(2,xx)
#         time.sleep(0.1)
#
#     vlist_y = np.arange(-100,80,2)
#     for yy in vlist_y:
#         MFS.set_target(2,yy)
#         time.sleep(0.02)
#         print('y输出的电压为',yy)
#         vol_y.append(yy)
#         power = pm100.read_power()
#         print('y此时的反射功率是:',power*1e6,'uW')
#         powerList_y.append(power)
#         time.sleep(0.02)
#
#
#     vlist_yb = np.arange(80,0,-10)
#     for yyb in vlist_yb:
#          MFS.set_target(2,yyb)
#          time.sleep(0.02)
#
#     # MFS.set_target(2,0.0)
#
#
#
# vlist_xb = np.arange(60,0,-10)
# for xxb in vlist_yb:
#      MFS.set_target(1,xxb)
#      time.sleep(0.1)
#
# MFS.set_target(1,0.0)
#
#
# pathName = 'D:\\Data_LZ\\2025\\20251209_0717_1_3器件_1号纳米线测试\\'
# fileName = 'xy_scanning_y_-150,150,5_x_-150,150,5_z=1.093_x_1.638_y_3.075_powerin_fs_laser_1.536K'
# timeStr = datetime.datetime.now().strftime('_%Y-%m-%d-%H-%M-%S')
# matFile = pathName + fileName + timeStr + '.mat'
# sio.savemat(matFile, {'yposition':yposition,'powerList_y':powerList_y,'powerList_x':powerList_x,'vol_x':vol_x,'vol_y':vol_y,'count_list_ch2':count_list_ch2,'count_list_ch1':count_list_ch1})

MFS.set_target(1,0.0)
time.sleep(1)
MFS.set_target(2,0.0)
MFS.nch(0)
MFS.write('[stop]')

# 关闭串口连接
MFS.close()
