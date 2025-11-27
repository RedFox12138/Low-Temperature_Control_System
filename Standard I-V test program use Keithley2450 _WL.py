import os
import sys
custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"

# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)
import numpy as np
import time
import datetime
from matplotlib import pyplot as plt
from scipy.optimize import fmin
import scipy.io as sio

from pymeasure.instruments.keithley import Keithley2450


def main():
    keithley = Keithley2450("USB0::0x05E6::0x2450::04514728::0::INSTR") # keithley2450地址
    keithley.reset() #keithley2450初始化sss
    time.sleep(0.1)

    #=================================================================================================
    #初始需修改的参数

    deviceName =  "Default"
    if(sys.argv[2]is not None):
        deviceName = sys.argv[2]

    Vmax = 2.8  # Vmax的值
    s1 = 0.1   # 步长s1, 从0到0.5Vmax
    s2 = 0.02   # 步长s2, 从0.5Vmax到Vmax
    s3 = 0.1  # 步长s3, 从Vmax到0.2Vmax
    s4 = 0.01  # 步长s4, 从0.2Vmax到0


    R_bias = 98800      # 偏置电阻大小 
    # R_bias = 10070      # 偏置电阻大小
    # R_bias = 1007
#=================================================================================================

    I = [] # 电流
    II=[]  
    V = [] # 电压

#=================================================================================================

    V_set = []

# 从0增大到0.5*Vmax（步长为s1）
    V_set.extend(np.arange(0, 0.65*Vmax, s1))

# 从0.5*Vmax增大到Vmax（步长为s2）
    V_set.extend(np.arange(0.65*Vmax, Vmax, s2))

# 从Vmax减小到0.2*Vmax（步长为s3）
    V_set.extend(np.arange(Vmax, 0.19*Vmax, -s3))

# 从0.2*Vmax减小到0（步长为s4）
    V_set.extend(np.arange(0.19*Vmax, 0.09*Vmax, -s4))

    V_set.extend(np.arange(0.09*Vmax, 0, -s3))
# 从0减小到-0.5*Vmax（步长为s1）
    V_set.extend(np.arange(0, -0.65*Vmax, -s1))

# 从-0.5*Vmax减小到-Vmax（步长为s2）
    V_set.extend(np.arange(-0.65*Vmax, -Vmax, -s2))

# 从-Vmax增大到-0.2*Vmax（步长为s3）
    V_set.extend(np.arange(-Vmax, 0, s3))

    V_set.append(0)

    V_set = np.array(V_set)

    #==================================================================================================
    # 测量部分

    keithley.use_rear_terminals             #使用仪器前面端子
    keithley.wires
    keithley.apply_voltage()                # Sets up to source voltage
    keithley.compliance_current = 0.1       # Sets the compliance current
    keithley.auto_range_source()
    keithley.measure_current()              # Sets up to measure current

    keithley.enable_source()                #打开源表
    time.sleep(0.1)

    try:
        for i in range(len(V_set)):
            keithley.source_voltage = V_set[i]
            time.sleep(0.2)
            current = keithley.current
            I.append(current)
            V.append(V_set[i]-current*R_bias)
            print('此时的电流为=',current,'此时的电压为=',V_set[i],'此时的器件上电压为=',V_set[i]-current*R_bias)
            time.sleep(0.1)

        keithley.shutdown()
    except (KeyboardInterrupt,Exception) as e:
        print("已停止实时观测，关闭源表...")
        keithley.shutdown()


    time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    datapath = sys.argv[1]
    if not os.path.exists(datapath) :
        os.makedirs (datapath)
    fileName = deviceName +'_Vmax_' + str(Vmax) +'_R_bias_'+ str(R_bias) +'_s1_'+ str(s1)+'_s2_'+ str(s2)+'_s3_'+ str(s3)+'_s4_'+ str(s4)+'_'+ time_str+'.mat'
    matFile = datapath +fileName
    print("保存路径是", matFile)
    sio.savemat(matFile, {'V_source_set' : V_set,'V': V,'I': I})

if __name__ == "__main__":
    sys.exit(main())
# plt.plot(V, I, 'b.')
# plt.grid(True)
# plt.xlabel('Voltage / V')
# plt.ylabel('Current / A')
# plt.show()