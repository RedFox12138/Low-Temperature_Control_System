"""
PyInstaller spec文件 - QTneedle低温控制系统
用于生成Windows可执行文件
"""

# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 需要包含的数据文件
datas = [
    ('demo.ui', '.'),
    ('*.png', '.'),
    ('Icon', 'Icon'),
    ('CameraConfig', 'CameraConfig'),
]

# 动态添加存在的文件
optional_files = [
    'source.qrc',
    'templateNeedle.png',
    'templatepad.png', 
    'templateLight.png',
    'kupai.png',
    'zauxdll.dll',
    'zmotion.dll',
]

for file in optional_files:
    if os.path.exists(file):
        datas.append((file, '.'))

# 需要包含的隐藏导入
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.uic',
    'numpy',
    'numpy.core',
    'cv2',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'pyvisa',
    'pyvisa_py',
    'pymeasure',
    'pymeasure.instruments',
    'pymeasure.instruments.keithley',
    'pymeasure.instruments.keithley.keithley2450',
    'scipy',
    'scipy.io',
    'scipy.optimize',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'psutil',
    'ctypes',
    'threading',
    'multiprocessing',
    'queue',
    'logging',
    'faulthandler',
    'tracemalloc',
    # 自定义模块
    'DailyLogger',
    'system_monitor',
    'SerialPage',
    'SerialLock',
    'MainPage',
    'CameraPage',
    'MicroPage',
    'NeedlePage',
    'ScriptPage',
    'SelectPage',
    'AutoDialog',
    'locationClass',
    'Position',
    'StopClass',
    'shared',
    'TemperatureConfig',
]

# 排除的模块（减小文件大小）
excludes = [
    'tkinter',
    'jupyter',
    'notebook',
    'IPython',
    'pytest',
    'unittest',
    'test',
    'distutils',
]

a = Analysis(
    ['run_demo.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QTneedle低温控制系统',
    debug=True,  # 启用调试模式
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩，避免兼容性问题
    console=True,  # 保留控制台窗口以查看错误信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # 禁用UPX压缩
    upx_exclude=[],
    name='QTneedle',
)
