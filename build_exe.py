#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTneedle 打包脚本
使用 PyInstaller 将项目打包成可执行文件
"""

import os
import sys
import subprocess
import shutil

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*50)
    print(title)
    print("="*50)

def check_pyinstaller():
    """检查并安装 PyInstaller"""
    print_section("1. 检查依赖")
    try:
        import PyInstaller
        print(f"  [OK] PyInstaller 已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("  [X] PyInstaller 未安装")
        print("  正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("  [OK] PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("  [X] 安装失败，请手动安装: pip install pyinstaller")
            return False

def check_psutil():
    """检查并安装 psutil（监控模块需要）"""
    try:
        import psutil
        print(f"  [OK] psutil 已安装")
        return True
    except ImportError:
        print("  正在安装 psutil...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("  [OK] psutil 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("  [X] psutil 安装失败")
            return False

def clean_build():
    """清理旧的构建文件"""
    print_section("2. 清理旧的构建文件")
    
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  [OK] 已删除 {folder} 文件夹")
            except Exception as e:
                print(f"  [X] 删除 {folder} 失败: {e}")
        else:
            print(f"  [SKIP] {folder} 文件夹不存在")

def build_exe():
    """使用 PyInstaller 打包"""
    print_section("3. 开始打包")
    print("  这可能需要几分钟时间，请耐心等待...")
    print()
    
    # 检查 spec 文件是否存在
    spec_file = "QTneedle.spec"
    if not os.path.exists(spec_file):
        print(f"  [X] 错误: 找不到 {spec_file} 文件")
        print("  请确保在项目根目录运行此脚本")
        return False
    
    try:
        # 运行 PyInstaller
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", spec_file, "--clean"],
            check=True,
            capture_output=False  # 显示实时输出
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"  [X] 打包失败: {e}")
        return False
    except FileNotFoundError:
        print("  [X] 找不到 PyInstaller，请确保已正确安装")
        return False

def show_success():
    """显示成功信息"""
    print()
    print_section("[OK] 打包成功！")
    print()
    print("可执行文件位置: .\\dist\\QTneedle\\")
    print("主程序: .\\dist\\QTneedle\\QTneedle低温控制系统.exe")
    print()
    print("使用说明:")
    print("  1. 将整个 dist\\QTneedle 文件夹复制到目标计算机")
    print("  2. 确保目标计算机已安装相机驱动和硬件驱动")
    print("  3. 双击运行 QTneedle低温控制系统.exe")
    print("  4. 日志文件将保存在 logs 文件夹中")
    print()
    
    # 询问是否打开文件夹
    try:
        answer = input("是否打开输出文件夹？(y/n): ").strip().lower()
        if answer == 'y':
            dist_path = os.path.join(os.getcwd(), "dist", "QTneedle")
            if os.path.exists(dist_path):
                if sys.platform == 'win32':
                    os.startfile(dist_path)
                else:
                    subprocess.run(["open", dist_path])
    except:
        pass

def show_failure():
    """显示失败信息"""
    print()
    print_section("[X] 打包失败")
    print()
    print("请检查上方的错误信息")
    print("常见问题:")
    print("  1. 缺少依赖包 - 运行: pip install -r requirements.txt")
    print("  2. 文件路径问题 - 确保在项目根目录运行此脚本")
    print("  3. 权限问题 - 尝试以管理员身份运行")
    print("  4. 磁盘空间不足 - 清理磁盘空间")
    print()

def main():
    """主函数"""
    print("="*50)
    print("QTneedle 打包工具")
    print("="*50)
    
    # 检查依赖
    if not check_pyinstaller():
        return 1
    
    if not check_psutil():
        print("  [WARNING] psutil 未安装，监控功能可能无法使用")
    
    # 清理旧文件
    clean_build()
    
    # 执行打包
    success = build_exe()
    
    # 显示结果
    if success:
        show_success()
        return 0
    else:
        show_failure()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print("\n按 Enter 键退出...")
        input()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n按 Enter 键退出...")
        input()
        sys.exit(1)
