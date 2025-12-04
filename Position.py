import time


from SerialLock import SerialLock
from SerialPage import NeedelConnectionThread, SIM928ConnectionThread
import sys

from StopClass import StopClass
# 导入全局温度配置
from TemperatureConfig import is_low

# 定义你要添加的库文件路径
custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"

# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)

def getPosition(Z_flag=False,Only_XY=False):

    anc = NeedelConnectionThread.anc
    x_distance = 0
    y_distance = 0
    z_distance = 0

    if Z_flag is not True:
        # X轴坐标
        try:
            anc.write('[ch3:1]'.encode())
            time.sleep(0.2)
            anc.write('[v?]'.encode())
            anc.write('[read:pulse?]'.encode())
            ret = anc.readline()
            ret_str = ret.decode()
            start_index = ret_str.find('[+') + 2
            end_index = ret_str.find('v]')
            if start_index > 1 and end_index > start_index:
                voltage_str = ret_str[start_index:end_index].strip()
                if voltage_str:  # 确保不是空字符串
                    distance = float(voltage_str)  # 浮点型
                    x_distance = (1 - distance / 2.5) * 10.92 - 5
            time.sleep(0.1)
        except (ValueError, IndexError) as e:
            print(f"获取X轴位置失败: {e}, 返回数据: {ret_str if 'ret_str' in locals() else 'N/A'}")
            x_distance = 0

        try:
            anc.write('[ch2:1]'.encode())
            time.sleep(0.2)
            anc.write('[v?]'.encode())
            anc.write('[read:pulse?]'.encode())
            ret = anc.readline()
            ret_str = ret.decode()
            start_index = ret_str.find('[+') + 2
            end_index = ret_str.find('v]')
            if start_index > 1 and end_index > start_index:
                voltage_str = ret_str[start_index:end_index].strip()
                if voltage_str:  # 确保不是空字符串
                    distance = float(voltage_str)  # 浮点型
                    y_distance = (1 - distance / 2.5) * 10.92 - 5
            time.sleep(0.1)
        except (ValueError, IndexError) as e:
            print(f"获取Y轴位置失败: {e}, 返回数据: {ret_str if 'ret_str' in locals() else 'N/A'}")
            y_distance = 0

    if Only_XY is not True:
        try:
            anc.write('[ch1:1]'.encode())
            time.sleep(0.2)
            anc.write('[v?]'.encode())
            anc.write('[read:pulse?]'.encode())
            ret = anc.readline()
            ret_str = ret.decode()
            start_index = ret_str.find('[+') + 2
            end_index = ret_str.find('v]')
            if start_index > 1 and end_index > start_index:
                voltage_str = ret_str[start_index:end_index].strip()
                if voltage_str:  # 确保不是空字符串
                    distance = float(voltage_str)  # 浮点型
                    z_distance = (1 - distance / 2.5) * 10.92 - 5
            time.sleep(0.1)
        except (ValueError, IndexError) as e:
            print(f"获取Z轴位置失败: {e}, 返回数据: {ret_str if 'ret_str' in locals() else 'N/A'}")
            z_distance = 0

    return round(x_distance,4),round(y_distance,4),round(z_distance,6)

def move_to_Z(z,indicatorLight,Voltage_flag=False):
    with SerialLock.serial_lock:
        _, _, z_current = getPosition(Z_flag=True)
    import MainPage
    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(True))
    # 定义不同阶段的阈值和参数
    FAR_THRESHOLD = 0.02  # 20微米以上为远距离移动
    NEAR_THRESHOLD = 0.005  # 5微米以下为微调阶段
    step_per_unit = 0.06  # 1单位对应0.06实际距离

    # 根据全局配置选择参数
    Z_k = 600 if is_low() else 100  # 低温600，常温100（基于其他文件推断）

    while abs(z_current - z) > 0.005:  # 最终精度要求5纳米
        if Voltage_flag:
            keithley = SIM928ConnectionThread.anc
            current = keithley.current
            print(current)
            if current >= 9e-10:
                break
        if StopClass.stop_num == 1:
            break

        # 计算剩余距离
        remaining_distance = abs(z_current - z)

        # 根据距离动态调整参数
        if remaining_distance > FAR_THRESHOLD:
            # 远距离快速移动 - 使用最大速度但限制单次移动距离
            speed_factor = 3.0
            max_step = 0.01  # 最大单次移动10微米
            micro_adjust = False
        elif remaining_distance > NEAR_THRESHOLD:
            # 中等距离正常移动 - 使用中等速度和小步长
            speed_factor = 1.0
            max_step = 0.002  # 最大单次移动2微米
            micro_adjust = False
        else:
            # 微调阶段 - 使用小步长和高精度
            speed_factor = 0.3  # 更慢的速度
            max_step = 0.0005  # 最大单次移动0.5微米
            micro_adjust = True

        # 计算实际移动距离（不超过max_step）
        move_distance = min(remaining_distance, max_step)

        with SerialLock.serial_lock:
            z_diff = z - z_current
            adjusted_distance = move_distance / step_per_unit * Z_k * speed_factor

            if z_diff > 0:
                move('-Z', adjusted_distance, False,micro_adjust)
            elif z_diff < 0:
                move('Z', adjusted_distance, False,micro_adjust)

            _, _, z_current = getPosition(Z_flag=True)

    StopClass.stop_num = 0
    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
    return z_current


def move(axis, distance, flag,Z_adjust=False):
    distance = round(distance)
    ser4 = NeedelConnectionThread.anc
    move_time = distance/8000 #初始为10000

    # 根据全局配置选择参数
    if is_low():
        frequencyXY = '1200'
        frequencyZ = '1000'
        voltage = '200'
    else:
        frequencyXY = '300'
        frequencyZ = '500'
        voltage = '150'

    # X/Y轴保持原始代码（固定频率1000Hz，固定时间0.3秒）
    if axis == '-X':
        ser4.write('[ch3:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())
        ser4.write(('[freq:+'+frequencyXY+'Hz]').encode())
        ser4.write(('[+:0000' + str(distance) + ']').encode())

    elif axis == 'X':
        ser4.write('[ch3:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())
        ser4.write(('[freq:+'+frequencyXY+'Hz]').encode())
        ser4.write(('[-:0000' + str(distance) + ']').encode())
    elif axis == '-Y':
        ser4.write('[ch2:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())
        ser4.write(('[freq:+'+frequencyXY+'Hz]').encode())
        ser4.write(('[+:0000' + str(distance) + ']').encode())
    elif axis == 'Y':
        ser4.write('[ch2:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())
        ser4.write(('[freq:+'+frequencyXY+'Hz]').encode())
        ser4.write(('[-:0000' + str(distance) + ']').encode())

    # Z轴保持微调和非微调功能
    elif axis == 'Z':
        ser4.write('[ch1:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())

        # 根据flag决定频率（微调500Hz，非微调800Hz）
        freq = '+0700Hz' if Z_adjust else '+1000Hz'
        ser4.write(f'[freq:{freq}]'.encode())
        ser4.write(('[+:0000' + str(distance) + '] ').encode())

        # 动态计算移动时间
        base_time = 0.3
        scale_factor = 0.001
        move_time = base_time + distance * scale_factor
        move_time = max(0.2, min(move_time, 3.0))

    elif axis == '-Z':
        ser4.write('[ch1:1]'.encode())
        ser4.write('[cap:013nF]'.encode())
        ser4.write(('[volt:+'+voltage+'V]').encode())

        # 根据flag决定频率（微调500Hz，非微调800Hz）
        freq = '+0500Hz' if Z_adjust else '+0800Hz'
        ser4.write(f'[freq:{freq}]'.encode())
        ser4.write(('[-:0000' + str(distance) + '] ').encode())

        # 动态计算移动时间
        base_time = 0.3
        scale_factor = 0.001
        move_time = base_time + distance * scale_factor
        move_time = max(0.2, min(move_time, 3.0))

    # 睡眠时间处理
    if flag:
        time.sleep((distance + 1) / 1500)
    else:
        time.sleep(move_time)

def move_to_target(x, y,indicatorLight):
    # 根据全局配置选择参数
    if is_low():
        XY_k = 1000
        XY_k_2 = 10000
    else:
        XY_k = 300
        XY_k_2 = 3000

    step_per_unit = 0.06  # 假设每 0.06 单位对应 100 步
    import MainPage
    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(True))
    with SerialLock.serial_lock:
        x_current, y_current,_ = getPosition(Only_XY=True)
        x_diff = round((x - x_current), 3)
        y_diff = round((y - y_current), 3)

        flag = True
        if x_diff > 0:
            move('X', abs(x_diff) / 0.03 * XY_k, flag)
        elif x_diff < 0:
            move('-X', abs(x_diff) / 0.03 * XY_k, flag)

        if y_diff > 0:
            move('Y', abs(y_diff) / 0.03 * XY_k, flag)
        elif y_diff < 0:
            move('-Y', abs(y_diff) / 0.03 * XY_k, flag)
        x_current, y_current,_ = getPosition(Only_XY=True)
        time.sleep(0.2)

    while  abs(y_current - y) > 0.015 :
        if StopClass.stop_num == 1:
            StopClass.stop_num = 0
            anc = NeedelConnectionThread.anc
            anc.write('[ch1:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch2:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch3:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch1:0]'.encode())
            anc.write('[ch2:0]'.encode())
            anc.write('[ch3:0]'.encode())
            time.sleep(0.2)
            break
        else:
            flag = False
            with SerialLock.serial_lock:
                y_diff = round((y - y_current), 3)
                if y_diff > 0:
                    move('Y', abs(y_diff) / step_per_unit * XY_k_2, flag)
                elif y_diff < 0:
                    move('-Y', abs(y_diff) / step_per_unit * XY_k_2, flag)
                _, y_current,_ = getPosition(Only_XY=True)
                time.sleep(0.2)
    while abs(x_current - x) > 0.015:
        if StopClass.stop_num == 1:
            StopClass.stop_num = 0
            anc = NeedelConnectionThread.anc
            anc.write('[ch1:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch2:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch3:1]'.encode())
            anc.write('[cap:000nF]'.encode())
            anc.write('[volt:+000V] '.encode())
            anc.write('[freq:+00000Hz]'.encode())
            time.sleep(0.2)
            anc.write('[ch1:0]'.encode())
            anc.write('[ch2:0]'.encode())
            anc.write('[ch3:0]'.encode())
            time.sleep(0.2)
            break
        else:
            flag = False
            with SerialLock.serial_lock:
                x_diff = round((x - x_current), 3)
                if x_diff > 0:
                    move('X', abs(x_diff) / step_per_unit * XY_k_2, flag)
                elif x_diff < 0:
                    move('-X', abs(x_diff) / step_per_unit * XY_k_2, flag)
                x_current, _, _ = getPosition(Only_XY=True)
                time.sleep(0.2)
    indicatorLight.setStyleSheet(MainPage.MainPage1.get_stylesheet(False))
    return x_current, y_current
