$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$dest = Join-Path $root 'QBZ-Data\Verification'
New-Item -Path $dest -ItemType Directory -Force | Out-Null
$report = Join-Path $dest ("Verify-{0}.txt" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$lines = New-Object 'System.Collections.Generic.List[string]'
$lines.Add('QBZ DOWNLOADER PORTABLE VERIFICATION (no settings content is read)')
$lines.Add("Generated: $(Get-Date)")
$lines.Add("Root: $root")
foreach($relative in @(
  'QBZ-Downloader-Portable.exe',
  'PORTABLE-SOURCE-PATCH.json',
  'QBZ-Data\data\qbz.db',
  'QBZ-Data\data\.secret.key',
  'QBZ-Data\Electron\UserData',
  'QBZ-Data\Electron\SessionData',
  'QBZ-Data\Logs',
  'QBZ-Data\Temp',
  'QBZ-Data\downloads'
)) {
  $p = Join-Path $root $relative
  $lines.Add("$relative : $(Test-Path -LiteralPath $p)")
}
$lines.Add('')
$lines.Add('POSSIBLE OLD APPDATA FOLDERS (presence does not prove new writes):')
foreach($p in @(
  (Join-Path $env:APPDATA 'QBZ Downloader'),
  (Join-Path $env:LOCALAPPDATA 'QBZ Downloader'),
  (Join-Path $env:APPDATA 'qbz-downloader'),
  (Join-Path $env:LOCALAPPDATA 'qbz-downloader')
)) { $lines.Add("$p : $(Test-Path -LiteralPath $p)") }
$lines.Add('')
$lines.Add('SQLite DB, WAL/SHM and .secret.key must stay together. Older safe: credentials may require re-login.')
$lines.Add('Electron-builder extraction can still use Windows TEMP before the app starts.')
$lines | Set-Content -LiteralPath $report -Encoding UTF8
Write-Host "Report saved: $report" -ForegroundColor Green
Write-Host 'This report does NOT include passwords or settings file contents.'
Read-Host 'Press Enter to close' | Out-Null
