@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY-PORTABLE.ps1"
if errorlevel 1 (
 echo.
 echo The VERIFY-PORTABLE script returned an error. Check the message above.
 pause
 exit /b 1
)
exit /b 0
