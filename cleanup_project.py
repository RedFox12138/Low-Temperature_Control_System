"""
清理脚本 - 将未使用的文件移到备份文件夹
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 创建备份文件夹
BACKUP_DIR = PROJECT_ROOT / "_backup"
BACKUP_DIR.mkdir(exist_ok=True)

# 需要移动的文件
FILES_TO_BACKUP = [
    "JiaoBen.py",
    "JiaoBen1.py",
    "JiaoBen2.py",
    "dia0.txt",
    "dia1.txt",
    "Paddia.txt",
    "Test.py",
    "AutoDialog.py",
    "AutoDialog.ui",
    "ZauxdSerial.py",  # 已被SerialPage.py替代
    "threading_location.py",
    "I-V test 2450_20250528.py",
    "Standard I-V test program use Keithley2450.py",
    "Standard I-V test program use Keithley2450 _WL.py",
]

# 旧日志文件
OLD_LOGS = [
    "operation_log_2025-04-09.txt",
    "operation_log_2025-04-11.txt",
    "operation_log_2025-04-16.txt",
]

def cleanup():
    """执行清理操作"""
    print("="*80)
    print(f"开始清理项目 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # 移动未使用的文件到备份
    print("【1. 移动未使用的文件到 _backup 文件夹】")
    print("-" * 80)
    
    moved_count = 0
    for filename in FILES_TO_BACKUP:
        src = PROJECT_ROOT / filename
        if src.exists():
            dst = BACKUP_DIR / filename
            try:
                shutil.move(str(src), str(dst))
                print(f"  ✓ 已移动: {filename}")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ 移动失败 {filename}: {e}")
        else:
            print(f"  ⚠ 文件不存在: {filename}")
    
    print(f"\n已移动 {moved_count} 个文件到备份文件夹")
    print()
    
    # 移动旧日志到logs文件夹
    print("【2. 移动旧日志文件到 logs 文件夹】")
    print("-" * 80)
    
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_moved = 0
    for log_file in OLD_LOGS:
        src = PROJECT_ROOT / log_file
        if src.exists():
            dst = logs_dir / log_file
            try:
                shutil.move(str(src), str(dst))
                print(f"  ✓ 已移动: {log_file}")
                log_moved += 1
            except Exception as e:
                print(f"  ✗ 移动失败 {log_file}: {e}")
        else:
            print(f"  ⚠ 文件不存在: {log_file}")
    
    print(f"\n已移动 {log_moved} 个日志文件")
    print()
    
    # 创建备份说明文件
    readme_path = BACKUP_DIR / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write("\\n")
        f.write("这些文件在代码分析中未被发现使用。\\n")
        f.write("如果一周后程序运行正常，可以删除此文件夹。\\n")
        f.write("\\n")
        f.write("如需恢复，请将文件移回项目根目录。\\n")
    
    print("="*80)
    print("清理完成！")
    print("="*80)
    print(f"备份文件夹: {BACKUP_DIR}")
    print(f"日志文件夹: {logs_dir}")
    print()
    print("提示:")
    print("  - 请运行程序测试所有功能是否正常")
    print("  - 如有问题，从 _backup 文件夹恢复文件")
    print("  - 如一周后无问题，可删除 _backup 文件夹")
    print()

if __name__ == '__main__':
    response = input("确认要清理项目吗？这将移动未使用的文件到备份文件夹 (y/n): ")
    if response.lower() == 'y':
        cleanup()
    else:
        print("已取消清理操作")
