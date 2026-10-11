# QBZ Downloader True-Portable Builder v1.0

This is the **initial Windows build kit**, grounded in the uploaded source inspection for `35b8a42f2517e006cef668124f6def9597ce8757` (version 5.6.3).

It patches the temporary GitHub checkout only. Your synced fork stays unchanged.

**Purpose:** redirect Electron userData/sessionData/logs/crash dumps and QBZ-owned TEMP beside the portable EXE, while preserving the existing backend database/key scheme and respecting any saved download path.

## Build

Actions > Build QBZ Downloader True Portable > Run workflow, leave source blank and ref `main`.

The output is `QBZ-Downloader-True-Portable-Windows-x64-<commit>`.

## Security and portability caveats

* Save the **entire `QBZ-Data` folder**. Preserve `data/qbz.db`, `data/.secret.key`, and any SQLite WAL/SHM files together.
* The application's current settings use file-key encryption. Older `safe:` entries encrypted through Windows DPAPI may not survive a Windows reinstall. The patch does not convert credential formats.
* The portable wrapper temporarily extracts via Windows TEMP; that is not the same as settings in AppData and cannot be wholly redirected by Electron app source.
* Explicit custom download paths remain unchanged. If moved to a new drive letter, some downloaded-file references may need updating.
* The first runner build and runtime behavior are **not yet verified**. Check for any residual state in AppData before using it as your sole copy.
* An upstream change to the settings encryption or source anchors makes the build fail for review.

## Future source changes

If the builder turns red after a sync, send the complete GitHub Actions logs and `QBZ-Builder-Diagnostics` artifact for inspection. Do not bypass the patch failure.

For one-time data migration or checking settings, double-click the matching `.cmd` helper. Each `.cmd` starts its `.ps1` partner.
