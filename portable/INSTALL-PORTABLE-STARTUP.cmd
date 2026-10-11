@echo off
setlocal EnableExtensions
title QBZ Downloader Portable startup (optional)
set "ROOT=%~dp0"
set "LAUNCHER=%ROOT%LAUNCH-QBZ-PORTABLE.cmd"
set "VBS=%ROOT%QBZ-Data\Start-QBZ-Hidden.vbs"
if not exist "%ROOT%QBZ-Data" mkdir "%ROOT%QBZ-Data" >nul 2>&1
> "%VBS%" echo Set sh = CreateObject("WScript.Shell")
>>"%VBS%" echo sh.Run Chr(34) ^& "%LAUNCHER%" ^& Chr(34), 0, False
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$l=Join-Path ([Environment]::GetFolderPath('Startup')) 'QBZ-Downloader-Portable.lnk';" ^
  "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($l);" ^
  "$s.TargetPath=$env:WINDIR+'\System32\wscript.exe';" ^
  "$s.Arguments='""%VBS%""'; $s.WorkingDirectory='%ROOT%'; $s.Save(); Write-Host ('Created: '+$l)"
echo.
echo Optional portable startup shortcut added. To remove, use REMOVE-PORTABLE-STARTUP.cmd.
pause
