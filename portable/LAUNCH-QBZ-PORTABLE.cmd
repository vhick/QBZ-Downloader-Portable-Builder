@echo off
setlocal EnableExtensions
title QBZ Downloader Portable
set "ROOT=%~dp0"
set "EXE=%ROOT%QBZ-Downloader-Portable.exe"
set "DATA=%ROOT%QBZ-Data"
set "TEMPROOT=%DATA%\Temp"
set "LOGS=%DATA%\LauncherLogs"
if not exist "%DATA%" mkdir "%DATA%" >nul 2>&1
if not exist "%TEMPROOT%" mkdir "%TEMPROOT%" >nul 2>&1
if not exist "%LOGS%" mkdir "%LOGS%" >nul 2>&1
if not exist "%EXE%" (
  echo ERROR: QBZ-Downloader-Portable.exe was not found beside the launcher.
  pause
  exit /b 1
)
set "TEMP=%TEMPROOT%"
set "TMP=%TEMPROOT%"
>>"%LOGS%\Launcher.log" echo %date% %time% Starting QBZ Downloader Portable
start "" "%EXE%"
if errorlevel 1 (
  echo ERROR: Could not start the portable app.
  pause
  exit /b 1
)
exit /b 0
