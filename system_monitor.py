"""
系统监控模块 - 用于追踪内存泄漏、线程问题和崩溃原因
专门针对0xC0000374(堆损坏)错误的监控
"""
import psutil
import threading
import traceback
import sys
import gc
from datetime import datetime
from pathlib import Path
import logging
from functools import wraps
from PyQt5.QtCore import QThread

class SystemMonitor:
    """系统监控类，用于追踪内存泄漏和线程问题"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger("SystemMonitor")
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 文件处理器 - 详细日志
        log_file = self.log_dir / f"crash_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # 控制台处理器 - 只显示警告
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.process = psutil.Process()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 记录线程创建历史
        self.thread_history = []
        self.max_memory_usage = 0
        
        self.logger.info("="*80)
        self.logger.info("系统监控初始化完成")
        self.logger.info(f"进程ID: {self.process.pid}")
        self.logger.info(f"Python版本: {sys.version}")
        self.logger.info("="*80)
        
    def start_monitoring(self, interval=5):
        """启动内存和线程监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,), 
            daemon=True,
            name="SystemMonitor"
        )
        self.monitor_thread.start()
        self.logger.info(f"系统监控已启动 (监控间隔: {interval}秒)")
        
    def _monitor_loop(self, interval):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 获取内存信息
                mem_info = self.process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024
                mem_percent = self.process.memory_percent()
                
                # 更新最大内存使用
                if mem_mb > self.max_memory_usage:
                    self.max_memory_usage = mem_mb
                
                # 获取线程信息
                thread_count = threading.active_count()
                threads = threading.enumerate()
                thread_names = [f"{t.name}({t.ident})" for t in threads]
                
                # 获取QThread信息
                qthread_count = sum(1 for t in threads if isinstance(t, QThread))
                
                # 记录基本信息
                self.logger.info(f"内存: {mem_mb:.2f}MB ({mem_percent:.2f}%) | 峰值: {self.max_memory_usage:.2f}MB")
                self.logger.info(f"线程: 总数={thread_count}, QThread={qthread_count}")
                self.logger.debug(f"活动线程列表: {thread_names}")
                
                # 检查异常情况
                if mem_percent > 70:
                    self.logger.warning(f"⚠️ 内存使用率过高: {mem_percent:.2f}%")
                    self.logger.warning(f"当前活动线程: {thread_names}")
                    # 强制垃圾回收
                    collected = gc.collect()
                    self.logger.warning(f"执行垃圾回收，清理了 {collected} 个对象")
                
                if thread_count > 30:
                    self.logger.warning(f"⚠️ 线程数异常: {thread_count}")
                    self.logger.warning(f"线程详情: {thread_names}")
                
                # 检查线程是否有死锁
                self._check_deadlock()
                    
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}\n{traceback.format_exc()}")
                
            threading.Event().wait(interval)
    
    def _check_deadlock(self):
        """检查可能的死锁"""
        try:
            # 获取所有线程的锁信息（简化版）
            import sys
            if hasattr(sys, '_current_frames'):
                frames = sys._current_frames()
                waiting_threads = []
                for thread_id, frame in frames.items():
                    # 检查是否在等待锁
                    if 'acquire' in str(frame.f_code.co_name):
                        waiting_threads.append(thread_id)
                
                if len(waiting_threads) > 3:
                    self.logger.warning(f"⚠️ 检测到多个线程({len(waiting_threads)})可能在等待锁")
        except:
            pass
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("="*80)
        self.logger.info("系统监控已停止")
        self.logger.info(f"峰值内存使用: {self.max_memory_usage:.2f}MB")
        self.logger.info("="*80)
    
    def log_thread_lifecycle(self, action, thread_name, extra_info=""):
        """记录线程生命周期"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_msg = f"[{timestamp}] 线程事件: {action} - {thread_name} {extra_info}"
        self.logger.info(log_msg)
        self.thread_history.append({
            'timestamp': timestamp,
            'action': action,
            'thread': thread_name,
            'info': extra_info
        })
    
    def log_exception(self, exc_type, exc_value, exc_traceback):
        """记录未捕获的异常信息"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        self.logger.critical("="*80)
        self.logger.critical("❌ 程序崩溃！检测到未捕获的异常")
        self.logger.critical("="*80)
        self.logger.critical("异常信息:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 记录崩溃时的系统状态
        try:
            mem_info = self.process.memory_info()
            thread_count = threading.active_count()
            threads = threading.enumerate()
            thread_details = [f"{t.name}(ID:{t.ident}, Alive:{t.is_alive()})" for t in threads]
            
            self.logger.critical(f"崩溃时内存使用: {mem_info.rss / 1024 / 1024:.2f}MB")
            self.logger.critical(f"崩溃时线程数: {thread_count}")
            self.logger.critical(f"崩溃时活动线程: {thread_details}")
            
            # 记录最近的线程活动
            self.logger.critical("最近10个线程事件:")
            for event in self.thread_history[-10:]:
                self.logger.critical(f"  {event}")
            
            # 尝试识别可能的问题线程
            qthreads = [t for t in threads if isinstance(t, QThread)]
            if qthreads:
                self.logger.critical(f"活动QThread数量: {len(qthreads)}")
                for qt in qthreads:
                    self.logger.critical(f"  QThread: {qt.objectName()} - Running: {qt.isRunning()}")
                    
        except Exception as e:
            self.logger.critical(f"获取崩溃信息时出错: {e}")
        
        self.logger.critical("="*80)

# 全局监控实例
_monitor = None

def get_monitor():
    """获取全局监控实例"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
        # 设置全局异常处理
        sys.excepthook = _monitor.log_exception
    return _monitor

def monitor_thread(func):
    """装饰器：监控线程函数的执行"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = get_monitor()
        thread_name = threading.current_thread().name
        monitor.log_thread_lifecycle("START", thread_name, f"执行 {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            monitor.log_thread_lifecycle("COMPLETE", thread_name, f"{func.__name__} 成功完成")
            return result
        except Exception as e:
            monitor.logger.error(f"❌ 线程 {thread_name} 在 {func.__name__} 中发生错误")
            monitor.logger.error(f"错误类型: {type(e).__name__}")
            monitor.logger.error(f"错误信息: {str(e)}")
            monitor.logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")
            monitor.log_thread_lifecycle("ERROR", thread_name, f"{func.__name__} 发生错误: {e}")
            raise
        finally:
            monitor.log_thread_lifecycle("END", thread_name, f"{func.__name__} 结束")
            
    return wrapper

def monitor_method(func):
    """装饰器：监控类方法的执行"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        monitor = get_monitor()
        class_name = self.__class__.__name__
        method_name = func.__name__
        
        # 只记录重要方法，避免日志过多
        important_methods = ['run', 'start', 'stop', 'connect', 'disconnect', 
                            'Start_grabbing', 'Stop_grabbing', 'Open_device', 'Close_device']
        
        if method_name in important_methods:
            monitor.logger.debug(f"📍 {class_name}.{method_name} 被调用")
        
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            monitor.logger.error(f"❌ {class_name}.{method_name} 发生错误: {e}")
            monitor.logger.error(traceback.format_exc())
            raise
            
    return wrapper

def safe_thread_start(thread_obj, thread_name=None):
    """安全启动线程，带监控"""
    monitor = get_monitor()
    if thread_name:
        thread_obj.setObjectName(thread_name)
    
    actual_name = thread_name or thread_obj.objectName() or str(thread_obj)
    monitor.log_thread_lifecycle("CREATE", actual_name, f"线程类型: {type(thread_obj).__name__}")
    
    # 包装原始run方法
    original_run = thread_obj.run
    
    @monitor_thread
    def monitored_run():
        return original_run()
    
    thread_obj.run = monitored_run
    thread_obj.start()
    
    return thread_obj

# 用于在脚本退出时自动停止监控
import atexit

def _cleanup_monitor():
    global _monitor
    if _monitor:
        _monitor.stop_monitoring()

atexit.register(_cleanup_monitor)
