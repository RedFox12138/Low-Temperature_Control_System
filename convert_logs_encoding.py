#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志文件编码转换工具
将旧的 GBK 编码日志文件转换为 UTF-8 编码
"""

import os
import glob
from datetime import datetime

def convert_log_file(file_path):
    """转换单个日志文件的编码"""
    print(f"处理文件: {file_path}")
    
    # 尝试多种编码读取
    content = None
    original_encoding = None
    
    for encoding in ['gbk', 'gb2312', 'utf-8', 'latin1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                original_encoding = encoding
                print(f"  成功用 {encoding} 读取")
                break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"  [失败] 无法读取文件，尝试二进制模式")
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('gbk', errors='ignore')
                original_encoding = 'gbk (强制)'
        except Exception as e:
            print(f"  [错误] {e}")
            return False
    
    # 备份原文件
    backup_path = file_path + '.bak'
    try:
        with open(backup_path, 'wb') as f:
            with open(file_path, 'rb') as original:
                f.write(original.read())
        print(f"  已备份到: {backup_path}")
    except Exception as e:
        print(f"  [警告] 备份失败: {e}")
    
    # 写入 UTF-8 编码
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [成功] 已转换为 UTF-8")
        return True
    except Exception as e:
        print(f"  [错误] 写入失败: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            os.replace(backup_path, file_path)
            print(f"  已从备份恢复")
        return False

def main():
    """主函数"""
    print("="*60)
    print("日志文件编码转换工具")
    print("="*60)
    print()
    
    # 查找所有日志文件
    log_patterns = [
        'logs/operation_log_*.txt',
        'operation_log_*.txt',
        'logs/*.log'
    ]
    
    log_files = []
    for pattern in log_patterns:
        log_files.extend(glob.glob(pattern))
    
    log_files = list(set(log_files))  # 去重
    
    if not log_files:
        print("未找到日志文件")
        return
    
    print(f"找到 {len(log_files)} 个日志文件:\n")
    for f in log_files:
        print(f"  - {f}")
    print()
    
    answer = input("是否继续转换？(y/n): ").strip().lower()
    if answer != 'y':
        print("取消操作")
        return
    
    print()
    print("开始转换...")
    print("-"*60)
    
    success_count = 0
    fail_count = 0
    
    for log_file in log_files:
        if convert_log_file(log_file):
            success_count += 1
        else:
            fail_count += 1
        print()
    
    print("-"*60)
    print(f"\n转换完成:")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {fail_count} 个")
    print(f"\n备份文件保存在原文件目录，文件名后缀 .bak")
    print(f"确认转换无问题后，可以手动删除备份文件")

if __name__ == "__main__":
    try:
        main()
        print("\n按 Enter 键退出...")
        input()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n按 Enter 键退出...")
        input()
