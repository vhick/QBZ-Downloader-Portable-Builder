param(
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$KitRoot,
  [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'
$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$KitRoot = [IO.Path]::GetFullPath($KitRoot)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)

$marker = Join-Path $SourceRoot '.qbz-portable-patch.json'
if (!(Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Missing portable patch marker; refusing to package.' }

$release = Join-Path $SourceRoot 'release'
if (!(Test-Path -LiteralPath $release -PathType Container)) { throw 'Expected electron-builder release/ folder is missing.' }

$candidates = @(Get-ChildItem -LiteralPath $release -Recurse -File -Filter '*.exe' |
  Where-Object { $_.Name -match 'Portable' -and $_.FullName -notmatch '(?i)unpacked|setup' } |
  Sort-Object LastWriteTime -Descending)
if ($candidates.Count -ne 1) {
  $paths = ($candidates | ForEach-Object { $_.FullName }) -join "`n"
  throw "Expected exactly ONE portable EXE under release/. Found $($candidates.Count).`n$paths"
}
if (Test-Path -LiteralPath $OutputRoot) { Remove-Item -LiteralPath $OutputRoot -Force -Recurse }
New-Item -Path $OutputRoot -ItemType Directory -Force | Out-Null
New-Item -Path (Join-Path $OutputRoot 'QBZ-Data') -ItemType Directory -Force | Out-Null
Copy-Item -LiteralPath $candidates[0].FullName -Destination (Join-Path $OutputRoot 'QBZ-Downloader-Portable.exe')
Copy-Item -LiteralPath $marker -Destination (Join-Path $OutputRoot 'PORTABLE-SOURCE-PATCH.json')
foreach ($f in @(
  'LAUNCH-QBZ-PORTABLE.cmd',
  'MIGRATE-OLD-QBZ-DATA.ps1',
  'MIGRATE-OLD-QBZ-DATA.cmd',
  'VERIFY-PORTABLE.ps1',
  'VERIFY-PORTABLE.cmd',
  'INSTALL-PORTABLE-STARTUP.cmd',
  'REMOVE-PORTABLE-STARTUP.cmd'
)) {
  Copy-Item -LiteralPath (Join-Path $KitRoot "portable\$f") -Destination (Join-Path $OutputRoot $f) -Force
}
if (Test-Path -LiteralPath (Join-Path $SourceRoot 'LICENSE')) {
  Copy-Item -LiteralPath (Join-Path $SourceRoot 'LICENSE') -Destination (Join-Path $OutputRoot 'LICENSE-UPSTREAM.txt')
}
$commit = (git -C $SourceRoot rev-parse HEAD).Trim()
Set-Content -LiteralPath (Join-Path $OutputRoot 'SOURCE-REVISION.txt') -Value $commit -Encoding UTF8
Write-Host "Portable build assembled: $OutputRoot" -ForegroundColor Green
Write-Host "Portable application: $($candidates[0].Name)" -ForegroundColor Green
