#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTneedle 可执行文件调试启动器
用于诊断 EXE 闪退问题
"""

import sys
import os
import traceback
from datetime import datetime

# 创建日志文件
log_file = f"exe_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_message(msg):
    """记录日志到文件和控制台"""
    print(msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

try:
    log_message("="*60)
    log_message("QTneedle 可执行文件调试启动")
    log_message("="*60)
    log_message(f"启动时间: {datetime.now()}")
    log_message(f"Python版本: {sys.version}")
    log_message(f"当前目录: {os.getcwd()}")
    log_message(f"可执行文件: {sys.executable}")
    log_message("")
    
    # 检查关键文件
    log_message("检查关键文件:")
    critical_files = [
        'demo.ui',
        'templateNeedle.png',
        'templatepad.png',
        'templateLight.png',
        'kupai.png',
    ]
    
    for file in critical_files:
        exists = os.path.exists(file)
        status = "[OK]" if exists else "[MISSING]"
        log_message(f"  {status} {file}")
    
    log_message("")
    
    # 检查关键模块
    log_message("检查关键模块:")
    modules_to_check = [
        'PyQt5',
        'numpy',
        'cv2',
        'serial',
        'pyvisa',
        'pymeasure',
        'scipy',
        'matplotlib',
        'psutil',
    ]
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            log_message(f"  [OK] {module_name}")
        except ImportError as e:
            log_message(f"  [MISSING] {module_name}: {e}")
    
    log_message("")
    log_message("尝试启动主程序...")
    log_message("")
    
    # 导入并运行主程序
    import run_demo
    
except Exception as e:
    log_message("")
    log_message("="*60)
    log_message("发生错误!")
    log_message("="*60)
    log_message(f"错误类型: {type(e).__name__}")
    log_message(f"错误信息: {str(e)}")
    log_message("")
    log_message("完整堆栈跟踪:")
    log_message(traceback.format_exc())
    log_message("")
    log_message(f"日志已保存到: {log_file}")
    log_message("")
    input("按 Enter 键退出...")
    sys.exit(1)
