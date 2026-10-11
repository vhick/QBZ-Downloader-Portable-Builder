#!/usr/bin/env python3
"""Prepare a fail-closed electron-builder config for QBZ desktop portable EXE.

The upstream package.json's "main": "dist/index.js" is intended for the Node
backend. Electron must instead start at electron/main.cjs. Packaging output
must be in release/, never dist/, because the backend build lives in dist/.

This script touches only the temporary GitHub source checkout, not the fork.
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    root = args.source.resolve()
    report = args.report.resolve()
    pkgfile = root / 'package.json'
    patchfile = root / '.qbz-portable-patch.json'

    if not pkgfile.is_file():
        raise RuntimeError('Missing upstream package.json')
    if not patchfile.is_file():
        raise RuntimeError('Portable source patch marker missing; refusing to package.')
    pkg = json.loads(pkgfile.read_text(encoding='utf-8'))
    if pkg.get('main') != 'dist/index.js':
        raise RuntimeError('Backend package.json main has changed upstream; re-inspect desktop entry point.')

    required_files = [
        'electron/main.cjs',
        'electron/preload.cjs',
        'dist/index.js',
        'dist/services/notifications.js',
        'bin/win32-x64/ffmpeg.exe',
        'bin/win32-x64/fpcalc.exe',
    ]
    missing = [rel for rel in required_files if not (root / rel).is_file()]
    if missing:
        raise RuntimeError('Required desktop files missing before packaging:\n  ' + '\n  '.join(missing))

    main = (root / 'electron/main.cjs').read_text(encoding='utf-8')
    if 'QBZ_TRUE_PORTABLE_PATCH_V1' not in main:
        raise RuntimeError('Electron main lacks the true-portable path patch')
    if "path.join(baseAppPath, 'dist', 'index.js')" not in main:
        raise RuntimeError('Backend loading entry changed upstream; inspect before packaging')
    if "path.join(__dirname, 'preload.cjs')" not in main:
        raise RuntimeError('Electron preload path changed upstream; inspect before packaging')

    cfg = {
        'appId': 'com.qbz.downloader.portable',
        'productName': 'QBZ Downloader',
        'directories': {
            'output': 'release',
        },
        # Distinct from backend's package.json main. The app's package.json
        # remains unchanged so Node commands continue to target dist/index.js.
        'extraMetadata': {'main': 'electron/main.cjs'},
        # Explicit globs prevent accidentally omitting the Electron entry point,
        # preload, built Node backend and dashboard static files.
        'files': [
            'electron/**/*',
            'dist/**/*',
            'assets/desktop/**/*',
            'package.json',
        ],
        'asar': True,
        'asarUnpack': ['**/*.node'],
        # Native executable paths are resolved relative to process.resourcesPath.
        # Bundled binaries MUST be external to app.asar to be executable.
        'extraResources': [
            {'from': 'bin/win32-x64', 'to': 'bin/win32-x64', 'filter': ['*.exe']}
        ],
        'win': {'target': ['portable']},
        'portable': {'artifactName': 'QBZ-Downloader-Portable-${version}-${arch}.${ext}'},
    }
    if (root / 'assets/desktop/icon.ico').is_file():
        cfg['win']['icon'] = 'assets/desktop/icon.ico'

    output = root / 'electron-builder.portable.json'
    output.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')

    lines = [
        'QBZ ELECTRON PACKAGING PREFLIGHT',
        'Source version: ' + str(pkg.get('version')),
        'Backend package.json main: ' + str(pkg.get('main')),
        'Packaged Electron main: ' + cfg['extraMetadata']['main'],
        'Electron Builder output: ' + cfg['directories']['output'],
        'ASAR: enabled',
        'Preflight requirements: PASS',
        '',
        'Bundled entry/dependency checks:',
        *['  FOUND ' + rel for rel in required_files],
        '',
        'Output configuration:',
        json.dumps(cfg, indent=2),
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('PASS: Electron desktop entry = electron/main.cjs (backend main unchanged)')
    print('PASS: output = release/ (does not overwrite compiled dist/)')
    print('PASS: bundled FFmpeg and fpcalc placed in resources/bin/win32-x64')
    print('PASS: electron-builder packaging config prepared at', output)
    print('Preflight report:', report)


if __name__ == '__main__':
    main()
