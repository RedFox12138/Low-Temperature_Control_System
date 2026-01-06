import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import matplotlib
import numpy as np

from matplotlib import pyplot as plt, animation
from PyQt5.QtCore import QTimer, Qt

from DailyLogger import DailyLogger
from Position import move_to_Z, getPosition, move_to_target
from SerialLock import SerialLock
from demo import Ui_MainWindow
from SerialPage import SIM928ConnectionThread, RelayConnectionThread, NeedelConnectionThread
from StopClass import StopClass

# 移除对 tkinter 的依赖，避免与 PyQt 事件循环冲突
# import tkinter as tk
# from tkinter import messagebox

custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"
# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)
import threading
import time
from PyQt5.QtWidgets import QMainWindow

# 使用与 PyQt 兼容的后端，避免使用 TkAgg 引发的跨主线程错误
matplotlib.use('Qt5Agg')

# 设置中文字体
plt.rcParams['font.family'] = 'SimHei'
# 解决负号显示问题
plt.rcParams['axes.unicode_minus'] = False
# 全局变量，用于控制测试的启动和停止
test_event = threading.Event()
logger = DailyLogger()

class locationClass(QMainWindow, Ui_MainWindow):
    locationX = 0
    locationY = 0
    locationZ = 0
    def __init__(self,lineEdit_Xlocation,lineEdit_Ylocation,lineEdit_Zlocation,
                 lineEdit_Location1,lineEdit_Location2,lineEdit_Location3,
                 Button_Location1,Button_Location2,Button_Location3,
                 lineEdit_row,lineEdit_col,Button_CreateMap,mainpage1,
                 Button_ContinueTest,Button_StopTest,
                 lineEdit_Pushlocation, lineEdit_Pulllocation,
                 Button_PushLocation, Button_PullLocation,
                 Button_PushBack, Button_PullBack,
                 lineEdit_leftTopX, lineEdit_leftTopY, lineEdit_rightTopX, lineEdit_rightTopY, lineEdit_rightBottomX, lineEdit_rightBottomY,
                 Checkbox_DontTest,widget_map,tabWidget,label_light,
                 lineEdit_leftTopName, lineEdit_rightTopName, lineEdit_rightBottomName
    ):
        super().__init__()

        # 初始化指示灯
        self.indicator = label_light

        #widget_map 用于把地图嵌入到界面中
        self.mapWidget = widget_map
        self.tab_widget = tabWidget

        # 大规模测试的时候，不需要按压与电学性能测试
        Checkbox_DontTest.stateChanged.connect(self.checkbox_DontTest_changed)
        self.DontTest = False

        #下面是内部矩阵三个坐标分别位于外部矩阵的什么位置
        self.lineEdit_leftTopX=lineEdit_leftTopX
        self.lineEdit_leftTopY=lineEdit_leftTopY
        self.lineEdit_rightTopX=lineEdit_rightTopX
        self.lineEdit_rightTopY=lineEdit_rightTopY
        self.lineEdit_rightBottomX=lineEdit_rightBottomX
        self.lineEdit_rightBottomY=lineEdit_rightBottomY

        self.lineEdit_leftTopName=lineEdit_leftTopName
        self.lineEdit_rightTopName=lineEdit_rightTopName
        self.lineEdit_rightBottomName=lineEdit_rightBottomName

        # 创建一个持久的线程池，避免重复创建销毁带来的开销
        self.move_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='MoveExecutor')

        self.device_positions = []
        self.ax = None
        self.fig = None
        self.mainpage1 = mainpage1
        self.lineEdit_Xlocation = lineEdit_Xlocation
        self.lineEdit_Ylocation = lineEdit_Ylocation
        self.lineEdit_Zlocation = lineEdit_Zlocation
        self.lineEdit_row = lineEdit_row
        self.lineEdit_col = lineEdit_col

        self.lineEdit_Pushlocation = lineEdit_Pushlocation
        self.lineEdit_Pulllocation = lineEdit_Pulllocation


        self.location1 = None
        self.location2 = None
        self.location3 = None
        self.Zlocation1 = 0
        self.Zlocation2 = 0

        self.lineEdit_Location1 = lineEdit_Location1
        self.lineEdit_Location2 = lineEdit_Location2
        self.lineEdit_Location3 = lineEdit_Location3

        # self.lineEdit_Location1.setText("0")
        # self.lineEdit_Location2.setText("0")
        # self.lineEdit_Location3.setText("0")

        Button_Location1.clicked.connect(lambda: threading.Thread(target=self.ConfirmPosition, args=(1,)).start())
        Button_Location2.clicked.connect(lambda: threading.Thread(target=self.ConfirmPosition, args=(2,)).start())
        Button_Location3.clicked.connect(lambda: threading.Thread(target=self.ConfirmPosition, args=(3,)).start())

        Button_PushLocation.clicked.connect(lambda: threading.Thread(target=self.ZConfirmPosition, args=(1,)).start())
        Button_PullLocation.clicked.connect(lambda: threading.Thread(target=self.ZConfirmPosition, args=(2,)).start())

        # 重要：CreateMap 在主线程执行，避免 Matplotlib/Qt 后端跨线程崩溃
        Button_CreateMap.clicked.connect(self.start_map_creation)

        Button_ContinueTest.clicked.connect(lambda: threading.Thread(target=self.continue_test).start())
        Button_StopTest.clicked.connect(lambda: threading.Thread(target=self.stop_test).start())

        Button_PushBack.clicked.connect(lambda: threading.Thread(target=self.PushBack).start())
        Button_PullBack.clicked.connect(lambda: threading.Thread(target=self.PullBack).start())

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_location_display)
        self.log_timer.start(500)  # 每秒更新一次

    def checkbox_DontTest_changed(self,state):
        # 根据复选框的状态更新标志位
        if state == Qt.Checked:
            self.DontTest = True
        else:
            self.DontTest = False

    def PushBack(self,flag=True):
        move_to_Z(self.Zlocation1,self.indicator,flag)
        locationClass.locationX, locationClass.locationY, locationClass.locationZ = getPosition()

    def PullBack(self):
        move_to_Z(self.Zlocation2,self.indicator)
        locationClass.locationX, locationClass.locationY, locationClass.locationZ = getPosition()


    def update_location_display(self):
        self.lineEdit_Xlocation.setText(str(locationClass.locationX))
        self.lineEdit_Ylocation.setText(str(locationClass.locationY))
        self.lineEdit_Zlocation.setText(str(locationClass.locationZ))

    def ConfirmPosition(self,flag):
        with SerialLock.serial_lock:
            locationClass.locationX,locationClass.locationY,locationClass.locationZ = getPosition()
        if flag == 1:
            self.location1 = (locationClass.locationX,locationClass.locationY)
            self.lineEdit_Location1.setText(str(self.location1))
        if flag == 2:
            self.location2 = (locationClass.locationX, locationClass.locationY)
            self.lineEdit_Location2.setText(str(self.location2))
        if flag == 3:
            self.location3 = (locationClass.locationX, locationClass.locationY)
            self.lineEdit_Location3.setText(str(self.location3))

    def ZConfirmPosition(self,flag):
        with SerialLock.serial_lock:
            _, _, locationClass.locationZ = getPosition()
        if flag == 1:
            self.Zlocation1 = locationClass.locationZ - 0.01
            self.lineEdit_Pushlocation.setText(str(self.Zlocation1))
        if flag == 2:
            self.Zlocation2 = locationClass.locationZ + 0.01
            self.lineEdit_Pulllocation.setText(str(self.Zlocation2))


    def CreateMap(self):
        # 关闭之前打开的图形窗口（如果存在）
        if hasattr(self, 'fig') and self.fig is not None:
            plt.close(self.fig)
            self.fig = None  # 显式释放资源

        if (self.lineEdit_row.text() == '' or self.lineEdit_col.text() == '' or
                self.location1 is None or self.location2 is None or self.location3 is None or
                self.lineEdit_rightTopX.text() == '' or self.lineEdit_rightTopY.text() == '' or
                self.lineEdit_leftTopX.text() == '' or self.lineEdit_leftTopY.text() == '' or
                self.lineEdit_rightBottomX.text() == '' or self.lineEdit_rightBottomY.text() == ''):
            # 处理空值的情况
            logger.log("参数配置未完成，无法生成MAP")
            return
        else:
            row = int(self.lineEdit_row.text())
            col = int(self.lineEdit_col.text())
            x1 = int(self.lineEdit_leftTopX.text())
            y1 = int(self.lineEdit_leftTopY.text())
            x2 = int(self.lineEdit_rightTopX.text())
            y2 = int(self.lineEdit_rightTopY.text())
            x3 = int(self.lineEdit_rightBottomX.text())
            y3 = int(self.lineEdit_rightBottomY.text())

            self.device_positions = self.calculate_device_positions(
                self.location1, x1, y1,
                self.location2, x2, y2,
                self.location3, x3, y3,
                row, col
            )

            # 基于三个基准名称生成整图命名（左上、右上、右下）
            self.device_names = self.calculate_device_names(
                self.lineEdit_leftTopName.text().strip(),
                self.lineEdit_rightTopName.text().strip(),
                self.lineEdit_rightBottomName.text().strip(),
                row, col
            )

            # 创建新的图形和坐标轴
            self.fig, self.ax = plt.subplots()

            # 获取所有设备的坐标
            x_coords = [float(pos[0]) for pos in self.device_positions]
            y_coords = [float(pos[1]) for pos in self.device_positions]

            # 计算坐标范围（自适应）
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            # 添加一些边距（例如10%的额外空间）
            margin_x = (x_max - x_min) * 0.1
            margin_y = (y_max - y_min) * 0.1

            # 设置坐标轴范围（自适应）
            self.ax.set_xlim(x_min - margin_x, x_max + margin_x)
            self.ax.set_ylim(y_min - margin_y, y_max + margin_y)
            self.ax.set_aspect('equal')  # 保持比例一致
            self.ax.invert_xaxis()
            self.ax.invert_yaxis()  # 翻转Y轴，使Dev_0在左上角
            # 修改后（将标签移到坐标轴外）
            info_text = self.ax.text(
                -0.36, 1.05,  # x负方向偏移25%，y正方向偏移5%
                'Status: Ready\n(0.00, 0.00)',
                transform=self.ax.transAxes,  # 保持坐标轴坐标系
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                fontsize=9,
                clip_on=False  # 关键！关闭裁剪限制
            )

            # 绘制设备点
            device_scatter = self.ax.scatter(
                x_coords, y_coords,
                color='blue', label='设备'
            )

            # 在图上为每个点标注名称（若已生成）
            try:
                if getattr(self, 'device_names', None) and len(self.device_names) == len(self.device_positions):
                    for i, name in enumerate(self.device_names):
                        self.ax.text(x_coords[i], y_coords[i] + margin_y * 0.08, name, fontsize=9, ha='center', color='black')
            except Exception as e:
                logger.log(f"标注名称时出现问题: {e}")

            # 绘制探针点
            probe_point, = self.ax.plot([], [], 'ro', label='探针')

            # 使用动画API替代线程
            def animate(_):
                try:
                    # 更新探针位置
                    probe_point.set_data([locationClass.locationX], [locationClass.locationY])

                    # 更新信息文本
                    info_text.set_text('Time: %s\nX: %.4f\nY: %.4f' % (
                        datetime.now().strftime("%H:%M:%S"),
                        locationClass.locationX,
                        locationClass.locationY
                    ))

                    # 请求重绘（线程安全方式）
                    self.fig.canvas.draw_idle()
                except Exception as e:
                    print(f"更新异常: {e}")
                    return
                return [probe_point, info_text]

            # 创建动画对象
            self.ani = animation.FuncAnimation(
                self.fig,
                animate,
                interval=2000,  # 2秒间隔
                cache_frame_data=False
            )

            # 绑定鼠标点击事件
            self.fig.canvas.mpl_connect('button_press_event', self.on_click)

            plt.show()



    # 遍历设备位置，依次移动探针 从头开始测试所有的探针
    def move_to_all_targets(self, start_index=0):
        test_event.set()
        try:
            step_size = 1
            for i in range(start_index, len(self.device_positions),step_size):
                if not test_event.is_set() or StopClass.stop_num==1:
                    StopClass.stop_num=0
                    break

                # 确保坐标值是浮点数
                try:
                    target_x, target_y = self.device_positions[i]
                    target_x = float(target_x)
                    target_y = float(target_y)
                except (ValueError, TypeError) as e:
                    logger.log(f'坐标转换失败: 索引={i}, 原始值={self.device_positions[i]}, 错误={e}')
                    continue
                
                PadName = self.device_names[i] if getattr(self, 'device_names', None) and i < len(self.device_names) else ''
                logger.log(f'探针已经移动移动到目标点: x={target_x}, y={target_y}，准备模板匹配移动')
                move_to_target(target_x, target_y,self.indicator)
                time.sleep(2)

                # 🔴 检查内存压力，决定是否跳过模板匹配
                import psutil
                import gc
                skip_template = False
                try:
                    mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    if mem_mb > 600:  # 超过 600MB
                        logger.log(f'[WARNING] 内存压力过大 ({mem_mb:.0f}MB)，跳过第{i}个点的模板匹配')
                        skip_template = True
                        gc.collect()  # 强制垃圾回收
                except Exception as e:
                    logger.log(f'[WARNING] 内存检查失败: {e}')
                
                if not skip_template:
                    #这里的template_error如果是true，说明模板匹配有问题，这个点就直接跳过，不匹配了
                    template_error = self.mainpage1.match_and_move()
                    if template_error:
                        logger.log(f'该点模板匹配失败: x={target_x}, y={target_y}，跳过当前点的处理')
                        continue
                else:
                    time.sleep(0.5)  # 简单等待以确保稳定


                locationClass.locationX, locationClass.locationY,_ = getPosition()
                time.sleep(1)  # 等待 1 秒，确保探针稳定

                if self.DontTest is False:
                    keithley = SIM928ConnectionThread.anc
                    keithley.use_rear_terminals  # 使用仪器前面端子
                    keithley.wires
                    keithley.apply_voltage()  # 设置为电压源
                    keithley.compliance_current = 0.1  # 设置合规电流
                    keithley.auto_range_source()
                    keithley.measure_current()  # 设置为测量电流
                    keithley.enable_source()  # 打开源表
                    keithley.source_voltage = 0.1

                    self.PushBack(True)
                    template_error = self.mainpage1.match_and_move()
                    if template_error:
                        logger.log(f'该点模板匹配失败: x={target_x}, y={target_y}，跳过当前点的处理')
                        self.PullBack()
                        continue

                    time.sleep(0.5)  # 等待 1 秒，确保探针稳定
                    anc = NeedelConnectionThread.anc
                    anc.write('[ch1:0]'.encode())
                    time.sleep(0.1)  # 等待 1 秒，确保探针稳定



                    current = keithley.current
                    logger.log("本次按压完成后的电流是",str(current))

                    if current >= 9e-10:
                        # 关闭继电器
                        d = bytes.fromhex('A0 01 00 A1')  # 关闭
                        RelayConnectionThread.anc.write(d)
                        time.sleep(1)

                        #执行IU计算
                        self.mainpage1.CalIU(self.device_names[i])
                        d = bytes.fromhex('A0 01 01 A2')  # 打开
                        RelayConnectionThread.anc.write(d)
                        time.sleep(1)


                    else:
                        logger.log("当前时刻测量失败")
                    self.PullBack()

                self.mainpage1.save_image()
        except Exception as e:
            logger.log(f"移动线程出现异常: {e}")
            self.PullBack()
        finally:
            test_event.clear()

    def continue_test(self):
        if not test_event.is_set():
            with SerialLock.serial_lock:
                current_x, current_y,_ = getPosition()
        nearest_index = self.find_nearest_index(current_x, current_y)
        start_index = nearest_index  if nearest_index < len(self.device_positions) else 0
        move_thread = threading.Thread(target=self.move_to_all_targets, args=(start_index,), daemon=True)
        move_thread.start()

    def stop_test(self):
        test_event.clear()
        logger.log(f"当前一个芯片测量结束后，会自动终止测试")



    # def calculate_device_positions(self, top_left, top_right, bottom_right, rows, cols):
    #     x = np.linspace(top_left[0], top_right[0], cols)
    #     y = np.linspace(top_left[1], bottom_right[1], rows)
    #     xx, yy = np.meshgrid(x, y)
    #
    #     # 转置网格点矩阵，然后展平，实现竖向编号
    #     return list(zip(xx.T.flatten(), yy.T.flatten()))

    import numpy as np

    # def calculate_device_positions(self,
    #                                inner_top_left, inner_top_left_row, inner_top_left_col,
    #                                inner_top_right, inner_top_right_row, inner_top_right_col,
    #                                inner_bottom_right, inner_bottom_right_row, inner_bottom_right_col,
    #                                outer_rows, outer_cols):
    #     """
    #     计算扩展矩阵的点阵列（使用1-based行列索引）
    #
    #     参数:
    #     - inner_top_left: 内部矩阵左上角坐标 (x, y)
    #     - inner_top_left_row: 左上角在外部矩阵中的行号 (1-based)
    #     - inner_top_left_col: 左上角在外部矩阵中的列号 (1-based)
    #     - inner_top_right: 内部矩阵右上角坐标 (x, y)
    #     - inner_top_right_row: 右上角在外部矩阵中的行号 (1-based)
    #     - inner_top_right_col: 右上角在外部矩阵中的列号 (1-based)
    #     - inner_bottom_right: 内部矩阵右下角坐标 (x, y)
    #     - inner_bottom_right_row: 右下角在外部矩阵中的行号 (1-based)
    #     - inner_bottom_right_col: 右下角在外部矩阵中的列号 (1-based)
    #     - outer_rows: 外部矩阵总行数
    #     - outer_cols: 外部矩阵总列数
    #
    #     返回:
    #     - 扩展矩阵所有点的坐标列表 [(x1, y1), (x2, y2), ...]
    #     """
    #
    #     # 将1-based索引转换为0-based（用于内部计算）
    #     tl_row = inner_top_left_row - 1
    #     tl_col = inner_top_left_col - 1
    #     tr_row = inner_top_right_row - 1
    #     tr_col = inner_top_right_col - 1
    #     br_row = inner_bottom_right_row - 1
    #     br_col = inner_bottom_right_col - 1
    #
    #     # 计算水平和垂直方向的单位间距
    #     # 水平间距 (基于右上角和左上角的差异)
    #     dx = (inner_top_right[0] - inner_top_left[0]) / (tr_col - tl_col) if (tr_col != tl_col) else 0
    #     # 垂直间距 (基于右下角和右上角的差异)
    #     dy = (inner_bottom_right[1] - inner_top_right[1]) / (br_row - tr_row) if (br_row != tr_row) else 0
    #
    #     # 计算外部矩阵四个角的坐标
    #     # 左上角
    #     outer_top_left = (
    #         inner_top_left[0] - dx * tl_col,
    #         inner_top_left[1] - dy * tl_row
    #     )
    #
    #     # 右上角
    #     outer_top_right = (
    #         inner_top_right[0] + dx * (outer_cols - 1 - tr_col),
    #         inner_top_right[1] - dy * tr_row
    #     )
    #
    #     # 右下角
    #     outer_bottom_right = (
    #         inner_bottom_right[0] + dx * (outer_cols - 1 - br_col),
    #         inner_bottom_right[1] + dy * (outer_rows - 1 - br_row)
    #     )
    #
    #     # 生成扩展矩阵的点阵列
    #     x = np.linspace(outer_top_left[0], outer_top_right[0], outer_cols)
    #     y = np.linspace(outer_top_left[1], outer_bottom_right[1], outer_rows)
    #     xx, yy = np.meshgrid(x, y)
    #
    #     # 转置网格点矩阵，然后展平，实现竖向编号
    #     return list(zip(xx.T.flatten(), yy.T.flatten()))

    import numpy as np

    def calculate_device_positions(self,
                                   inner_top_left, inner_top_left_row, inner_top_left_col,
                                   inner_top_right, inner_top_right_row, inner_top_right_col,
                                   inner_bottom_right, inner_bottom_right_row, inner_bottom_right_col,
                                   outer_rows, outer_cols):
        """
        计算设备坐标（适配X轴反转 + S型扫描顺序）
        列顺序：从右到左（最右侧为第1列）
        行顺序：奇数列（从右数）自上而下，偶数列自下而上
        """
        # 转换为0-based索引
        tl_row = inner_top_left_row - 1
        tl_col = inner_top_left_col - 1
        tr_row = inner_top_right_row - 1
        tr_col = inner_top_right_col - 1
        br_row = inner_bottom_right_row - 1
        br_col = inner_bottom_right_col - 1

        # 计算单位间距（允许dx为负）
        dx = (inner_top_right[0] - inner_top_left[0]) / (tr_col - tl_col) if (tr_col != tl_col) else 0
        dy = (inner_bottom_right[1] - inner_top_right[1]) / (br_row - tr_row) if (br_row != tr_row) else 0

        # 计算外部矩阵四个角的坐标
        outer_top_left = (
            inner_top_left[0] - dx * tl_col,
            inner_top_left[1] - dy * tl_row
        )
        outer_top_right = (
            inner_top_right[0] + dx * (outer_cols - 1 - tr_col),
            inner_top_right[1] - dy * tr_row
        )
        outer_bottom_right = (
            outer_top_right[0],  # X与右上角对齐
            inner_bottom_right[1] + dy * (outer_rows - 1 - br_row)
        )

        # 生成网格（X从右到左：start > stop）
        x = np.linspace(outer_top_right[0], outer_top_left[0], outer_cols)
        y = np.linspace(outer_top_left[1], outer_bottom_right[1], outer_rows)
        xx, yy = np.meshgrid(x, y, indexing='xy')

        # S型扫描顺序（从右到左的列，奇数列上→下，偶数列下→上）
        points = []
        for col_idx in range(outer_cols):  # col_idx=0是最右侧列
            col = outer_cols - 1 - col_idx  # 转换为网格索引
            if col_idx % 2 == 0:  # 奇数列（从右数）：自上而下
                points.extend([(xx[row, col], yy[row, col]) for row in range(outer_rows)])
            else:  # 偶数列：自下而上
                points.extend([(xx[row, col], yy[row, col]) for row in reversed(range(outer_rows))])

        return points
    # 鼠标点击事件处理函数
    def on_click(self,event):
        # 忽略坐标轴外的点击
        if event.xdata is None or event.ydata is None:
            return

        try:
            click_x, click_y = float(event.xdata), float(event.ydata)
            nearest_index = self.find_nearest_index(click_x, click_y)
            target_x, target_y = self.device_positions[nearest_index]
            target_x, target_y = float(target_x), float(target_y)

            logger.log(f"地图点击：移动到目标点 ({target_x:.4f}, {target_y:.4f})")

            # 使用持久化的线程池提交任务，避免重复创建线程带来的开销
            future = self.move_executor.submit(move_to_target, target_x, target_y, self.indicator)
            future.add_done_callback(self.on_move_complete)
        except (ValueError, TypeError) as e:
            logger.log(f"on_click 坐标转换失败: 错误={e}")


    def on_move_complete(self,future):
        # 当 move_to_target 完成后，此回调在主线程中被触发
        try:
            # 获取移动结果，并更新UI（如果需要）
            result = future.result()
            if result:
                locationClass.locationX, locationClass.locationY = result
                logger.log(f"地图点击移动完成，当前位置: ({locationClass.locationX:.4f}, {locationClass.locationY:.4f})")
            else:
                # 如果没有返回有效结果，重新获取一次
                locationClass.locationX, locationClass.locationY, _ = getPosition()

            # 将后续的耗时操作（模板匹配）也放入后台线程，防止阻塞UI
            threading.Thread(target=self._post_move_actions, daemon=True).start()

        except Exception as e:
            logger.log(f"移动完成回调(on_move_complete)中出现异常: {e}")

    def _post_move_actions(self):
        # 移动后的耗时操作（如模板匹配）
        try:
            # 等待探针稳定
            time.sleep(1)
            logger.log("准备执行移动后的模板匹配...")
            self.mainpage1.match_and_move()
            logger.log("移动后的模板匹配完成。")
        except Exception as e:
            logger.log(f"后台模板匹配(_post_move_actions)中出现异常: {e}")

    # 找到距离当前位置最近的点的索引
    def find_nearest_index(self,current_x, current_y):
        try:
            # 确保输入是浮点数
            current_x = float(current_x)
            current_y = float(current_y)
            # 计算距离时确保坐标转换为浮点数
            distances = [np.sqrt((current_x - float(pos[0]))**2 + (current_y - float(pos[1]))**2) for pos in self.device_positions]
            nearest_index = np.argmin(distances)
            return nearest_index
        except (ValueError, TypeError) as e:
            logger.log(f"find_nearest_index 转换失败: current=({current_x}, {current_y}), 错误={e}")
            return 0  # 返回第一个索引作为默认值

    def start_map_creation(self):
        # 在主线程中执行 CreateMap
        self.CreateMap()

    def calculate_device_names(self, left_top_name: str, right_top_name: str, right_bottom_name: str, rows: int, cols: int):
        """
        使用三个基准名称（左上、右上、右下）为地图内每个点生成名称。
        命名规则：
        - 水平移动（屏幕左→右）：第二个字母按列依次+1（考虑 A..Z 循环），后缀不变。
        - 垂直移动（从上到下）：2 -> 1（字母不变），1 -> 2（第一个字母-1，并在 A..Z 内循环）。
        - 每个字母组合有两份，后缀为 _1 或 _2。
        按与 device_positions 相同的 S 型扫描顺序展平返回。
        """
        def parse_name(name: str):
            letters, suf = name.split('_')
            if len(letters) != 2:
                raise ValueError('字母部分长度必须为2')
            return ord(letters[0].upper()), ord(letters[1].upper()), int(suf)

        def format_name(a_ord: int, b_ord: int, suffix: int) -> str:
            return f"{chr(a_ord)}{chr(b_ord)}_{suffix}"

        def wrap_inc(letter_ord: int, steps: int) -> int:
            base = ord('A'); span = 26
            return base + ((letter_ord - base + steps) % span)

        def wrap_dec(letter_ord: int, steps: int) -> int:
            base = ord('A'); span = 26
            return base + ((letter_ord - base - steps) % span)

        if not left_top_name or '_' not in left_top_name:
            return [f"Dev_{i}" for i in range(rows * cols)]

        try:
            a0, b0, s0 = parse_name(left_top_name)
            if right_top_name and '_' in right_top_name:
                a_rt, b_rt, s_rt = parse_name(right_top_name)
            else:
                # 右上 = 左上向右 (cols-1) 个位置（第二个字母增加，循环）
                a_rt, b_rt, s_rt = a0, wrap_inc(b0, cols - 1), s0
        except Exception:
            return [f"Dev_{i}" for i in range(rows * cols)]

        # 生成首行（屏幕左→右，第二个字母递增并在A..Z内循环）
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        for c in range(cols):
            grid[0][c] = format_name(a0, wrap_inc(b0, c), s0)

        # 每列向下递推（第一个字母在A..Z内循环递减，仅当 1->2 切换时）
        for c in range(cols):
            a, b, s = parse_name(grid[0][c])
            for r in range(1, rows):
                if s == 2:
                    s = 1
                else:
                    s = 2
                    a = wrap_dec(a, 1)
                grid[r][c] = format_name(a, b, s)

        # 一致性提示（非强校验）
        try:
            if grid[0][-1] != format_name(a_rt, b_rt, s_rt):
                logger.log(f"提示：根据左上推算的右上是 {grid[0][-1]}，与提供的右上 {format_name(a_rt,b_rt,s_rt)} 不一致，将以推算规则为准。")
        except Exception:
            pass

        if right_bottom_name and '_' in right_bottom_name:
            try:
                if grid[rows-1][cols-1] != right_bottom_name:
                    logger.log(f"提示：根据规则推算的右下是 {grid[rows-1][cols-1]}，与提供的右下 {right_bottom_name} 不一致，将以推算规则为准。")
            except Exception:
                pass

        names_s = []
        for col_idx in range(cols):
            # c = cols - 1 - col_idx # 之前是从右到左遍历列
            c = col_idx  # 现在从左到右遍历列
            if col_idx % 2 == 0:  # 偶数列（从左数）：自上而下
                for r in range(rows):
                    names_s.append(grid[r][c])
            else:  # 奇数列：自下而上
                for r in reversed(range(rows)):
                    names_s.append(grid[r][c])
        return names_s

