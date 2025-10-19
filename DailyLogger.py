import os
from datetime import datetime


class DailyLogger:
    _instance = None

    def __new__(cls, log_dir='logs'):
        if cls._instance is None:
            cls._instance = super(DailyLogger, cls).__new__(cls)
            cls._instance.log_dir = log_dir
            # 确保日志目录存在
            os.makedirs(log_dir, exist_ok=True)
            # 初始化当前日志文件
            cls._instance._update_log_file()
        return cls._instance

    def _update_log_file(self):
        """更新当前日志文件路径为当天日期"""
        today = datetime.now().strftime('%Y-%m-%d')
        # 仅修改这行，使用您指定的文件名格式
        self.current_log_file = os.path.join(self.log_dir, f"operation_log_{today}.txt")

        # 如果文件不存在，创建并写入文件头
        if not os.path.exists(self.current_log_file):
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Log file created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

    # 以下方法保持不变...
    def _check_date_change(self):
        """检查日期是否变化，如果是则更新日志文件"""
        today = datetime.now().strftime('%Y-%m-%d')
        if not hasattr(self, 'current_date') or today != self.current_date:
            self.current_date = today
            self._update_log_file()

    def log(self, action, level='INFO'):
        """记录日志

        Args:
            action (str): 要记录的操作描述
            level (str): 日志级别(INFO/WARNING/ERROR)
        """
        self._check_date_change()
        try:
            # 尝试用 UTF-8 追加写入
            with open(self.current_log_file, 'a', encoding='utf-8', errors='ignore') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 将特殊字符替换为文本表示，避免编码问题
                action_safe = action.replace('⚠️', '[WARNING]').replace('✓', '[OK]').replace('✗', '[FAIL]')
                f.write(f"[{timestamp}] [{level}] - {action_safe}\n")
                f.flush()  # 立即刷新
        except Exception as e:
            # 如果写入失败，至少打印到控制台
            print(f"日志写入失败: {e}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] - {action}")

    def get_today_logs(self):
        """获取当天日志内容

        Returns:
            str: 当天所有日志内容
        """
        self._check_date_change()
        
        # 尝试多种编码读取（兼容旧文件）
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        
        for encoding in encodings:
            try:
                with open(self.current_log_file, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                return "日志文件不存在"
            except Exception as e:
                continue
        
        # 如果所有编码都失败，使用二进制模式读取
        try:
            with open(self.current_log_file, 'rb') as f:
                content = f.read()
                # 尝试解码，忽略错误
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"读取日志失败: {e}"

    def get_log_file_path(self, date=None):
        """获取指定日期的日志文件路径

        Args:
            date (str): 日期字符串(YYYY-MM-DD)，默认为当天

        Returns:
            str: 日志文件完整路径
        """
        if date is None:
            return self.current_log_file
        return os.path.join(self.log_dir, f"operation_log_{date}.txt")