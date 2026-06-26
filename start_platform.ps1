<# 中医药科学大数据管理平台启动脚本 #>
$ErrorActionPreference = 'SilentlyContinue'

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    中医药科学大数据管理平台 v2.0" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 停止可能正在运行的 Python 进程
Write-Host "清理旧进程..." -ForegroundColor Gray
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# 启动服务器
Write-Host "启动服务..." -ForegroundColor Green
$process = Start-Process python -ArgumentList "server.py" -PassThru -NoNewWindow

# 等待服务启动
Write-Host "等待服务初始化..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 打开浏览器
Write-Host "打开浏览器..." -ForegroundColor Green
Start-Process "http://127.0.0.1:5000"

Write-Host ""
Write-Host "平台已启动！按任意键退出..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 清理
Write-Host "正在停止服务..." -ForegroundColor Gray
$process | Stop-Process -Force