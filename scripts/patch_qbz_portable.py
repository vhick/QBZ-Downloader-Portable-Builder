#!/usr/bin/env python3
"""Fail-closed source patch for the inspected QBZ-Downloader Windows portable build.

This changes only the TEMPORARY GitHub checkout. It never edits the clean fork.
"""
import argparse
import json
from pathlib import Path
import subprocess

INSPECTED = "35b8a42f2517e006cef668124f6def9597ce8757"
MARKER = "QBZ_TRUE_PORTABLE_PATCH_V1"

START_AFTER = "const crypto = require('crypto');"
DEFAULT_OLD = "process.env.QBZ_DEFAULT_DOWNLOADS_PATH = path.join(app.getPath('downloads'), 'QBZ-Downloader');"
DEFAULT_NEW = "process.env.QBZ_DEFAULT_DOWNLOADS_PATH = path.join(runtimeDir, 'downloads');"

INSERT = r"""
// QBZ_TRUE_PORTABLE_PATCH_V1
// electron-builder's portable target provides the location of the ORIGINAL
// executable, not the temporary NSIS extraction folder.
// Fail closed if somebody packages this patched build as an installer, which
// would otherwise bring back AppData-based backend storage.
if (process.platform === 'win32' && app.isPackaged) {
  if (!process.env.PORTABLE_EXECUTABLE_DIR) {
    throw new Error('QBZ portable: PORTABLE_EXECUTABLE_DIR is missing. Use the Windows portable EXE, not an installer.');
  }

  const portableBase = path.resolve(process.env.PORTABLE_EXECUTABLE_DIR);
  const portableData = path.join(portableBase, 'QBZ-Data');
  const portableUserData = path.join(portableData, 'Electron', 'UserData');
  const portableSessionData = path.join(portableData, 'Electron', 'SessionData');
  const portableLogs = path.join(portableData, 'Logs');
  const portableCrashes = path.join(portableData, 'CrashDumps');
  const portableTemp = path.join(portableData, 'Temp');

  for (const dir of [
    portableData,
    portableUserData,
    portableSessionData,
    portableLogs,
    portableCrashes,
    portableTemp,
  ]) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // Must be performed synchronously before Electron fires app.ready.
  app.setPath('userData', portableUserData);
  app.setPath('sessionData', portableSessionData);
  app.setAppLogsPath(portableLogs);
  app.setPath('crashDumps', portableCrashes);

  // Backend temporary files follow this path. The portable wrapper can still
  // briefly extract its app payload in Windows TEMP before this JS code starts.
  process.env.TEMP = portableTemp;
  process.env.TMP = portableTemp;
}
"""

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected exactly one known source anchor, found {n}. Upstream changed; stop rather than risk nonportable build.")
    return text.replace(old, new, 1)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True,type=Path)
    a=parser.parse_args()
    source=a.source.resolve()
    mainjs=source/'electron'/'main.cjs'
    settings=source/'src'/'services'/'settings.ts'
    encryption=source/'src'/'utils'/'encryption.ts'
    package=source/'package.json'
    for p in (mainjs,settings,encryption,package):
        if not p.is_file(): raise RuntimeError(f'Missing upstream file: {p}')
    code=mainjs.read_text(encoding='utf-8')
    if MARKER in code: raise RuntimeError('Source already patched; refusing to create an ambiguous build')
    required=[
        'process.env.PORTABLE_EXECUTABLE_DIR',
        "return path.join(process.env.PORTABLE_EXECUTABLE_DIR, 'QBZ-Data');",
        'process.chdir(runtimeDir);',
        "app.whenReady()",
        "process.env.QBZ_DEFAULT_DOWNLOADS_PATH",
    ]
    for needle in required:
        if needle not in code: raise RuntimeError(f'Upstream main.cjs changed: expected {needle!r}')
    if 'autoUpdater' in code or 'setLoginItemSettings' in code:
        raise RuntimeError('New updater/login-item code found; inspect upstream before making a portable build.')
    config=settings.read_text(encoding='utf-8')
    enc=encryption.read_text(encoding='utf-8')
    for needle in ['encryptionService.encryptSync(', 'encryptionService.decryptSync(']:
        if needle not in config: raise RuntimeError('Credential backend changed: '+needle)
    if "'data', '.secret.key'" not in enc:
        raise RuntimeError('Portable encryption key layout changed upstream; manual review required')
    if 'safeStorage' not in enc: raise RuntimeError('Encryption source changed; reinspection required')
    pkg=json.loads(package.read_text(encoding='utf-8'))
    if not all(name in pkg.get('scripts',{}) for name in ('build:full','bundle-binaries','desktop:rebuild')):
        raise RuntimeError('Upstream build scripts changed; update the workflow after inspection.')
    code=replace_once(code,START_AFTER,START_AFTER+'\n'+INSERT,'Electron early path injection')
    code=replace_once(code,DEFAULT_OLD,DEFAULT_NEW,'portable default download directory')
    if code.index(MARKER) > code.index('app.whenReady()'):
        raise RuntimeError('Portable Electron paths would be set too late.')
    mainjs.write_text(code,encoding='utf-8')
    sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip() if (source/'.git').exists() else 'local-source-test'
    marker={
        'patch':'QBZ True Portable v1.0',
        'inspected_source_commit':INSPECTED,
        'built_source_commit':sha,
        'electron_user_data':'QBZ-Data/Electron/UserData',
        'electron_session_data':'QBZ-Data/Electron/SessionData',
        'logs':'QBZ-Data/Logs',
        'temporary_files':'QBZ-Data/Temp',
        'downloads_default':'QBZ-Data/downloads',
        'credentials':'unchanged upstream file-key storage; preserve data/.secret.key with data/qbz.db',
        'notes':['Older safeStorage safe: entries may remain DPAPI-bound.',
                 'Download destinations explicitly selected by users remain unchanged.',
                 'The electron-builder portable EXE unpacks itself in OS TEMP before application startup.']
    }
    (source/'.qbz-portable-patch.json').write_text(json.dumps(marker,indent=2),encoding='utf-8')
    print('PASS: portable Electron profile, cache, logs, crash and Temp paths patched')
    print('PASS: existing SQLite database and encryption key logic unchanged')
    print('PASS: download default changed without overriding a saved user choice')

if __name__=='__main__':main()
