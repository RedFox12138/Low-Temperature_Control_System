import threading

class LockSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.serial_lock = threading.Lock()
        return cls._instance

# 创建单例实例
lock_singleton = LockSingleton()