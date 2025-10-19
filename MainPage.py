import os
import subprocess
import sys

from CameraConfig.CameraParams_const import MV_GIGE_DEVICE, MV_USB_DEVICE
from DailyLogger import DailyLogger
from Load_Mat import load_and_plot_latest_mat_signals
from StopClass import StopClass

# 定义你要添加的库文件路径
custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"

# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)
import cv2
import threading
import time

from datetime import datetime
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from CameraConfig.CamOperation_class import CameraOperation
from CameraConfig.CameraParams_header import MV_CC_DEVICE_INFO_LIST
from CameraConfig.ImagePro import load_templates, template, match_device_templates
from CameraConfig.MvCameraControl_class import MvCamera
from LTDS import ReturnNeedleMove, WhileMove
from Microscope import ReturnZauxdll
from SerialPage import SIM928ConnectionThread, RelayConnectionThread, NeedelConnectionThread
from demo import Ui_MainWindow
# 导入全局温度配置
from TemperatureConfig import set_low, set_high, is_low


def handle_coordinates(x, y):
    print(f"Received coordinates: x={x}, y={y}")

# 获取日志器实例
logger = DailyLogger()

global red_dot_x
global red_dot_y


class MainPage1(QMainWindow, Ui_MainWindow):
    micro_distanceY = 0.5
    micro_distanceX = 0.5
    needle_distanceY = 300
    needle_distanceX = 300
    needle_distanceZ = 300

    obj_cam_operation = None
    equipment = 0  # 0代表电探针，1代表光纤
    stop_flag = False
    stop_num = 0
    # 默认的脚本位置
    import_script = "./jiaoben.py"
    # 默认的保存路径
    save_script = 'D:\\lzg\\data\\' + time.strftime("save_%Y-%m-%d_%H-%M-%S") + '\\IV\\'

    #全局的视频帧，为了让其他类也能调用截图
    global_frame = None

    # 给小灯设置颜色
    @staticmethod
    def get_stylesheet(status):
        color = "red" if status else "green"
        return f"""
               QLabel {{
                   background-color: {color};
                   border-radius: 20px;
                   border: 1px solid black;
               }}
           """

    def __init__(self, label_video, label_cameraLabel, Button_screenshot, lineEdit_savePath, Button_browse,
                 Button_needleTemplate,
                 Button_padTemplate, Button_iuCalculate, plainTextEdit_log, log_file,Checkbox_templateDevice,
                 Checkbox_microAutoTrace,Checkbox_ElecNeedle, Checkbox_Light,
                 Button_Micro_up, Button_Micro_down, Button_Micro_left, Button_Micro_right,
                 Button_needle1Up, Button_needle1Down, Button_needle1Left, Button_needle1Right,
                 lineEdit_needle1Xdistance, lineEdit_needle1Ydistance, lineEdit_needle1Zdistance,
                 Button_needle1SetXdisConfirm, Button_needle1SetYdisConfirm, Button_needle1SetZdisConfirm,
                 label_light,
                 lineEdit_SIM928, Button_SIM928,
                 Button_pushing, Button_pulling,
                 Button_relay, label_needle1, lineEdit_SaveResult,
                 lineEdit_needleSetXdis, lineEdit_needleSetYdis,lineEdit_needleSetZdis,
                 lineEdit_microSetXdis, lineEdit_microSetYdis,lineEdit_Scripts,
                 plot_Label,
                 Checkbox_lowTemp, Checkbox_highTemp):
        super().__init__()

        self.plot_Label = plot_Label

        self.lineEdit_Scripts = lineEdit_Scripts

        self.lineEdit_needleSetXdis = lineEdit_needleSetXdis
        self.lineEdit_needleSetYdis = lineEdit_needleSetYdis
        self.lineEdit_needleSetZdis = lineEdit_needleSetZdis
        self.lineEdit_microSetXdis = lineEdit_microSetXdis
        self.lineEdit_microSetYdis = lineEdit_microSetYdis

        MainPage1.micro_distanceX = float(self.lineEdit_microSetXdis.text())
        MainPage1.micro_distanceY = float(self.lineEdit_microSetYdis.text())
        MainPage1.needle_distanceY = float(self.lineEdit_needleSetYdis.text())
        MainPage1.needle_distanceX = float(self.lineEdit_needleSetXdis.text())
        MainPage1.needle_distanceZ = float(self.lineEdit_needleSetZdis.text())

        # 是否显示器件的模板匹配，True显示，False不显示
        self.DeviceTemplate_view = False

        # 调用电学测量函数，传入保存路径
        self.lineEdit_SaveResult = lineEdit_SaveResult

        # 电和光的选择按钮
        self.label_needle1 = label_needle1

        self.Checkbox_ElecNeedle = Checkbox_ElecNeedle
        self.Checkbox_Light = Checkbox_Light

        self.voltage928max = 0

        # 日志的路径
        self.log_file = log_file

        # 保存图片的默认路径
        self.save_folder = "./"

        # 刚开始默认显微镜不跟随
        self.align_allowed = False
        self.allow_alignment = True  # 控制对齐是否允许的标志

        # 初始化指示灯
        self.indicator = label_light
        self.status = False
        self.indicator.setStyleSheet(MainPage1.get_stylesheet(self.status))

        # 显微镜移动方向
        self.microY = 1
        self.microX = 0
        self.microup = 1
        self.microdown = -1
        self.microleft = 1
        self.microright = -1

        # 探针移动方向
        self.needleup = 0
        self.needledown = 1
        self.needleuleft = 2
        self.needleright = 3

        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        self.cam = MvCamera()

        self.x_dia = 0
        self.y_dia = 0
        self.dia = np.zeros([2, 2])

        self.pad_x_dia = 0
        self.pad_y_dia = 0
        self.initCamera()
        self.timer = QTimer()
        self.label_video = label_video

        # 保护帧访问的锁，避免多线程读写冲突
        self._frame_lock = threading.Lock()
        # 帧计数器用于节流重载计算
        self._frame_idx = 0
        # 缓存dia偏移及mtime，避免每帧读文件
        self._dia_cache = {'mtime': None, 'xdia': 0, 'ydia': 0}

        self.label_video.mousePressEvent = self.mousePressEvent

        self.label_cameraLabel = label_cameraLabel
        self.timer.timeout.connect(self.update_frame)
        # 将UI刷新频率从 ~33FPS 降到 ~16FPS，减轻相机与处理压力
        self.timer.start(60)
        self.frame_resized = 0
        self.lineEdit_savePath = lineEdit_savePath
        self.lineEdit_savePath.setText("C:\\Users\\Administrator\\PycharmProjects\\QTneedle\\ScreenShot")
        self.save_folder = "C:\\Users\\Administrator\\PycharmProjects\\QTneedle\\ScreenShot"

        self.plainTextEdit_log = plainTextEdit_log

        # 探针距离设置的输入框
        self.lineEdit_needle1Xdistance = lineEdit_needle1Xdistance
        self.lineEdit_needle1Ydistance = lineEdit_needle1Ydistance
        self.lineEdit_needle1Zdistance = lineEdit_needle1Zdistance

        self.lineEdit_needle1Xdistance.setText(str(MainPage1.needle_distanceX))
        self.lineEdit_needle1Ydistance.setText(str(MainPage1.needle_distanceY))
        self.lineEdit_needle1Zdistance.setText(str(MainPage1.needle_distanceZ))

        # 928更新电压
        self.lineEdit_SIM928 = lineEdit_SIM928
        Button_SIM928.clicked.connect(self.update_voltage)

        # 三个方向距离的确认按钮
        Button_needle1SetXdisConfirm.clicked.connect(self.update_needle_distanceX)
        Button_needle1SetYdisConfirm.clicked.connect(self.update_needle_distanceY)
        Button_needle1SetZdisConfirm.clicked.connect(self.update_needle_distanceZ)

        # 避免在子线程中操作UI：改为主线程直接保存当前帧
        Button_screenshot.clicked.connect(self.save_image)
        Button_browse.clicked.connect(self.browse_folder)
        # OpenCV 交互界面在子线程运行，避免阻塞Qt，但不要在子线程中操作Qt控件
        Button_needleTemplate.clicked.connect(lambda: threading.Thread(target=self.select_template).start())
        Button_padTemplate.clicked.connect(lambda: threading.Thread(target=self.select_pad_template).start())
        # 运行测量与绘图过程在主线程中更新UI，避免跨线程操作Qt控件导致崩溃
        Button_iuCalculate.clicked.connect(self.CalIU)

        # 显微镜是否跟随
        Checkbox_microAutoTrace.stateChanged.connect(self.checkbox_state_changed)

        # 是否显示探针的模板匹配
        Checkbox_templateDevice.stateChanged.connect(self.checkbox_template_changed)

        # 电探针和光的复选框
        self.Checkbox_ElecNeedle.toggled.connect(lambda: self.checkbox_ElecNeedle_changed(self.Checkbox_ElecNeedle))
        self.Checkbox_Light.toggled.connect(lambda: self.checkbox_Light_changed(self.Checkbox_Light))

        # 绑定温度模式切换
        self.Checkbox_lowTemp = Checkbox_lowTemp
        self.Checkbox_highTemp = Checkbox_highTemp
        self.Checkbox_lowTemp.toggled.connect(self.on_temp_mode_changed)
        self.Checkbox_highTemp.toggled.connect(self.on_temp_mode_changed)
        # 初始化默认模式
        self.on_temp_mode_changed()

        # 显微镜移动按钮
        Button_Micro_up.clicked.connect(self.move_microscope_up)
        Button_Micro_down.clicked.connect(self.move_microscope_down)
        Button_Micro_left.clicked.connect(self.move_microscope_left)
        Button_Micro_right.clicked.connect(self.move_microscope_right)

        # 探针移动按钮
        Button_needle1Up.clicked.connect(self.move_probe_up)
        Button_needle1Down.clicked.connect(self.move_probe_down)
        Button_needle1Left.clicked.connect(self.move_probe_left)
        Button_needle1Right.clicked.connect(self.move_probe_right)

        # 继电器的按钮
        Button_relay.clicked.connect(self.relay_IO)
        self.relay_flag = False

        Button_pushing.clicked.connect(lambda: threading.Thread(target=self.Pushing).start())
        Button_pulling.clicked.connect(lambda: threading.Thread(target=self.Pulling).start())

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log_display)
        self.log_timer.start(500)  # 每秒更新一次

        # 初次加载模板，并启动文件监视器，仅在模板发生变化时刷新缓存
        try:
            load_templates()
            self._template_files = [
                os.path.abspath('templateNeedle.png'),
                os.path.abspath('templatepad.png'),
                os.path.abspath('templateLight.png'),
            ]
            self._template_watcher = QtCore.QFileSystemWatcher(self)
            existing = [p for p in self._template_files if os.path.exists(p)]
            if existing:
                self._template_watcher.addPaths(existing)
            # 监视当前工作目录，以便捕获新建模板文件
            self._watched_dir = os.path.abspath(os.getcwd())
            self._template_watcher.addPath(self._watched_dir)
            self._template_watcher.fileChanged.connect(self._on_template_changed)
            self._template_watcher.directoryChanged.connect(self._on_template_dir_changed)
        except Exception as e:
            print(f"初始化模板监视器失败: {e}")

    def on_temp_mode_changed(self):
        if self.Checkbox_lowTemp.isChecked():
            set_low()
            logger.log("温度模式切换为：低温")
        elif self.Checkbox_highTemp.isChecked():
            set_high()
            logger.log("温度模式切换为：常温")

    # 继电器的开关函数
    def relay_IO(self):
        try:
            if self.relay_flag:
                d = bytes.fromhex('A0 01 00 A1')  # 关闭
                RelayConnectionThread.anc.write(d)
                self.relay_flag = False
                time.sleep(0.1)
            else:
                d = bytes.fromhex('A0 01 01 A2')  # 打开
                RelayConnectionThread.anc.write(d)
                self.relay_flag = True
                time.sleep(0.1)
        except (AttributeError, ValueError):
            print("请检查继电器否连接")

    # @staticmethod
    def initCamera(self):
        try:
            # Enumerate devices
            ret = self.cam.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, self.deviceList)
            if ret != 0:
                print(f"枚举设备失败，错误码: {ret}")
                return False

            if self.deviceList.nDeviceNum == 0:
                print("Find no device")
                return False

            # Select the first device
            nSelCamIndex = 0
            # Open selected device
            MainPage1.obj_cam_operation = CameraOperation(self.cam, self.deviceList, nSelCamIndex)
            ret = MainPage1.obj_cam_operation.Open_device()
            if ret != 0:
                print(f"打开设备失败，错误码: {ret}")
                return False

            # Start grabbing
            ret = MainPage1.obj_cam_operation.Start_grabbing(0)
            if ret != 0:
                print(f"开始取图失败，错误码: {ret}")
                return False

            print("相机初始化成功")
            return True

        except Exception as e:
            print(f"初始化相机时发生异常: {e}")
            return False

    def update_frame(self):
        try:
            self._frame_idx += 1

            # 🚩 检查是否正在重置缓冲区
            if hasattr(MainPage1.obj_cam_operation, 'is_resetting') and MainPage1.obj_cam_operation.is_resetting:
                return None  # 等待重置完成

            stFrameInfo = MainPage1.obj_cam_operation.st_frame_info
            if MainPage1.obj_cam_operation.buf_grab_image_size > 0 and stFrameInfo:
                if stFrameInfo.nWidth > 0 and stFrameInfo.nHeight > 0 and stFrameInfo.nFrameLen > 0:
                    try:
                        global red_dot_x, red_dot_y

                        # 从保存缓冲区复制数据，使用锁防止抓图线程写入过程中发生竞态
                        with MainPage1.obj_cam_operation.buf_lock:
                            st_info = MainPage1.obj_cam_operation.st_frame_info
                            buf = MainPage1.obj_cam_operation.buf_save_image
                            
                            # ✅ 验证缓冲区有效性
                            if not st_info or st_info.nFrameLen <= 0 or buf is None:
                                return None
                            if st_info.nWidth <= 0 or st_info.nHeight <= 0:
                                return None
                            
                            try:
                                data = np.frombuffer(buf, dtype=np.uint8, count=st_info.nFrameLen).copy()
                            except Exception as e:
                                print(f"读取帧缓冲区失败: {e}")
                                return None
                                
                            width = st_info.nWidth
                            height = st_info.nHeight

                        # 解码 Bayer -> RGB（这一步较重，必要时可进一步降低分辨率）
                        try:
                            frame = data.reshape((height, width))
                            rgb = cv2.cvtColor(frame, cv2.COLOR_BayerBG2RGB)

                            # 单次resize到目标显示尺寸，避免二次缩放
                            target_size = (851, 851)
                            resized = cv2.resize(rgb, target_size, interpolation=cv2.INTER_LINEAR)
                        finally:
                            # 🔴 及时释放临时图像数据
                            del data
                            if 'frame' in locals():
                                del frame

                        # 写入共享帧前加锁
                        with self._frame_lock:
                            self.frame_resized = resized

                        # 仅在必要频率做模板/器件匹配，降低CPU占用
                        # 每2帧进行一次针/光模板匹配
                        do_template = (self._frame_idx % 2 == 0)
                        # 每15帧进行一次器件模板匹配（且仅当显示开启）
                        do_device_match = self.DeviceTemplate_view

                        # 缓存并读取dia偏移（仅当文件修改时才重载）
                        try:
                            dia_file = 'dia' + str(MainPage1.equipment) + '.txt'
                            cur_mtime = os.path.getmtime(dia_file) if os.path.exists(dia_file) else None
                            if cur_mtime and cur_mtime != self._dia_cache['mtime']:
                                with open(dia_file, 'r', encoding='utf-8') as file:
                                    line = file.readline().strip()
                                    numbers = line.split(',') if line else []
                                    if len(numbers) >= 2:
                                        self._dia_cache['xdia'] = int(numbers[0])
                                        self._dia_cache['ydia'] = int(numbers[1])
                                        self._dia_cache['mtime'] = cur_mtime
                        except Exception as e:
                            # 使用缓存中的默认值
                            pass

                        xdia = self._dia_cache['xdia']
                        ydia = self._dia_cache['ydia']

                        if do_template:
                            red_dot_x, red_dot_y, self.board_height, self.board_width = template(resized, xdia,
                                                                                                 ydia, MainPage1.equipment)
                        # 如果开启了器件显示，降低频率进行匹配
                        if do_device_match:
                            match_device_templates(resized)

                        aligned = self.align_frame_with_probe()
                        if aligned is None or isinstance(aligned, int):
                            aligned = resized

                        h, w, c = aligned.shape
                        bytes_per_line = 3 * w
                        q_image = QImage(aligned.data, w, h, bytes_per_line, QImage.Format_BGR888).copy()

                        self.label_video.setPixmap(QPixmap.fromImage(q_image))
                        # 提取中心区域
                        center_width, center_height = w // 2, h // 2
                        start_x, start_y = max(0, center_width // 2), max(0, center_height // 2)
                        q_image_zoom = q_image.copy(start_x, start_y, center_width, center_height)
                        self.label_cameraLabel.setPixmap(QPixmap.fromImage(q_image_zoom))

                        MainPage1.global_frame = aligned
                        return aligned

                    except Exception as e:
                        print(f"更新视频帧异常: {e}")
        except Exception as e_outer:
            print(f"update_frame外层异常: {e_outer}")

    def _on_template_changed(self, path):
        # 文件更改时刷新模板，并重新添加监视（Windows上有时需要）
        try:
            load_templates()
        except Exception as e:
            print(f"刷新模板失败({path}): {e}")
        finally:
            try:
                if os.path.exists(path):
                    self._template_watcher.addPath(path)
            except Exception:
                pass

    def _on_template_dir_changed(self, path):
        # 目录变化时尝试添加新创建的模板文件
        try:
            for f in self._template_files:
                if os.path.exists(f) and f not in self._template_watcher.files():
                    try:
                        self._template_watcher.addPath(f)
                    except Exception:
                        pass
        except Exception as e:
            print(f"监视目录更新失败({path}): {e}")

    def browse_folder(self):
        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(self, "选择存储路径", "", QFileDialog.ShowDirsOnly)
        if folder:
            # 将选择的文件夹路径显示在文本框中
            self.lineEdit_savePath.setText(folder)
            self.save_folder = folder

    def save_image(self):
        # 使用最新帧保存，避免在子线程/此处触发update_frame导致UI竞争
        with self._frame_lock:
            frame = None if isinstance(self.frame_resized, int) else self.frame_resized.copy()
        if frame is None or frame.size == 0:
            print("当前无可保存的帧")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"{timestamp}.png"
        path = os.path.join(self.save_folder, filename)
        try:
            cv2.imwrite(path, frame)
        except Exception as e:
            print(f"保存图片失败: {e}")

    def match_and_move(self):
        # 🚩 检查是否正在重置缓冲区
        if hasattr(MainPage1.obj_cam_operation, 'is_resetting') and MainPage1.obj_cam_operation.is_resetting:
            return False  # 等待重置完成
        
        # 🔴 检查内存压力
        import psutil
        import gc
        try:
            mem_mb = psutil.Process().memory_info().rss / 1024 / 1024
            if mem_mb > 600:  # 超过 600MB
                print(f"[WARNING] 内存压力过大 ({mem_mb:.0f}MB)，跳过模板匹配")
                gc.collect()  # 强制垃圾回收
                return False
        except Exception as e:
            print(f"[WARNING] 内存检查失败: {e}")
        
        # 获取当前帧并进行模板匹配
        video = self.update_frame()
        
        # 如果获取帧失败，返回False
        if video is None:
            return False
        
        try:
            matched_centers = match_device_templates(video)
        finally:
            # 🔴 立即释放大图像对象
            del video
            gc.collect()  # 强制垃圾回收

        # 如果没有匹配点，直接返回True
        if not matched_centers:
            return True

        min_distance = float('inf')
        probe_x, probe_y = self.get_probe_position()
        closest = [probe_x, probe_y]

        for center_x, center_y in matched_centers:
            distance = pow(abs(center_x - probe_x), 2) + pow(abs(center_y - probe_y), 2)
            if distance < min_distance:
                min_distance = distance
                closest = [center_x, center_y]

        if min_distance <= 2000:
            self.move_probe_to_target(closest[0], closest[1])
            return False
        else:
            return True



    def selectROIWithAdjust(self, window_name, img):
        """自定义的ROI选择函数，支持通过关闭按钮取消"""
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, img)

        # 初始化ROI参数
        rect = (0, 0, 0, 0)
        drawing = False
        roi_selected = False
        start_x, start_y = -1, -1

        def mouse_callback_roi(event, x, y, flags, param):
            nonlocal rect, drawing, roi_selected, start_x, start_y
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                start_x, start_y = x, y
                rect = (x, y, 0, 0)
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    rect = (min(start_x, x), min(start_y, y), abs(x - start_x), abs(y - start_y))
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
                roi_selected = True

        cv2.setMouseCallback(window_name, mouse_callback_roi)

        start_time = time.time()
        while True:
            # 显示当前图像和ROI
            display_img = img.copy()
            if drawing or roi_selected:
                x, y, w, h = rect
                cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_img, "Drag to select ROI, Enter to confirm", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(display_img, "ESC to cancel, Close window to exit", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow(window_name, display_img)

            key = cv2.waitKey(1) & 0xFF

            # 检查窗口是否被关闭
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    cv2.setMouseCallback(window_name, lambda *args: None)
                    return None
            except:
                cv2.setMouseCallback(window_name, lambda *args: None)
                return None

            if key == 13:  # Enter键确认选择
                if rect[2] > 0 and rect[3] > 0:
                    break
                else:
                    print("请先选择一个有效的区域")
            elif key == 27:  # ESC键取消
                cv2.setMouseCallback(window_name, lambda *args: None)
                return None
            elif roi_selected:  # 鼠标选择完成
                # 等待用户按Enter确认
                pass

            # 超时检查
            if time.time() - start_time > 60:  # 60秒超时
                cv2.setMouseCallback(window_name, lambda *args: None)
                return None

        cv2.setMouseCallback(window_name, lambda *args: None)
        return rect

    def take_screenshot(self):
        # 确保窗口不存在
        try:
            cv2.destroyWindow("Take Screenshot")
        except:
            pass

        # 读取帧时加锁，避免并发
        with self._frame_lock:
            frame = None if isinstance(self.frame_resized, int) else self.frame_resized.copy()
        if frame is None or frame.size == 0:
            print("当前无可用帧")
            return None

        # 使用自定义的ROI选择函数
        r = self.selectROIWithAdjust("Take Screenshot", frame)

        # 检查用户是否取消选择或选择了无效的区域
        if r is None or r[2] == 0 or r[3] == 0:
            print("框选被取消或无效。")
            cv2.destroyWindow("Take Screenshot")
            return None

        # 获取选中的矩形区域，并进行裁剪
        x, y, w, h = r
        cropped_image = frame[y:y + h, x:x + w]

        # 保存截图
        cv2.imwrite("screenshot.png", cropped_image)
        print("截图已保存为 screenshot.png")
        cv2.destroyWindow("Take Screenshot")
        return cropped_image

    def select_template(self):
        # 读取帧时加锁，避免与update_frame竞争
        with self._frame_lock:
            param = None if isinstance(self.frame_resized, int) else self.frame_resized.copy()
        if param is None or param.size == 0:
            print("当前无可用帧，无法选择模板")
            return None

        # 确保窗口不存在
        try:
            cv2.destroyWindow("Select Needle Template")
        except:
            pass

        # 使用自定义的ROI选择函数
        r = self.selectROIWithAdjust("Select Needle Template", param)

        # 检查用户是否取消选择或选择了无效的区域
        if r is None or r[2] == 0 or r[3] == 0:
            print("选择被取消或无效。")
            cv2.destroyWindow("Select Needle Template")
            return None

        mouseX = 0
        mouseY = 0
        mouse_clicked = False
        window_closed = False

        # 定义鼠标回调函数
        def mouse_callback(event, X, Y, flags, userdata):
            nonlocal mouseX, mouseY, mouse_clicked
            if event == cv2.EVENT_LBUTTONDOWN and not mouse_clicked:
                print(f"鼠标点击坐标: ({X}, {Y})")
                mouseX = X
                mouseY = Y
                mouse_clicked = True
                # 解除回调
                cv2.setMouseCallback("Select Needle Template", lambda *args: None)

        # 设置鼠标回调
        cv2.setMouseCallback("Select Needle Template", mouse_callback)

        # 显示选中的区域和提示信息
        x, y, w, h = r
        temp_img = param.copy()
        cv2.rectangle(temp_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(temp_img, "Click reference point in selected area", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(temp_img, "Press ESC to cancel", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Select Needle Template", temp_img)

        # 使用一个小的等待时间，避免等待太长时间
        start_time = time.time()
        while True:
            # 以 1ms 的延迟等待键盘事件或鼠标点击
            key = cv2.waitKey(1) & 0xFF

            # 检查窗口是否被关闭
            try:
                if cv2.getWindowProperty("Select Needle Template", cv2.WND_PROP_VISIBLE) < 1:
                    window_closed = True
                    break
            except:
                window_closed = True
                break

            if mouse_clicked:  # 判断是否有鼠标点击
                break
            if key == 27:  # 监听 ESC 键退出
                print("用户按下 ESC 键退出。")
                break
            # 超时检查，避免无限等待
            if time.time() - start_time > 30:  # 30秒超时
                print("操作超时。")
                break

        if window_closed or key == 27:
            cv2.destroyWindow("Select Needle Template")
            return None

        if not mouse_clicked:
            print("未检测到鼠标点击。")
            cv2.destroyWindow("Select Needle Template")
            return None


        # 获取选中的矩形区域，并进行裁剪
        x, y, w, h = r
        # 计算ROI中心点（固定基准）
        roi_center_x = x + w // 2
        roi_center_y = y + h // 2

        # 计算偏移量：鼠标点击位置相对于ROI中心的偏移
        self.x_dia = mouseX - roi_center_x
        self.y_dia = mouseY - roi_center_y


        cv2.destroyWindow("Select Needle Template")

        with open('dia' + str(MainPage1.equipment) + '.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.x_dia},{self.y_dia}")

        print(f"偏移量已保存: x_dia={self.x_dia}, y_dia={self.y_dia}")
        return True

    def select_pad_template(self):
        """新版Pad模板选择：框选一个pad + 点击参考点，自动匹配所有pad"""
        # 第一步：用户框选一个pad作为模板
        print("请框选一个pad作为模板")
        try:
            cv2.destroyWindow("Select Pad Template")
        except:
            pass

        # 使用摄像头当前帧
        with self._frame_lock:
            frame = None if isinstance(self.frame_resized, int) else self.frame_resized.copy()
        if frame is None or frame.size == 0:
            print("当前无可用帧")
            return None

        # 框选单个pad
        pad_roi = self.selectROIWithAdjust("Select Pad Template", frame)
        if pad_roi is None or pad_roi[2] == 0 or pad_roi[3] == 0:
            print("框选被取消或无效。")
            cv2.destroyWindow("Select Pad Template")
            return None

        # 裁剪出选中的pad
        x, y, w, h = pad_roi
        pad_template = frame[y:y + h, x:x + w]
        cv2.imwrite("templatepad.png", pad_template)
        print("Pad模板已保存")

        # 第二步：在原始图像中点击参考点
        print("请在图像中点击参考点（相对于框选的pad）")
        mouseX, mouseY = 0, 0
        mouse_clicked = False

        def mouse_callback(event, X, Y, flags, userdata):
            nonlocal mouseX, mouseY, mouse_clicked
            if event == cv2.EVENT_LBUTTONDOWN:
                print(f"参考点坐标: ({X}, {Y})")
                mouseX = X
                mouseY = Y
                mouse_clicked = True
                cv2.setMouseCallback("Select Reference Point", lambda *args: None)

        cv2.namedWindow("Select Reference Point", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Select Reference Point", mouse_callback)

        # 显示原始图像和框选区域
        display_img = frame.copy()
        cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(display_img, "Click reference point", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(display_img, "Press ESC to cancel", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Select Reference Point", display_img)

        start_time = time.time()
        while not mouse_clicked:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("用户取消操作")
                cv2.destroyWindow("Select Reference Point")
                return None
            if time.time() - start_time > 30:  # 超时
                print("操作超时")
                cv2.destroyWindow("Select Reference Point")
                return None

        cv2.destroyWindow("Select Reference Point")
        # 第三步：计算偏移量（相对于框选pad的中心）
        pad_center_x = x + w // 2
        pad_center_y = y + h // 2
        x_dia = mouseX - pad_center_x
        y_dia = mouseY - pad_center_y
        print(f"偏移量计算：pad中心({pad_center_x},{pad_center_y}) -> 参考点({mouseX},{mouseY}) = ({x_dia},{y_dia})")

        # 保存偏移量
        with open('Paddia.txt', 'w', encoding='utf-8') as f:
            f.write(f"{x_dia},{y_dia}")
            f.flush()  # 强制刷新缓冲区
            os.fsync(f.fileno())  # 强制同步到磁盘
        return True


    def CalIU(self,PadName):

        """
            Function:
              用于测量探针的IU性能，这里就是直接执行用户自己输入的JiaoBen文件
              执行后，强行将探针抬起来了，防止出现损坏
            Args:
              none
            Return:
              none
        """
        try:
            self.save_image()
            run_script = self.lineEdit_Scripts.text()
            if run_script == '':
                run_script = "./jiaoben.py"

            save_script = self.lineEdit_SaveResult.text()
            if save_script == '':
                save_script = 'D:\\lzg\\data\\' + time.strftime("save_%Y-%m-%d_%H-%M-%S") + '\\IV\\'

            result = subprocess.run(
                [sys.executable, run_script, save_script,PadName],
                capture_output=True,
                text=True,
                check=True,  # 如果返回非零会抛出异常
                encoding='utf-8',  # 明确指定编码
            )

            pixmap = load_and_plot_latest_mat_signals(save_script)
            if pixmap:
                # 调整图像大小以适应label
                scaled_pixmap = pixmap.scaled(
                    self.plot_Label.width() - 20,
                    self.plot_Label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.plot_Label.setPixmap(scaled_pixmap)
            else:
                self.plot_Label.setText("加载失败或未找到信号")


            logger.log(result.stdout)
            logger.log("当前时刻测量成功")

        except Exception as e:
            logger.log(f"执行过程中发生错误: {str(e)}")

    def update_log_display(self):
        '''
        Function:
            用于和定时器进行绑定，更新日志显示
        Args:
            none
        Return:
            none
        '''
        try:
            # 获取当天日志内容
            log_content = logger.get_today_logs()

            # 分割日志行并反转顺序（最新的在最前面）
            lines = log_content.split('\n')
            reversed_lines = lines[::-1]  # 反转列表

            # 取前10行（最新的10条）
            first_lines = reversed_lines[:10] if len(reversed_lines) >= 10 else reversed_lines

            # 更新日志显示内容
            self.plainTextEdit_log.setPlainText("\n".join(first_lines))

        except Exception as e:
            self.plainTextEdit_log.setPlainText(f"Log display error: {str(e)}")



    def checkbox_template_changed(self,state):
        # 根据复选框的状态更新标志位
        if state == Qt.Checked:
            self.DeviceTemplate_view = True
        else:
            self.DeviceTemplate_view = False

    def checkbox_state_changed(self, state):
        # 根据复选框的状态更新标志位
        if state == Qt.Checked:
            self.align_allowed = True
        else:
            self.align_allowed = False

    def checkbox_ElecNeedle_changed(self, Checkbox):
        # 根据复选框的状态更新标志位
        if Checkbox.isChecked:
            MainPage1.equipment = 0
            self.label_needle1.setText("探针位移")
        else:
            MainPage1.equipment = 1
            self.label_needle1.setText("光纤位移")

    def checkbox_Light_changed(self, Checkbox):
        # 根据复选框的状态更新标志位
        if Checkbox.isChecked:
            MainPage1.equipment = 1
            self.label_needle1.setText("光纤位移")
        else:
            MainPage1.equipment = 0
            self.label_needle1.setText("探针位移")

    # 自动跟随函数
    def align_frame_with_probe(self):
        if not self.allow_alignment:
            # 未启用对齐时直接返回当前帧
            with self._frame_lock:
                return self.frame_resized if not isinstance(self.frame_resized, int) else None

        # 初始化线程锁
        if not hasattr(self, '_align_lock'):
            self._align_lock = threading.Lock()

        # 防抖机制：检查上次对齐时间
        current_time = time.time()
        if hasattr(self, '_last_align_time'):
            if current_time - self._last_align_time < 0.5:  # 500ms内不重复启动
                with self._frame_lock:
                    return self.frame_resized if not isinstance(self.frame_resized, int) else None

        # 尝试获取锁，如果已经有线程在运行则直接返回
        if not self._align_lock.acquire(blocking=False):
            with self._frame_lock:
                return self.frame_resized if not isinstance(self.frame_resized, int) else None

        # 更新上次对齐时间
        self._last_align_time = current_time

        def align():
            try:
                # PID控制参数
                kp = 0.5  # 比例系数
                ki = 0.02  # 积分系数
                kd = 0.08  # 微分系数

                # 控制限制
                integral_limit = 40
                output_limit = 70
                dead_zone = 1.5  # 死区阈值
                stop_threshold = 50  # 停止阈值（更小）

                # PID状态变量
                integral_x, integral_y = 0, 0
                prev_error_x, prev_error_y = 0, 0
                last_output_x, last_output_y = 0, 0

                # 平滑移动参数
                max_accel = 25
                last_time = time.time()
                move_count = 0
                consecutive_small_moves = 0

                while self.align_allowed:
                    current_time = time.time()
                    dt = max(0.01, current_time - last_time)
                    last_time = current_time

                    # 获取当前帧（避免在循环中修改原始帧）
                    with self._frame_lock:
                        if isinstance(self.frame_resized, int):
                            break
                        current_frame = self.frame_resized.copy()
                    frame_center_x = current_frame.shape[1] // 2
                    frame_center_y = current_frame.shape[0] // 2

                    probe_x, probe_y = self.get_probe_position()
                    if probe_x is None:
                        print("模板匹配失败，无法获取探针位置")
                        break

                    # 计算误差
                    error_x = frame_center_x - probe_x
                    error_y = frame_center_y - probe_y
                    distance = np.sqrt(error_x ** 2 + error_y ** 2)

                    # 检查是否达到目标
                    if distance < stop_threshold:
                        break

                    # PID计算
                    # X轴
                    integral_x += error_x * dt
                    integral_x = np.clip(integral_x, -integral_limit, integral_limit)
                    derivative_x = (error_x - prev_error_x) / dt

                    output_x = kp * error_x + ki * integral_x + kd * derivative_x
                    output_x = np.clip(output_x, -output_limit, output_limit)

                    # Y轴
                    integral_y += error_y * dt
                    integral_y = np.clip(integral_y, -integral_limit, integral_limit)
                    derivative_y = (error_y - prev_error_y) / dt

                    output_y = kp * error_y + ki * integral_y + kd * derivative_y
                    output_y = np.clip(output_y, -output_limit, output_limit)

                    # 应用死区
                    if abs(output_x) < dead_zone:
                        output_x = 0
                    if abs(output_y) < dead_zone:
                        output_y = 0

                    # 加速度限制
                    if abs(output_x - last_output_x) > max_accel:
                        output_x = last_output_x + np.sign(output_x - last_output_x) * max_accel
                    if abs(output_y - last_output_y) > max_accel:
                        output_y = last_output_y + np.sign(output_y - last_output_y) * max_accel

                    last_output_x, last_output_y = output_x, output_y

                    # 动态速度调整（接近目标时减速）
                    speed_factor = 1.0
                    if distance < 15:
                        speed_factor = 0.4
                    elif distance < 30:
                        speed_factor = 0.7

                    output_x *= speed_factor
                    output_y *= speed_factor

                    # 检查是否需要移动
                    if output_x == 0 and output_y == 0:
                        consecutive_small_moves += 1
                        if consecutive_small_moves > 3:  # 连续3次无需移动则认为稳定
                            break
                        time.sleep(0.1)
                        continue
                    else:
                        consecutive_small_moves = 0

                    # 执行移动（使用更平滑的移动方式）
                    move_scale = 800  # 比原来的1000更保守

                    if output_y < 0:
                        ReturnZauxdll(self.microY, self.microdown * abs(output_y) / move_scale)
                    elif output_y > 0:
                        ReturnZauxdll(self.microY, self.microup * abs(output_y) / move_scale)

                    if output_x < 0:
                        ReturnZauxdll(self.microX, self.microright * abs(output_x) / move_scale)
                    elif output_x > 0:
                        ReturnZauxdll(self.microX, self.microleft * abs(output_x) / move_scale)

                    # 更新历史误差
                    prev_error_x = error_x
                    prev_error_y = error_y

                    # 调试信息（减少打印频率）
                    move_count += 1
                    # 自适应延迟
                    sleep_time = 0.12  # 基础延迟
                    if distance < 20:
                        sleep_time = 0.08
                    elif distance > 50:
                        sleep_time = 0.15

                    time.sleep(sleep_time)

            except Exception as e:
                print(f"对齐过程中出现错误: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                # 确保锁被释放
                try:
                    self._align_lock.release()
                except:
                    pass

        # 启动线程
        threading.Thread(target=align, daemon=True).start()
        return self.frame_resized

    # 获得探针位置
    def get_probe_position(self):
        global red_dot_x
        global red_dot_y
        return red_dot_x, red_dot_y

    # 显微镜移动函数
    def move_microscope_up(self):
        distance = self.get_distance(MainPage1.micro_distanceY, 0.5)
        threading.Thread(target=ReturnZauxdll, args=(self.microY, self.microup * distance)).start()

    def move_microscope_down(self):
        distance = self.get_distance(MainPage1.micro_distanceY, 0.5)
        threading.Thread(target=ReturnZauxdll, args=(self.microY, self.microdown * distance)).start()

    def move_microscope_left(self):
        distance = self.get_distance(MainPage1.micro_distanceX, 0.5)
        threading.Thread(target=ReturnZauxdll, args=(self.microX, self.microleft * distance)).start()

    def move_microscope_right(self):
        distance = self.get_distance(MainPage1.micro_distanceX, 0.5)
        threading.Thread(target=ReturnZauxdll, args=(self.microX, self.microright * distance)).start()

    def get_distance(self, input_distance, default_distance):
        try:
            return float(input_distance) if input_distance else default_distance
        except ValueError:
            return default_distance

    def move_probe_up(self):
        threading.Thread(target=WhileMove,
                         args=(0, self.indicator,MainPage1.equipment, MainPage1.needle_distanceY)).start()
        logger.log("探针往上移动了")

    def move_probe_down(self):
        threading.Thread(target=WhileMove,
                         args=(1, self.indicator,MainPage1.equipment, MainPage1.needle_distanceY)).start()
        logger.log("探针往下移动了")

    def move_probe_left(self):
        threading.Thread(target=WhileMove,
                         args=(2, self.indicator,MainPage1.equipment, MainPage1.needle_distanceX)).start()
        logger.log("探针往左移动了")

    def move_probe_right(self):
        threading.Thread(target=WhileMove,
                         args=(3, self.indicator,MainPage1.equipment, MainPage1.needle_distanceX)).start()
        logger.log("探针往右移动了")

    from PyQt5.QtWidgets import QMessageBox

    def update_needle_distanceX(self):
        try:
            input_value = float(self.lineEdit_needle1Xdistance.text())
            if input_value > 3000:
                QMessageBox.warning(
                    self,  # 父窗口
                    "输入超出范围",  # 窗口标题
                    "X 轴移动距离不能超过 3000！"  # 提示信息
                )
                # 可以在这里重置输入框的值（可选）
                self.lineEdit_needle1Xdistance.setText("3000")
            MainPage1.needle_distanceX = min(3000, input_value)
        except ValueError:
            QMessageBox.warning(
                self,
                "输入错误",
                "请输入有效的数字！"
            )

    def update_needle_distanceY(self):
        try:
            input_value = float(self.lineEdit_needle1Ydistance.text())
            if input_value > 3000:
                QMessageBox.warning(
                    self,
                    "输入超出范围",
                    "Y 轴移动距离不能超过 3000！"
                )
                self.lineEdit_needle1Ydistance.setText("3000")
            MainPage1.needle_distanceY = min(3000, input_value)
        except ValueError:
            QMessageBox.warning(
                self,
                "输入错误",
                "请输入有效的数字！"
            )

    def update_needle_distanceZ(self):
        try:
            input_value = float(self.lineEdit_needle1Zdistance.text())
            if input_value > 1000:
                QMessageBox.warning(
                    self,
                    "输入超出范围",
                    "Z 轴移动距离不能超过 1000！"
                )
                self.lineEdit_needle1Zdistance.setText("1000")
            MainPage1.needle_distanceZ = min(1000, input_value)
        except ValueError:
            QMessageBox.warning(
                self,
                "输入错误",
                "请输入有效的数字！"
            )


    def restart_program(self):
        python = sys.executable  # 当前 python 解释器路径
        os.execl(python, python, *sys.argv)  # 使用同样的参数重新执行该脚本

    # 鼠标点击运动
    def mousePressEvent(self, event):
        """
            Function:
                用户点击画面的一个位置，探针会移动到这个位置
            Args:
                鼠标左键点击事件
            Return:
                none
        """
        # 如果当前帧不可用，直接返回
        if isinstance(self.frame_resized, int) or self.frame_resized is None:
            return
        # 获取 label_video 在屏幕中的位置
        top_left_global = self.label_video.mapToGlobal(QtCore.QPoint(0, 0))

        # 获取鼠标点击位置的全局坐标
        global_point = event.globalPos()

        # 计算点击位置相对于 label_video 的位置
        relative_x = global_point.x() - top_left_global.x()
        relative_y = global_point.y() - top_left_global.y()

        # 获取视频的宽高
        video_width = self.frame_resized.shape[1]
        video_height = self.frame_resized.shape[0]

        # 设置目标坐标
        self.target_x = relative_x
        self.target_y = relative_y

        # 检查目标坐标是否在有效区域内
        if self.board_width / 2 <= self.target_x <= video_width - self.board_width / 2 and self.board_height / 2 <= self.target_y <= video_height - self.board_height / 2:
            if event.button() == QtCore.Qt.LeftButton:
                confirm = QMessageBox.question(self, '确认操作', '您确定要移动探针吗?',
                                               QMessageBox.Yes | QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    logger.log("执行了一次探针鼠标点击运动")
                    threading.Thread(target=self.move_probe_to_target, args=(self.target_x, self.target_y)).start()
                    self.indicator.setStyleSheet(MainPage1.get_stylesheet(False))
        elif 0 <= self.target_x <= video_width and 0 <= self.target_y <= video_height:
            QMessageBox.warning(self, '提示', '请在视频有效区域内点击！', QMessageBox.Ok)
            return

    # 计算距离并移动探针
    def move_probe_to_target(self, target_x, target_y):
        # 根据全局配置选择参数
        if is_low():
            distance_weight = 50  # 低温
            error = 6
            sleep_time = 0.2 #这里本来是0.5，但是为了加快速度改成0.2
        else:
            distance_weight = 10  # 常温
            error = 10
            sleep_time = 0.1

        self.allow_alignment = False  # 禁用对齐
        self.indicator.setStyleSheet(MainPage1.get_stylesheet(True))
        probe_x, probe_y = self.get_probe_position()
        distance = np.sqrt((target_x - probe_x) ** 2) *distance_weight
        while distance>=error:
            if StopClass.stop_num == 1:
                break
            if probe_x is None:
                logger.log("模板匹配失败，请先进行模板匹配")
                break
            if target_x < probe_x:
                ReturnNeedleMove(self.needleuleft, distance, self.indicator, True, False, MainPage1.equipment)
            elif target_x > probe_x:
                ReturnNeedleMove(self.needleright, distance, self.indicator, True, False, MainPage1.equipment)
            # 低温情况下time.sleep应该是0.5，常温情况是0.1
            time.sleep(sleep_time)
            probe_x, probe_y = self.get_probe_position()
            distance = np.sqrt((target_x - probe_x) ** 2)*distance_weight

        distance = np.sqrt((target_y - probe_y) ** 2)*distance_weight
        while distance>=error:
            if StopClass.stop_num == 1:
                break
            if probe_y is None:
                logger.log("模板匹配失败，请先进行模板匹配")
                break
            if target_y < probe_y:
                ReturnNeedleMove(self.needleup, distance, self.indicator, True, False, MainPage1.equipment)
            elif target_y > probe_y:
                ReturnNeedleMove(self.needledown, distance, self.indicator, True, False, MainPage1.equipment)
            # 低温情况下time.sleep应该是0.5，常温情况是0.1
            time.sleep(sleep_time)
            probe_x, probe_y = self.get_probe_position()
            distance = np.sqrt((target_y - probe_y) ** 2)*distance_weight

        self.allow_alignment = True  # 重新允许对齐
        self.indicator.setStyleSheet(MainPage1.get_stylesheet(False))
        StopClass.stop_num = 0

    # 928更新电压的函数
    def update_voltage(self):
        """
            Function:
                用于和按钮事件绑定，更新赋予探针的电压
            Args:
                none
            Return:
                none
        """
        # sim928_2 = SIM928(5, 'GPIB4::2::INSTR')
        keithley = SIM928ConnectionThread.anc
        if keithley is None:
            print("keithley未正常连接")
        else:
            try:
                voltage_input = 0.1 if not self.lineEdit_SIM928.text() else float(self.lineEdit_SIM928.text())
            except ValueError:
                voltage_input = 0.1
                print("输入的不是有效数字，已使用默认值 0.1")
            try:
                keithley.use_rear_terminals  # 使用仪器前面端子
                keithley.wires
                keithley.apply_voltage()  # 设置为电压源
                keithley.compliance_current = 0.1  # 设置合规电流
                keithley.auto_range_source()
                keithley.measure_current()  # 设置为测量电流
                keithley.enable_source()  # 打开源表
                keithley.source_voltage = voltage_input
                time.sleep(0.1)
            except (AttributeError, ValueError):
                print("keithley未正常连接")

    def Pushing(self):
        if SIM928ConnectionThread.anc is None or not self.lineEdit_SIM928.text():
            logger.log("警告：anc 是 None，无法执行 Pushing 操作")
        else:
            distance = 5000 if is_low() else 1000
            WhileMove(4, self.indicator,MainPage1.equipment, distance)
            logger.log("探针下压了")

    def Pulling(self):
        if SIM928ConnectionThread.anc is None or not self.lineEdit_SIM928.text():
            logger.log("警告：anc 是 None，无法执行 Pulling 操作")
        else:
            # 常温下min的最大值是1000，低温下min的最大值是5000
            distance = 5000 if is_low() else 1000
            WhileMove(5, self.indicator,MainPage1.equipment, distance)
            logger.log("探针抬升了")


def Color_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
    data_r = data_[0:nWidth * nHeight * 3:3]
    data_g = data_[1:nWidth * nHeight * 3:3]
    data_b = data_[2:nWidth * nHeight * 3:3]

    data_r_arr = data_r.reshape(nHeight, nWidth)
    data_g_arr = data_g.reshape(nHeight, nWidth)
    data_b_arr = data_b.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 3], "uint8")

    numArray[:, :, 0] = data_r_arr
    numArray[:, :, 1] = data_g_arr
    numArray[:, :, 2] = data_b_arr
    return numArray
