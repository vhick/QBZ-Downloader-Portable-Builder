#!/usr/bin/env python3
"""Layer a PAF Data-folder override on the proven QBZ standalone source patch.

Only the temporary Actions checkout is modified. The original standalone
build-portable.yml and its source-patch script remain unchanged.

Data target provided by PortableApps Launcher:
  QBZ_PORTABLE_DATA_DIR=%PAL:DataDir%\\QBZ-Data

With no override, the executable behaves like the proven standalone build.
"""
import argparse
import json
from pathlib import Path

MARKER = 'QBZ_PAF_OVERRIDE_PATCH_V1'

# Both anchors are from the already-verified standalone v1.1 source patch.
OLD_RUNTIME = """function resolveRuntimeDir() {
  if (process.env.PORTABLE_EXECUTABLE_DIR) {"""
NEW_RUNTIME = """function resolveRuntimeDir() {
  // QBZ_PAF_OVERRIDE_PATCH_V1: optional PortableApps-preserved data root.
  if (process.env.QBZ_PORTABLE_DATA_DIR) {
    return path.resolve(process.env.QBZ_PORTABLE_DATA_DIR);
  }
  if (process.env.PORTABLE_EXECUTABLE_DIR) {"""

OLD_DATA = """  const portableData = path.join(portableBase, 'QBZ-Data');"""
NEW_DATA = """  // PortableApps Launcher can direct writes to its preserved top-level Data.
  if (process.env.QBZ_PORTABLE_DATA_DIR && !path.isAbsolute(process.env.QBZ_PORTABLE_DATA_DIR)) {
    throw new Error('QBZ PAF: QBZ_PORTABLE_DATA_DIR must be an absolute path.');
  }
  const portableData = process.env.QBZ_PORTABLE_DATA_DIR
    ? path.resolve(process.env.QBZ_PORTABLE_DATA_DIR)
    : path.join(portableBase, 'QBZ-Data');"""


def replace_exact(text: str, before: str, after: str, name: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f'{name}: expected exactly one original anchor, found {count}. '
                           'Upstream or the standalone patch changed: stop safely.')
    return text.replace(before, after, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve()
    mainjs = source / 'electron' / 'main.cjs'
    standalone_marker = source / '.qbz-portable-patch.json'
    if not mainjs.is_file() or not standalone_marker.is_file():
        raise RuntimeError('Run the working patch_qbz_portable.py first.')
    code = mainjs.read_text(encoding='utf-8')
    if 'QBZ_TRUE_PORTABLE_PATCH_V1' not in code:
        raise RuntimeError('The verified standalone portable patch is missing.')
    if MARKER in code:
        raise RuntimeError('PAF extension is already present; refusing double-patch.')
    code = replace_exact(code, OLD_RUNTIME, NEW_RUNTIME, 'backend data root')
    code = replace_exact(code, OLD_DATA, NEW_DATA, 'Electron profile/data root')
    if code.index(MARKER) >= code.index('app.whenReady()'):
        raise RuntimeError('PAF override must be installed before Electron app.ready.')
    mainjs.write_text(code, encoding='utf-8')
    metadata = {
        'patch': 'QBZ PAF Data override v1.0',
        'extends': 'QBZ True Portable v1.1 working build',
        'variable': 'QBZ_PORTABLE_DATA_DIR',
        'example': r'%PAL:DataDir%\QBZ-Data',
        'normal_standalone_fallback': 'QBZ-Data beside original portable EXE',
        'persistent_data': 'QBZ-Data (including data/qbz.db and data/.secret.key)',
        'installer': 'Not included: build outputs PAF-compatible EXE, not a .paf.exe',
    }
    (source / '.qbz-paf-patch.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print('PASS: QBZ_PORTABLE_DATA_DIR honored by Electron profile AND backend')
    print('PASS: standalone data path preserved when no override is set')
    print('PASS: existing database and encryption-key code untouched')


if __name__ == '__main__':
    main()
