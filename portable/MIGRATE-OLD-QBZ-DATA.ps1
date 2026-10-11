# Portable QBZ data migration — does not delete or overwrite source files.
$ErrorActionPreference = 'Stop'
$target = Join-Path $PSScriptRoot 'QBZ-Data'
Write-Host ''
Write-Host 'QBZ Downloader portable data migration' -ForegroundColor Cyan
Write-Host 'CLOSE QBZ Downloader everywhere before continuing.' -ForegroundColor Yellow
Write-Host 'Source must be the ORIGINAL QBZ-Data folder (or its parent folder).'
Write-Host ''
$inputPath = Read-Host 'Paste the existing QBZ-Data folder path (or press Enter to cancel)'
if ([string]::IsNullOrWhiteSpace($inputPath)) { Write-Host 'Cancelled.'; return }
$inputPath = $inputPath.Trim().Trim('"')
if (!(Test-Path -LiteralPath $inputPath -PathType Container)) { throw "Folder not found: $inputPath" }
$source = [IO.Path]::GetFullPath($inputPath)
if ((Split-Path -Leaf $source) -ine 'QBZ-Data') {
  $nested = Join-Path $source 'QBZ-Data'
  if (Test-Path -LiteralPath $nested -PathType Container) { $source = $nested }
}
$source = [IO.Path]::GetFullPath($source)
$target = [IO.Path]::GetFullPath($target)
if ($source.TrimEnd('\') -ieq $target.TrimEnd('\')) { throw 'Source and destination are the same folder.' }
if (!(Test-Path -LiteralPath (Join-Path $source 'data') -PathType Container) -and
    !(Test-Path -LiteralPath (Join-Path $source 'settings.json') -PathType Leaf)) {
  throw 'That does not appear to contain QBZ application data. Check your source folder.'
}
if (Test-Path -LiteralPath $target -PathType Container) {
  $items = @(Get-ChildItem -LiteralPath $target -Force -ErrorAction SilentlyContinue)
  if ($items.Count -gt 0) { throw "Destination already has files. To avoid overwriting, stop here: $target" }
} else { New-Item -ItemType Directory -Path $target -Force | Out-Null }
Write-Host "Copying from: $source"
Write-Host "Into:         $target"
# Robocopy copies dot-files, SQLite WAL and SHM files, and preserves timestamps.
# It does not delete or change the original.
& robocopy.exe "$source" "$target" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -gt 7) { throw "Copy failed (robocopy $LASTEXITCODE). Do not delete the original." }
foreach ($file in @('data\qbz.db','data\.secret.key')) {
  $found = Test-Path -LiteralPath (Join-Path $target $file) -PathType Leaf
  Write-Host "$file found: $found"
}
Write-Host ''
Write-Host 'Migration copied. Original data remains untouched.' -ForegroundColor Green
Write-Host 'Do NOT delete the original until the portable version is tested.'
Read-Host 'Press Enter to close' | Out-Null
