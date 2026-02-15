@echo off
chcp 65001 > nul

echo 正在执行格式修正与Word文档转换脚本...
python convert.py

echo.
echo === 所有任务已执行完毕 ===
echo.
pause
