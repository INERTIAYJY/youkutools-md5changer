@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0\.."

echo ================================================
echo   视频 MD5 重构工具V2 - 打包
echo ================================================

if not exist "ffmpeg_bin\ffmpeg.exe" (
  echo [错误] 缺少 ffmpeg_bin\ffmpeg.exe
  exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python -m pip install pyinstaller
if errorlevel 1 exit /b 1

python -m PyInstaller build\app.spec --clean --noconfirm
if errorlevel 1 exit /b 1

echo 打包完成: dist\视频MD5重构工具.exe
exit /b 0
