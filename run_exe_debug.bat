@echo off
chcp 65001 >nul
echo ========================================
echo QTneedle 可执行文件诊断工具
echo ========================================
echo.

cd /d "%~dp0"

if not exist "dist\QTneedle\QTneedle低温控制系统.exe" (
    echo [错误] 找不到可执行文件！
    echo 请先运行 build_exe.py 进行打包
    pause
    exit /b 1
)

echo [1/3] 检查可执行文件目录...
cd dist\QTneedle
echo 当前目录: %CD%
echo.

echo [2/3] 检查关键文件...
for %%F in (demo.ui templateNeedle.png templatepad.png templateLight.png) do (
    if exist "%%F" (
        echo   [OK] %%F
    ) else (
        echo   [MISSING] %%F
    )
)
echo.

echo [3/3] 启动程序（控制台模式）...
echo 如果程序闪退，请查看下面的错误信息：
echo ----------------------------------------
echo.

"QTneedle低温控制系统.exe"

echo.
echo ----------------------------------------
echo 程序已退出
echo.
pause
