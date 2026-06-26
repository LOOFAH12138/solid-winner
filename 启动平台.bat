@echo off
chcp 65001 >nul
title 中医药科学大数据管理平台

echo ================================================
echo      中医药科学大数据管理平台 v2.0
echo ================================================
echo.
echo 正在启动服务...
echo.

start /B python server.py

echo 服务启动中，请稍候...
timeout /t 3 /nobreak >nul

echo 服务已启动，正在打开浏览器...
start http://127.0.0.1:5000

echo.
echo 平台已启动！按 Ctrl+C 停止服务
echo ================================================
pause