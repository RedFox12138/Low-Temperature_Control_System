# QTneedle 打包脚本
# 使用PyInstaller将项目打包成可执行文件

# 设置控制台编码为UTF-8以正确显示中文
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================" -ForegroundColor Cyan
Write-Host "QTneedle 打包工具" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查PyInstaller是否安装
Write-Host "1. 检查依赖..." -ForegroundColor Yellow
$pyinstallerVersion = python -m PyInstaller --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] PyInstaller 已安装: $pyinstallerVersion" -ForegroundColor Green
} else {
    Write-Host "  [X] PyInstaller 未安装" -ForegroundColor Red
    Write-Host "  正在安装 PyInstaller..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [X] 安装失败，请手动安装: pip install pyinstaller" -ForegroundColor Red
        exit 1
    }
}

# 检查psutil（监控模块需要）
python -c "import psutil" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] psutil 已安装" -ForegroundColor Green
} else {
    Write-Host "  正在安装 psutil..." -ForegroundColor Yellow
    python -m pip install psutil
}

Write-Host ""
Write-Host "2. 清理旧的构建文件..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "  [OK] 已删除 build 文件夹" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "  [OK] 已删除 dist 文件夹" -ForegroundColor Green
}

Write-Host ""
Write-Host "3. 开始打包..." -ForegroundColor Yellow
Write-Host "  这可能需要几分钟时间，请耐心等待..." -ForegroundColor Cyan
Write-Host ""

# 使用spec文件打包
python -m PyInstaller QTneedle.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "[OK] 打包成功！" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "可执行文件位置: .\dist\QTneedle\" -ForegroundColor Cyan
    Write-Host "主程序: .\dist\QTneedle\QTneedle低温控制系统.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用说明:" -ForegroundColor Yellow
    Write-Host "  1. 将整个 dist\QTneedle 文件夹复制到目标计算机" -ForegroundColor White
    Write-Host "  2. 确保目标计算机已安装相机驱动和硬件驱动" -ForegroundColor White
    Write-Host "  3. 双击运行 QTneedle低温控制系统.exe" -ForegroundColor White
    Write-Host "  4. 日志文件将保存在 logs 文件夹中" -ForegroundColor White
    Write-Host ""
    
    # 打开dist文件夹
    $openDist = Read-Host "是否打开输出文件夹？(y/n)"
    if ($openDist -eq 'y') {
        $distPath = Join-Path -Path $PSScriptRoot -ChildPath "dist\QTneedle"
        if (Test-Path $distPath) {
            explorer.exe $distPath
        }
    }
} else {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host "[X] 打包失败" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查上方的错误信息" -ForegroundColor Yellow
    Write-Host "常见问题:" -ForegroundColor Yellow
    Write-Host "  1. 缺少依赖包 - 运行: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  2. 文件路径问题 - 确保在项目根目录运行此脚本" -ForegroundColor White
    Write-Host "  3. 权限问题 - 以管理员身份运行PowerShell" -ForegroundColor White
    Write-Host ""
}

Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
