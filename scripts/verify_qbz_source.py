#!/usr/bin/env python3
"""Validate the source patch and produce a path review report (never reads user data)."""
import argparse, json, re
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    root=a.source.resolve()
    mainjs=(root/'electron'/'main.cjs').read_text(encoding='utf-8')
    settings=(root/'src'/'services'/'settings.ts').read_text(encoding='utf-8')
    enc=(root/'src'/'utils'/'encryption.ts').read_text(encoding='utf-8')
    checks={
        'patch installed':'QBZ_TRUE_PORTABLE_PATCH_V1' in mainjs,
        'userData redirected':"app.setPath('userData', portableUserData)" in mainjs,
        'sessionData redirected':"app.setPath('sessionData', portableSessionData)" in mainjs,
        'logs redirected':'app.setAppLogsPath(portableLogs)' in mainjs,
        'crashes redirected':"app.setPath('crashDumps', portableCrashes)" in mainjs,
        'TEMP redirected':'process.env.TEMP = portableTemp' in mainjs,
        'backend portable root':"return path.join(process.env.PORTABLE_EXECUTABLE_DIR, 'QBZ-Data');" in mainjs,
        'backend chdir':'process.chdir(runtimeDir);' in mainjs,
        'download default portable':"process.env.QBZ_DEFAULT_DOWNLOADS_PATH = path.join(runtimeDir, 'downloads');" in mainjs,
        'current settings file-key encrypt':'encryptionService.encryptSync(' in settings,
        'current settings file-key decrypt':'encryptionService.decryptSync(' in settings,
        'key file layout':"'data', '.secret.key'" in enc,
        'before app ready':mainjs.index('QBZ_TRUE_PORTABLE_PATCH_V1') < mainjs.index('app.whenReady()'),
        'patch metadata':(root/'.qbz-portable-patch.json').is_file(),
    }
    hits=[]
    needles=re.compile(r'LOCALAPPDATA|APPDATA|app\.getPath\(|os\.homedir\(|getenv\(|userData|appData|TEMP|TMP',re.IGNORECASE)
    for searchroot in (root/'electron', root/'src',root/'client'/'src'):
        if not searchroot.is_dir(): continue
        for file in searchroot.rglob('*'):
            if file.suffix.lower() not in ('.js','.cjs','.ts','.tsx','.mjs'): continue
            if not file.is_file() or file.stat().st_size>2_000_000:continue
            for idx,line in enumerate(file.read_text(encoding='utf-8',errors='replace').splitlines(),1):
                if needles.search(line):
                    hits.append(f'{file.relative_to(root)}:{idx}: {line.strip()[:220]}')
    result=['QBZ TRUE PORTABLE SOURCE AUDIT','This report contains source code snippets only, no user settings.','',
            'CHECKS:']+[f'{"PASS" if value else "FAIL"}: {name}' for name,value in checks.items()]+['','POTENTIAL PATH USAGE (for review, not proof of leakage):']+hits[:700]
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text('\n'.join(result)+'\n',encoding='utf-8')
    for name,value in checks.items():print(('PASS' if value else 'FAIL'),name)
    print('Source path audit saved to:',a.report)
    if not all(checks.values()):raise SystemExit('FAIL: Portable source verification failed.')
if __name__=='__main__':main()
