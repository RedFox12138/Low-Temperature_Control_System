"""
分析未使用文件的脚本
运行此脚本前请先备份代码！
"""
import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 疑似未使用的文件（根据文件名判断）
SUSPECTED_FILES = [
    "JiaoBen.py",  # 旧脚本
    "JiaoBen1.py",  # 旧脚本
    "JiaoBen2.py",  # 旧脚本
    "dia0.txt",  # 测试数据
    "dia1.txt",  # 测试数据
    "Paddia.txt",  # 测试数据
    "Test.py",  # 测试文件
    "AutoDialog.py",  # 可能未使用
    "AutoDialog.ui",  # 可能未使用
    "ZauxdSerial.py",  # 可能被SerialPage.py替代
    "threading_location.py",  # 可能未使用
    "I-V test 2450_20250528.py",  # 临时测试脚本
    "Standard I-V test program use Keithley2450.py",  # 独立测试脚本
    "Standard I-V test program use Keithley2450 _WL.py",  # 独立测试脚本
]

# 旧的日志文件
OLD_LOGS = [
    "operation_log_2025-04-09.txt",
    "operation_log_2025-04-11.txt",
    "operation_log_2025-04-16.txt",
]

def collect_all_imports():
    """收集所有Python文件中的导入语句"""
    imports = set()
    
    # 遍历所有py文件
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if py_file.stem in ['analyze_unused_files', 'system_monitor']:
            continue  # 跳过本脚本和新文件
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 查找 import xxx 和 from xxx import 语句
                import_pattern = r'^\s*(?:from\s+(\w+)|import\s+(\w+))'
                matches = re.findall(import_pattern, content, re.MULTILINE)
                
                for match in matches:
                    module = match[0] if match[0] else match[1]
                    imports.add(module)
        except Exception as e:
            print(f"读取 {py_file} 时出错: {e}")
    
    return imports

def analyze():
    """分析未使用的文件"""
    print("="*80)
    print("QTneedle 项目文件使用分析报告")
    print("="*80)
    print()
    
    # 收集导入的模块
    imported_modules = collect_all_imports()
    print(f"✓ 扫描到 {len(imported_modules)} 个被导入的模块")
    print()
    
    # 分析疑似未使用的文件
    print("【疑似未使用的文件】")
    print("-" * 80)
    
    unused_count = 0
    maybe_used_count = 0
    
    for filename in SUSPECTED_FILES:
        file_path = PROJECT_ROOT / filename
        if not file_path.exists():
            print(f"  ⚠ {filename} - 文件不存在")
            continue
        
        # 检查是否被导入
        module_name = Path(filename).stem
        if module_name in imported_modules:
            print(f"  ✓ {filename} - 正在使用（被导入）")
            maybe_used_count += 1
        else:
            print(f"  ✗ {filename} - 未被导入，可能未使用")
            unused_count += 1
    
    print()
    print(f"未被导入的文件数: {unused_count}")
    print(f"可能在使用的文件: {maybe_used_count}")
    print()
    
    # 检查旧日志
    print("【旧日志文件】")
    print("-" * 80)
    log_count = 0
    for log_file in OLD_LOGS:
        file_path = PROJECT_ROOT / log_file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  • {log_file} ({size_kb:.1f} KB) - 建议移到logs文件夹")
            log_count += 1
        else:
            print(f"  • {log_file} - 已不存在")
    
    print(f"\n旧日志文件数: {log_count}")
    print()
    
    # 显示被频繁导入的核心模块
    print("【核心模块列表】（以下模块在使用中，请勿删除）")
    print("-" * 80)
    
    core_modules = [
        'demo', 'run_demo', 'MainPage', 'SerialPage', 'CameraPage', 
        'MicroPage', 'NeedlePage', 'ScriptPage', 'SelectPage',
        'locationClass', 'StopClass', 'Position', 'LTDS', 'Microscope',
        'ANC300', 'SRS_SIM928', 'SRS_SIM970', 'ZauxdllTest',
        'DailyLogger', 'Load_Mat', 'TemperatureConfig', 'SerialLock',
        'full_screen', 'system_monitor', 'shared', 'zauxdllPython'
    ]
    
    for module in sorted(core_modules):
        if module in imported_modules:
            print(f"  ✓ {module}.py")
    
    print()
    print("="*80)
    print("建议操作:")
    print("="*80)
    print("1. 将疑似未使用的文件移到 '_backup' 文件夹")
    print("2. 将旧日志文件移到 'logs' 文件夹")
    print("3. 运行程序测试功能是否正常")
    print("4. 如果一周后没有问题，可以删除备份")
    print()

if __name__ == '__main__':
    analyze()
