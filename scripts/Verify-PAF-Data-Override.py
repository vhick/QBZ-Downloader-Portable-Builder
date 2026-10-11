#!/usr/bin/env python3
"""Validate PAF-specific source behavior; never read user profiles or credentials."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    code = (source / 'electron' / 'main.cjs').read_text(encoding='utf-8')
    settings = (source / 'src' / 'services' / 'settings.ts').read_text(encoding='utf-8')
    encryption = (source / 'src' / 'utils' / 'encryption.ts').read_text(encoding='utf-8')
    checks = {
        'standalone patch preserved': 'QBZ_TRUE_PORTABLE_PATCH_V1' in code,
        'PAF patch marker installed': 'QBZ_PAF_OVERRIDE_PATCH_V1' in code,
        'backend override supported': 'return path.resolve(process.env.QBZ_PORTABLE_DATA_DIR);' in code,
        'backend fallback retained': "return path.join(process.env.PORTABLE_EXECUTABLE_DIR, 'QBZ-Data');" in code,
        'Electron override supported': 'const portableData = process.env.QBZ_PORTABLE_DATA_DIR' in code,
        'standalone Electron fallback preserved': "path.join(portableBase, 'QBZ-Data');" in code,
        'absolute path checked': 'QBZ_PORTABLE_DATA_DIR must be an absolute path' in code,
        'profile and session follow chosen root': "path.join(portableData, 'Electron', 'UserData')" in code
             and "path.join(portableData, 'Electron', 'SessionData')" in code,
        'downloads default follows runtime': "process.env.QBZ_DEFAULT_DOWNLOADS_PATH = path.join(runtimeDir, 'downloads');" in code,
        'file-key encryption untouched': "'data', '.secret.key'" in encryption
             and 'encryptionService.encryptSync(' in settings
             and 'encryptionService.decryptSync(' in settings,
        'PAF patch runs before ready': code.index('QBZ_PAF_OVERRIDE_PATCH_V1') < code.index('app.whenReady()'),
        'PAF metadata exists': (source / '.qbz-paf-patch.json').is_file(),
    }
    report = [
        'QBZ PAF SOURCE CHECK',
        'Source-only report. No stored user credentials read.',
        '',
        *[f'{"PASS" if ok else "FAIL"}: {name}' for name, ok in checks.items()],
        '',
        'Expected from PortableApps launcher:',
        r'QBZ_PORTABLE_DATA_DIR=%PAL:DataDir%\QBZ-Data',
        'Portable TEMP is created by patched application at startup.',
        'Leave system TEMP available to self-extracting EXE before startup.',
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text('\n'.join(report) + '\n', encoding='utf-8')
    for name, value in checks.items():
        print(f'{"PASS" if value else "FAIL"}: {name}')
    if not all(checks.values()):
        raise SystemExit('PAF source verification failed; aborting build.')
    print('Report:', args.report)


if __name__ == '__main__':
    main()
