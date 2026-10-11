param(
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'
$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)

$standaloneMarker = Join-Path $SourceRoot '.qbz-portable-patch.json'
$pafMarker = Join-Path $SourceRoot '.qbz-paf-patch.json'
foreach ($marker in @($standaloneMarker, $pafMarker)) {
  if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
    throw "Missing verified patch marker: $marker"
  }
}

$release = Join-Path $SourceRoot 'release'
if (-not (Test-Path -LiteralPath $release -PathType Container)) {
  throw 'Electron Builder release/ folder not found.'
}
$candidates = @(
  Get-ChildItem -LiteralPath $release -Filter 'QBZ-Downloader-Portable-*.exe' -File |
    Sort-Object LastWriteTime -Descending
)
if ($candidates.Count -ne 1) {
  throw "Expected exactly one QBZ portable EXE in release/. Found $($candidates.Count)."
}

if (Test-Path -LiteralPath $OutputRoot) {
  Remove-Item -LiteralPath $OutputRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

Copy-Item -LiteralPath $candidates[0].FullName `
  -Destination (Join-Path $OutputRoot 'QBZ-Downloader-Portable.exe') -Force
Copy-Item -LiteralPath $pafMarker `
  -Destination (Join-Path $OutputRoot 'PAF-SOURCE-PATCH.json') -Force

$commit = (git -C $SourceRoot rev-parse HEAD).Trim()
Set-Content -LiteralPath (Join-Path $OutputRoot 'SOURCE-REVISION.txt') -Value $commit -Encoding UTF8

$guide = @'
QBZ DOWNLOADER - PORTABLEAPPS-COMPATIBLE BINARY

THIS IS NOT YET A .paf.exe INSTALLER.

Copy QBZ-Downloader-Portable.exe into your PortableApps skeleton:
  QBZDownloaderPortable\App\QBZDownloader\QBZ-Downloader-Portable.exe

In your PortableApps Launcher INI, provide:
  [Environment]
  QBZ_PORTABLE_DATA_DIR=%PAL:DataDir%\QBZ-Data

The patched program creates QBZ-Data\Temp at runtime and sets TEMP/TMP after
startup. Do not override TEMP/TMP in the Launcher on a first run: the
self-extracting EXE needs an existing temp location before app code runs.

All persistent app data, SQLite database, .secret.key, browser state and logs
must go into:
  QBZDownloaderPortable\Data\QBZ-Data

Back up QBZ-Data before upgrading. Do not delete the .secret.key file.
Do not move data on exit; the source patch writes to Data continuously.
You must generate the PortableApps launcher and installer separately.

Directly launching this EXE without the PortableApps environment variable
still uses the same stand-alone QBZ-Data location as the working builder.
'@
Set-Content -LiteralPath (Join-Path $OutputRoot 'READ-ME-FIRST.txt') -Value $guide -Encoding UTF8
Write-Host "PAF-compatible binary artifact assembled: $OutputRoot" -ForegroundColor Green
