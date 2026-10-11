@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0MIGRATE-OLD-QBZ-DATA.ps1"
if errorlevel 1 (
 echo.
 echo The MIGRATE-OLD-QBZ-DATA script returned an error. Check the message above.
 pause
 exit /b 1
)
exit /b 0
