@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$l=Join-Path ([Environment]::GetFolderPath('Startup')) 'QBZ-Downloader-Portable.lnk'; if(Test-Path -LiteralPath $l){Remove-Item -LiteralPath $l -Force;Write-Host ('Removed: '+$l)}else{Write-Host 'Shortcut not found (already removed).'}"
pause
