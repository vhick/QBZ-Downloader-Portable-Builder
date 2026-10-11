# QBZ-Downloader Portable Builder — Inspection Edition

This is the **first stage only** of building a truly portable QBZ-Downloader.

It checks a **clean, synchronized fork** of [`ifauzeee/QBZ-Downloader`](https://github.com/ifauzeee/QBZ-Downloader) and produces a source-inspection artifact. It **does not build an EXE or modify the original source**.

## Why inspect it?

Upstream already has an Electron portable executable and uses `PORTABLE_EXECUTABLE_DIR` to put the backend's `QBZ-Data` beside the executable. We need to inspect the remaining Electron browser profile, updater, download destinations, and credential encryption before claiming it is fully portable.

## GitHub repositories

- **Clean fork:** `YOUR-USERNAME/QBZ-Downloader`
- **New inspection builder:** `YOUR-USERNAME/QBZ-Downloader-Portable-Builder`

Keep the fork untouched. The builder holds the inspection scripts and, later, the portable source patch.

## Run the inspection

On the builder repository, open:

**Actions → Inspect QBZ-Downloader Portability → Run workflow**

Leave the source repository blank (uses your fork), leave branch at `main`, then click **Run workflow**.

After a green result, download **QBZ-Portable-Inspection-<commit>** under **Artifacts** and upload it to ChatGPT.

## No local prerequisites

Python runs on GitHub's temporary Windows runner; **nothing needs to be installed on your computer**. No npm packages are installed in the inspection.

## What does it collect?

- Main Electron process and packaging configuration
- Path resolution for QBZ-Data, Chromium userData/sessionData/cache
- Credentials, encryption and Qobuz authentication source code
- Backend SQLite database settings/migration and downloaded music path handling
- Update, autostart, and temporary file logic
- Relevant source files only, plus an inspection report and Git revision

It excludes typical `.env`, token, database, runtime, download and binary files from source collection, and never reads **your** actual AppData, registry or stored credentials. Review the artifact if your fork ever contained secrets committed directly in source code.

## Do not do these things yet

- Do **not** enable automatic portable builds through Universal Fork Sync.
- Do **not** overwrite your working QBZ portable EXE.
- Do **not** delete existing QBZ-Data or move your music library.

After source inspection, the builder will be replaced with a verified true-portable version.
