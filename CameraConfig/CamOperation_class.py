# -- coding: utf-8 --
import sys
import threading
import msvcrt
import numpy as np
import time
import sys, os
import datetime
import inspect
import ctypes
import random
from ctypes import *


from CameraConfig.CameraParams_const import MV_GIGE_DEVICE
from CameraConfig.CameraParams_header import MVCC_INTVALUE_EX, MV_FRAME_OUT_INFO_EX, \
    MV_TRIGGER_MODE_OFF, MV_CC_DEVICE_INFO, MVCC_FLOATVALUE, MV_DISPLAY_FRAME_INFO, MV_SAVE_IMG_TO_FILE_PARAM, \
    MV_Image_Jpeg, MV_Image_Bmp
from CameraConfig.MvCameraControl_class import MvCamera
from CameraConfig.PixelType_header import PixelType_Gvsp_Mono8, PixelType_Gvsp_Mono10, \
    PixelType_Gvsp_Mono12, PixelType_Gvsp_Mono10_Packed, PixelType_Gvsp_Mono12_Packed, PixelType_Gvsp_BayerGR8, \
    PixelType_Gvsp_BayerRG8, PixelType_Gvsp_BayerGB8, PixelType_Gvsp_BayerBG8, PixelType_Gvsp_BayerGR10, \
    PixelType_Gvsp_BayerRG10, PixelType_Gvsp_BayerBG10, PixelType_Gvsp_BayerGB10, PixelType_Gvsp_BayerGR12, \
    PixelType_Gvsp_BayerRG12, PixelType_Gvsp_BayerBG12, PixelType_Gvsp_BayerGB12, PixelType_Gvsp_BayerGR10_Packed, \
    PixelType_Gvsp_BayerRG10_Packed, PixelType_Gvsp_BayerGB10_Packed, PixelType_Gvsp_BayerBG10_Packed, \
    PixelType_Gvsp_BayerRG12_Packed, PixelType_Gvsp_BayerGR12_Packed, PixelType_Gvsp_BayerGB12_Packed, \
    PixelType_Gvsp_YUV422_Packed, PixelType_Gvsp_BayerBG12_Packed, PixelType_Gvsp_YUV422_YUYV_Packed
from MvErrorDefine_const import MV_E_CALLORDER, MV_OK, MV_E_PARAMETER

sys.path.append("../MvImport")



# 强制关闭线程
def Async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


# 停止线程
def Stop_thread(thread):
    Async_raise(thread.ident, SystemExit)


# 转为16进制字符串
def To_hex_str(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


# 是否是Mono图像
def Is_mono_data(enGvspPixelType):
    if PixelType_Gvsp_Mono8 == enGvspPixelType or PixelType_Gvsp_Mono10 == enGvspPixelType \
            or PixelType_Gvsp_Mono10_Packed == enGvspPixelType or PixelType_Gvsp_Mono12 == enGvspPixelType \
            or PixelType_Gvsp_Mono12_Packed == enGvspPixelType:
        return True
    else:
        return False


# 是否是彩色图像
def Is_color_data(enGvspPixelType):
    if PixelType_Gvsp_BayerGR8 == enGvspPixelType or PixelType_Gvsp_BayerRG8 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB8 == enGvspPixelType or PixelType_Gvsp_BayerBG8 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR10 == enGvspPixelType or PixelType_Gvsp_BayerRG10 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB10 == enGvspPixelType or PixelType_Gvsp_BayerBG10 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR12 == enGvspPixelType or PixelType_Gvsp_BayerRG12 == enGvspPixelType \
            or PixelType_Gvsp_BayerGB12 == enGvspPixelType or PixelType_Gvsp_BayerBG12 == enGvspPixelType \
            or PixelType_Gvsp_BayerGR10_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG10_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGB10_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG10_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGR12_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG12_Packed == enGvspPixelType \
            or PixelType_Gvsp_BayerGB12_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG12_Packed == enGvspPixelType \
            or PixelType_Gvsp_YUV422_Packed == enGvspPixelType or PixelType_Gvsp_YUV422_YUYV_Packed == enGvspPixelType:
        return True
    else:
        return False

def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr

# Mono图像转为python数组
def Mono_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    data_mono_arr = data_.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 1], "uint8")
    numArray[:, :, 0] = data_mono_arr
    return numArray


# 彩色图像转为python数组
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


# 相机操作类
class CameraOperation:

    def __init__(self, obj_cam, st_device_list, n_connect_num=0, b_open_device=False, b_start_grabbing=False,
                 h_thread_handle=None,
                 b_thread_closed=False, st_frame_info=None, b_exit=False, b_save_bmp=False, b_save_jpg=False,
                 buf_save_image=None,
                 n_save_image_size=0, n_win_gui_id=0, frame_rate=0, exposure_time=0, gain=0):

        self.obj_cam = obj_cam
        self.st_device_list = st_device_list
        self.n_connect_num = n_connect_num
        self.b_open_device = b_open_device
        self.b_start_grabbing = b_start_grabbing
        self.b_thread_closed = b_thread_closed
        self.st_frame_info = st_frame_info
        self.b_exit = b_exit
        self.b_save_bmp = b_save_bmp
        self.b_save_jpg = b_save_jpg
        self.buf_grab_image = None
        self.buf_grab_image_size = 0
        self.buf_save_image = buf_save_image
        self.n_save_image_size = n_save_image_size
        self.h_thread_handle = h_thread_handle
        # self.b_thread_closed  # removed no-op
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        self.gain = gain
        self.buf_lock = threading.Lock()  # 取图和存图的buffer锁
        # 目标抓取间隔（秒），用于轻微节流，默认约16FPS
        self.target_grab_interval = 0.06
        # 使用事件进行线程安全退出
        self._stop_event = threading.Event()


    # 打开相机
    def Open_device(self):
        if not self.b_open_device:
            if self.n_connect_num < 0:
                return MV_E_CALLORDER

            # ch:选择设备并创建句柄 | en:Select device and create handle
            nConnectionNum = int(self.n_connect_num)
            stDeviceList = cast(self.st_device_list.pDeviceInfo[int(nConnectionNum)],
                                POINTER(MV_CC_DEVICE_INFO)).contents
            self.obj_cam = MvCamera()
            ret = self.obj_cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.obj_cam.MV_CC_DestroyHandle()
                return ret

            ret = self.obj_cam.MV_CC_OpenDevice()
            if ret != 0:
                return ret
            print("open device successfully!")
            self.b_open_device = True
            self.b_thread_closed = False

            # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.obj_cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.obj_cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        print("warning: set packet size fail! ret[0x%x]" % ret)
                else:
                    print("warning: set packet size fail! ret[0x%x]" % nPacketSize)

            # 尝试开启并设置较低的采集帧率，缓解超时
            try:
                # 启用 AcquisitionFrameRateEnable
                ret = self.obj_cam.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", True)
                if ret != 0:
                    print("warning: enable AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
                else:
                    # 将采集帧率设置为 ~15 FPS（可根据需要微调）
                    ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate", 15.0)
                    if ret != 0:
                        print("warning: set AcquisitionFrameRate fail! ret[0x%x]" % ret)
            except Exception as e:
                print(f"warning: set frame rate exception: {e}")

            # ch:设置触发模式为off | en:Set trigger mode as off
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            if ret != 0:
                print("set trigger mode fail! ret[0x%x]" % ret)
            return MV_OK

    # 开始取图
    def Start_grabbing(self, winHandle):
        if not self.b_start_grabbing and self.b_open_device:
            self.b_exit = False
            self._stop_event.clear()
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                return ret
            self.b_start_grabbing = True
            print("start grabbing successfully!")
            try:
                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self, winHandle), daemon=True)
                self.h_thread_handle.start()
                self.b_thread_closed = True
            finally:
                pass
            return MV_OK

        return MV_E_CALLORDER

    # 停止取图（改为协作式停止）
    def Stop_grabbing(self):
        if self.b_start_grabbing and self.b_open_device:
            # 通知线程退出并等待
            if self.b_thread_closed and self.h_thread_handle is not None:
                self._stop_event.set()
                # 等待线程结束，最多2秒，避免阻塞UI
                self.h_thread_handle.join(timeout=2.0)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_StopGrabbing()
            if ret != 0:
                return ret
            print("stop grabbing successfully!")
            self.b_start_grabbing = False
            self.b_exit = True
            return MV_OK
        else:
            return MV_E_CALLORDER

    # 关闭相机
    def Close_device(self):
        if self.b_open_device:
            # 协作式退出线程
            if self.b_thread_closed and self.h_thread_handle is not None:
                self._stop_event.set()
                self.h_thread_handle.join(timeout=2.0)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_CloseDevice()
            if ret != 0:
                return ret

        # ch:销毁句柄 | Destroy handle
        self.obj_cam.MV_CC_DestroyHandle()
        self.b_open_device = False
        self.b_start_grabbing = False
        self.b_exit = True
        print("close device successfully!")

        return MV_OK

    # 设置触发模式
    def Set_trigger_mode(self, is_trigger_mode):
        if not self.b_open_device:
            return MV_E_CALLORDER

        if not is_trigger_mode:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 0)
            if ret != 0:
                return ret
        else:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 1)
            if ret != 0:
                return ret
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerSource", 7)
            if ret != 0:
                return ret

        return MV_OK

    # 软触发一次
    def Trigger_once(self):
        if self.b_open_device:
            return self.obj_cam.MV_CC_SetCommandValue("TriggerSoftware")

    # 获取参数
    def Get_parameter(self):
        if self.b_open_device:
            stFloatParam_FrameRate = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_FrameRate), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_exposureTime = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_exposureTime), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_gain = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_gain), 0, sizeof(MVCC_FLOATVALUE))
            ret = self.obj_cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam_FrameRate)
            if ret != 0:
                return ret
            self.frame_rate = stFloatParam_FrameRate.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam_exposureTime)
            if ret != 0:
                return ret
            self.exposure_time = stFloatParam_exposureTime.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("Gain", stFloatParam_gain)
            if ret != 0:
                return ret
            self.gain = stFloatParam_gain.fCurValue

            return MV_OK

    # 设置参数
    def Set_parameter(self, frameRate, exposureTime, gain):
        if '' == frameRate or '' == exposureTime or '' == gain:
            print('show info', 'please type in the text box !')
            return MV_E_PARAMETER
        if self.b_open_device:
            ret = self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(exposureTime))
            if ret != 0:
                print('show error', 'set exposure time fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("Gain", float(gain))
            if ret != 0:
                print('show error', 'set gain fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate", float(frameRate))
            if ret != 0:
                print('show error', 'set acquistion frame rate fail! ret = ' + To_hex_str(ret))
                return ret

            print('show info', 'set parameter success!')

            return MV_OK

    # 取图线程函数
    def Work_thread(self, winHandle):
        stFrameInfo = MV_FRAME_OUT_INFO_EX()

        stPayloadSize = MVCC_INTVALUE_EX()
        ret_temp = self.obj_cam.MV_CC_GetIntValueEx("PayloadSize", stPayloadSize)
        if ret_temp != MV_OK:
            print(f"获取PayloadSize失败: {To_hex_str(ret_temp)}")
            return
        NeedBufSize = int(stPayloadSize.nCurValue)

        consecutive_errors = 0
        max_consecutive_errors = 5  # 连续5次错误后退出线程，由上层决定是否重连

        # 预分配抓取缓冲区
        if self.buf_grab_image is None or self.buf_grab_image_size < NeedBufSize:
            try:
                self.buf_grab_image = (c_ubyte * NeedBufSize)()
                self.buf_grab_image_size = NeedBufSize
            except MemoryError:
                print("内存不足，无法分配图像缓冲区")
                return

        while not self.b_exit and not self._stop_event.is_set():
            ret = self.obj_cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, stFrameInfo, 2000)

            if ret == MV_OK:
                consecutive_errors = 0
                # 将当前帧复制到保存缓冲区（线程安全）
                with self.buf_lock:
                    try:
                        if self.buf_save_image is None or self.n_save_image_size < stFrameInfo.nFrameLen:
                            self.buf_save_image = (c_ubyte * stFrameInfo.nFrameLen)()
                            self.n_save_image_size = stFrameInfo.nFrameLen
                        # 保存帧信息的浅拷贝到新的结构体，避免复用导致的数据被覆盖
                        st_copy = MV_FRAME_OUT_INFO_EX()
                        ctypes.memmove(ctypes.byref(st_copy), ctypes.byref(stFrameInfo), ctypes.sizeof(MV_FRAME_OUT_INFO_EX))
                        self.st_frame_info = st_copy
                        # 复制图像数据
                        ctypes.memmove(self.buf_save_image, self.buf_grab_image, stFrameInfo.nFrameLen)
                    except MemoryError:
                        print("内存不足，复制图像失败")
                        # 降低帧率或短暂休眠以缓解
                        time.sleep(0.05)
                        continue
            else:
                consecutive_errors += 1
                error_code = To_hex_str(ret)
                print(f"获取帧失败, ret = {error_code}, 连续错误次数: {consecutive_errors}")
                if consecutive_errors >= max_consecutive_errors:
                    print("连续错误过多，抓图线程退出")
                    break

        # 线程即将退出
        self._stop_event.set()
        # 不在此处做任何句柄关闭，交由上层Stop_grabbing/Close_device处理

    # 存jpg图像
    def Save_jpg(self):

        if self.buf_save_image is None:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".jpg"

        stSaveParam = MV_SAVE_IMG_TO_FILE_PARAM()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Jpeg  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 80
        stSaveParam.pImagePath = file_path.encode('ascii')
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFile(stSaveParam)

        self.buf_lock.release()
        return ret

    # 存BMP图像
    def Save_Bmp(self):

        if 0 == self.buf_save_image:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".bmp"

        stSaveParam = MV_SAVE_IMG_TO_FILE_PARAM()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Bmp  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 8
        stSaveParam.pImagePath = file_path.encode('ascii')
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFile(stSaveParam)

        self.buf_lock.release()

        return ret
