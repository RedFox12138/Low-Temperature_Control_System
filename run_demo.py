import sys
import traceback

from locationClass import locationClass
from StopClass import StopClass

# 定义你要添加的库文件路径
custom_lib_path = "c:\\users\\administrator\\appdata\\local\\programs\\python\\python37\\lib\\site-packages"

# 将路径添加到 sys.path
if custom_lib_path not in sys.path:
    sys.path.append(custom_lib_path)
import ctypes

from datetime import datetime

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow

from CameraPage import CameraPage
from MainPage import MainPage1
from MicroPage import MicroPage
from NeedlePage import NeedlePage
from ScriptPage import ScriptPage
from SerialPage import SerialPage
from demo import Ui_MainWindow
from full_screen import show_custom_fullscreen

# 监控相关：启用faulthandler与tracemalloc，并在退出时输出报告
import atexit
import faulthandler
import tracemalloc
import os

# 导入增强的系统监控模块
from system_monitor import get_monitor, monitor_thread, safe_thread_start

# 将crash堆栈输出到文件，辅助定位原生崩溃（如0xC0000374）
_crash_log_file = open("logs/faulthandler.log", "w", buffering=1, encoding="utf-8")
faulthandler.enable(file=_crash_log_file, all_threads=True)

# 通过环境变量控制是否启用内存跟踪，避免常态运行的性能影响
_ENABLE_DIAG = os.getenv("ENABLE_DIAG", "0") == "1"
if _ENABLE_DIAG:
    # 启动内存跟踪，记录更多栈深以便定位来源
    tracemalloc.start(15)


def _print_memory_report():
    if not _ENABLE_DIAG:
        return
    try:
        snap = tracemalloc.take_snapshot()
        top = snap.statistics('lineno')
        with open("memory_report.txt", "w", encoding="utf-8") as f:
            f.write("--- Top 20 memory usage by line ---\n")
            for stat in top[:20]:
                f.write(str(stat) + "\n")
            f.write("-----------------------------------\n")
    except Exception:
        # 避免在退出阶段抛出异常
        pass

atexit.register(_print_memory_report)

log_file = f"operation_log_{datetime.now().strftime('%Y-%m-%d')}.txt"


class UsingTest(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(UsingTest, self).__init__(*args, **kwargs)

        self.setupUi(self)  # 初始化ui
        show_custom_fullscreen(self)  # 自定义全屏模式，运行时直接进入全屏模式


        self.stopclass = StopClass(self.Button_needle1Stop)
        self.mainpage1 = MainPage1(self.label_video, self.label_cameraLabel, self.Button_screenshot, self.lineEdit_savePath, self.Button_browse, self.Button_needleTemplate,
                                   self.Button_padTemplate,self.Button_iuCalculate, self.plainTextEdit_log,log_file,self.Checkbox_templateDevice,self.Checkbox_microAutoTrace,self.Checkbox_ElecNeedle,self.Checkbox_Light,
                                   self.Button_Micro_up, self.Button_Micro_down, self.Button_Micro_left,self.Button_Micro_right,
                                   self.Button_needle1Up, self.Button_needle1Down, self.Button_needle1Left, self.Button_needle1Right,
                                   self.lineEdit_needle1Xdistance,self.lineEdit_needle1Ydistance, self.lineEdit_needle1Zdistance,
                                   self.Button_needle1SetXdisConfirm,self.Button_needle1SetYdisConfirm, self.Button_needle1SetZdisConfirm, self.label_light,
                                   self.lineEdit_SIM928, self.Button_SIM928,
                                   self.Button_pushing, self.Button_pulling, self.Button_relay,
                                   self.label_needle1,self.lineEdit_SaveResult,
                                   self.lineEdit_needleSetXdis, self.lineEdit_needleSetYdis, self.lineEdit_needleSetZdis,
                                   self.lineEdit_microSetXdis, self.lineEdit_microSetYdis,self.lineEdit_Scripts,self.plot_Label,self.Checkbox_lowTemp,self.Checkbox_highTemp,
                                   self.xReverseButton,self.yReverseButton)
        self.mainpage2 = SerialPage(self.comboBox_micro, self.label_microConnect, self.Button_microConnect,
                                    self.Button_microDisConnect,
                                    self.comboBox_needle, self.label_needleConnect, self.Button_needleConnect,
                                    self.Button_needleDisConnect,
                                    self.lineEdit_Keithley, self.label_SIM928Connect,
                                    self.Button_SIM928Connect, self.Button_SIM928DisConnect,
                                    self.comboBox_SIM970_port1, self.comboBox_SIM970_port2, self.label_SIM970Connect,
                                    self.Button_SIM970Connect, self.Button_SIM970DisConnect,
                                    self.GBIO_connect_button,
                                    self.comboBox_relay, self.label_relayConnect, self.Button_relayConnect,
                                    self.Button_relayDisConnect,self.Serial_connect_refresh)

        self.mainpage3 = CameraPage(self.lineEdit_cameraBao, self.lineEdit_cameraGain, self.lineEdit_cameraRate, self.Button_cameraConfirm)
        self.mainpage4 = MicroPage(self.lineEdit_microSetXdis, self.lineEdit_microSetYdis, self.pushButton_MicroConfirm)
        self.mainpage5 = NeedlePage(self.lineEdit_needleSetXdis, self.lineEdit_needleSetYdis, self.lineEdit_needleSetZdis,
                                    self.lineEdit_needleSetXvol, self.lineEdit_needleSetYvol, self.lineEdit_needleSetZvol,
                                    self.lineEdit_needleSetXfreq, self.lineEdit_needleSetYfreq, self.lineEdit_needleSetZfreq, self.Button_needleSetConfirm)
        self.mainpage6 = ScriptPage(self.lineEdit_Scripts, self.Button_ScriptsBrowse, self.textEdit_Scripts, self.Button_scriptConfirm,
                                    self.lineEdit_SaveResult,self.Button_SaveResultBrowse,self.Button_scriptUpdate)
        self.locationClass = locationClass( self.lineEdit_Xlocation,self.lineEdit_Ylocation,self.lineEdit_Zlocation,
                                   self.lineEdit_Location1,self.lineEdit_Location2,self.lineEdit_Location3,
                                   self.Button_Location1,self.Button_Location2,self.Button_Location3,
                                   self.lineEdit_row,self.lineEdit_col,self.Button_CreateMap,self.mainpage1,
                                   self.Button_ContinueTest,self.Button_StopTest,
                                   self.lineEdit_Pushlocation,self.lineEdit_Pulllocation,
                                   self.Button_PushLocation,self.Button_PullLocation,
                                   self.Button_PushBack,self.Button_PullBack,
                                   self.lineEdit_leftTopX,self.lineEdit_leftTopY,self.lineEdit_rightTopX,self.lineEdit_rightTopY,self.lineEdit_rightBottomX,self.lineEdit_rightBottomY,
                                   self.Checkbox_DontTest,self.widget_map,self.tabWidget,self.label_light,
                                            self.lineEdit_leftTopName,self.lineEdit_rightTopName,self.lineEdit_rightBottomName)

        # 周期性输出内存快照（轻量），辅助观察是否持续增长（仅在诊断模式下启用）
        from PyQt5.QtCore import QTimer
        if _ENABLE_DIAG:
            self._mem_timer = QTimer(self)
            self._mem_timer.timeout.connect(self._dump_mem_tick)
            self._mem_timer.start(30000)  # 每30秒记录一次

    def _dump_mem_tick(self):
        if not _ENABLE_DIAG:
            return
        try:
            snap = tracemalloc.take_snapshot()
            top = snap.statistics('lineno')
            with open("memory_stats.txt", "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] Top 5 allocations:\n")
                for stat in top[:5]:
                    f.write(str(stat) + "\n")
        except Exception:
            pass

    def closeEvent(self, event):
        # 确保退出前释放相机资源
        try:
            if hasattr(self, 'mainpage1') and self.mainpage1 and getattr(MainPage1, 'obj_cam_operation', None):
                try:
                    MainPage1.obj_cam_operation.Stop_grabbing()
                except Exception:
                    pass
                try:
                    MainPage1.obj_cam_operation.Close_device()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            _crash_log_file.flush()
        except Exception:
            pass
        super().closeEvent(event)

# 程序入口文件
if __name__ == '__main__':
    # ========== 启动系统监控 ==========
    monitor = get_monitor()
    monitor.start_monitoring(interval=5)  # 每5秒记录一次系统状态
    monitor.logger.info("程序启动")
    # ===================================
    
    app = QApplication(sys.argv)  # 创建窗口程序
    app.setWindowIcon(QIcon('kupai.png'))  # 设置应用程序图标

    # 设置任务栏图标（Windows 特定）
    myappid = 'mycompany.myproduct.subproduct.version'  # 任意唯一字符串
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    win = UsingTest()

    # 进程退出前的兜底清理
    def _cleanup():
        try:
            if getattr(MainPage1, 'obj_cam_operation', None):
                try:
                    MainPage1.obj_cam_operation.Stop_grabbing()
                except Exception:
                    pass
                try:
                    MainPage1.obj_cam_operation.Close_device()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            _crash_log_file.flush()
        except Exception:
            pass

    atexit.register(_cleanup)

    win.show()
    
    try:
        exit_code = app.exec()
        monitor.logger.info(f"程序正常退出，退出码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        monitor.logger.critical(f"程序异常退出: {e}")
        monitor.logger.critical(traceback.format_exc())
        sys.exit(-1)
    finally:
        monitor.stop_monitoring()
