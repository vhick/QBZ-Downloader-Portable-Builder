#!/usr/bin/env python3
"""Static, source-only QBZ-Downloader portability inventory.

Requires only Python stdlib. Never executes any of the checked-out project code.
Does not read Windows AppData, registry, application settings, or saved credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCANNED_DIRS = ('electron', 'src', 'client', 'scripts', 'tests')
SCANNED_SUFFIXES = {'.cjs', '.mjs', '.js', '.jsx', '.ts', '.tsx', '.json', '.yml', '.yaml', '.toml'}
SKIP_DIRS = {
    '.git', 'node_modules', 'release', 'dist', 'dist-electron', 'dist-server',
    '.next', '.cache', '.turbo', 'out', 'build', 'coverage', 'downloads',
    'data', 'QBZ-Data', '.venv', '__pycache__',
}
# Never copy personal/runtime files even if accidentally committed to the fork.
SKIP_FILENAMES = {
    'settings.json', 'history.json', '.env', '.env.local', '.env.production',
    'cookies.json', 'credentials.json', 'secrets.json', 'tokens.json',
    '.encryption-key', 'qbz.db', 'qbz.db-wal', 'qbz.db-shm',
    'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock',
}
SKIP_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.wal', '.shm', '.pem', '.key', '.p12', '.pfx'}

GROUPS = {
    'ELECTRON PROFILE AND PATH OVERRIDES': (
        'app.getPath', 'app.setPath', 'setAppLogsPath', 'userData', 'sessionData',
        'getCachePath', 'cache', 'crashDumps', 'Local Storage', 'IndexedDB',
        'app.isPackaged', 'process.execPath', 'process.resourcesPath',
        'PORTABLE_EXECUTABLE_DIR', 'QBZ-Data', 'resolveRuntimeDir',
    ),
    'BACKEND DATABASE SETTINGS AND MIGRATION': (
        'QBZ_DATA_DIR', 'QBZ_RUNTIME_DIR', 'QBZ_MIGRATE_FROM', 'qbz.db',
        'better-sqlite3', 'sqlite', 'settings.json', 'history.json',
        'download_dir', 'downloadDir', 'downloadsDir', 'migrateLegacyState',
        'dataDir', 'appData', 'APPDATA', 'LOCALAPPDATA',
    ),
    'QOBUZ CREDENTIALS ENCRYPTION': (
        'safeStorage', 'keytar', 'dpapi', 'encrypt', 'decrypt', 'credential',
        'access_token', 'refresh_token', 'authToken', 'sessionToken',
        'encryptionKey', 'encryption-key', 'password', 'secret',
        'credentialStore', 'Qobuz',
    ),
    'DOWNLOAD PATHS AND TEMPORARY FILES': (
        'Downloads', 'downloadPath', 'downloadDirectory', 'dialog.showOpenDialog',
        'dialog.showSaveDialog', 'os.tmpdir', 'tmpdir(', 'TEMP', 'TMP',
        'mkdirSync', 'mkdtemp', 'writeFile', 'createWriteStream',
        'ffmpeg', 'fpcalc',
    ),
    'UPDATER AND WINDOWS INTEGRATION': (
        'electron-updater', 'autoUpdater', 'autoDownload', 'quitAndInstall',
        'setLoginItemSettings', 'autoLaunch', 'winreg', 'reg.exe',
        'registry', 'setAsDefaultProtocolClient', 'shell.openExternal',
        'Notification',
    ),
    'WINDOWS PORTABLE PACKAGING': (
        'electron-builder', 'desktop:dist:portable', 'portable', 'artifactName',
        'extraResources', 'extraFiles', 'asarUnpack', 'release/',
        'nsis', 'node26', 'node 26', 'engines',
    ),
}

# Always capture these current upstream source/config files if present.
PRIORITY_FILES = (
    'electron/main.cjs', 'electron/preload.cjs', 'package.json',
    'README.md', 'CHANGELOG.md', 'AGENTS.md', 'LICENSE',
    '.github/workflows/release.yml',
)
MAX_READ_BYTES = 800_000  # per code file; prevents huge generated sources
MAX_COPY_BYTES = 11_000_000
MAX_MATCHING_FILES = 120
MAX_CONTEXT_OCCURRENCES_PER_GROUP = 180


def safe_relative(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def is_source_file(path: Path) -> bool:
    name = path.name.lower()
    if name in SKIP_FILENAMES or path.suffix.lower() in SKIP_SUFFIXES:
        return False
    if name.startswith('.env'):
        return False
    return path.suffix.lower() in SCANNED_SUFFIXES


def read_text(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_READ_BYTES:
        return None
    return path.read_text(encoding='utf-8', errors='replace')


def run_git_sha(source: Path) -> str:
    proc = subprocess.run(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'],
        capture_output=True, text=True, timeout=30, check=True,
    )
    sha = proc.stdout.strip()
    if not re.fullmatch(r'[a-f0-9]{40}', sha):
        raise RuntimeError('Could not determine exact 40-character Git revision')
    return sha


def main() -> int:
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--source', required=True, type=Path)
    arg.add_argument('--output', required=True, type=Path)
    ns = arg.parse_args()
    source = ns.source.resolve()
    output = ns.output.resolve()
    if not (source / 'electron' / 'main.cjs').is_file():
        raise RuntimeError(f'Missing upstream electron/main.cjs in {source}')
    if not (source / 'package.json').is_file():
        raise RuntimeError(f'Missing upstream package.json in {source}')
    if output == source or source in output.parents:
        raise RuntimeError('Output folder must not be within the source checkout')
    output.mkdir(parents=True, exist_ok=True)
    rev = run_git_sha(source)

    files: list[tuple[Path, str]] = []
    for dirname in SCANNED_DIRS:
        root = source / dirname
        if not root.is_dir():
            continue
        for current, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (Path(current)/d).is_symlink()]
            for name in names:
                path = Path(current) / name
                if not is_source_file(path):
                    continue
                text = read_text(path)
                if text is not None:
                    files.append((path, text))

    # Not all interesting fields live in the same subsystem. Record candidates and
    # copy a bounded selection of relevant source files, not credentials/runtime files.
    source_out = output / 'RelevantSource'
    source_out.mkdir(parents=True, exist_ok=True)
    matched_paths: dict[Path, set[str]] = defaultdict(set)
    report = [
        'QBZ-DOWNLOADER PORTABILITY SOURCE INSPECTION',
        f'Commit: {rev}',
        f'Scanned source files: {len(files)}',
        '',
        'SOURCE-ONLY: no application was started, no dependencies installed,',
        'and no Windows AppData, Qobuz account, registry, or local credentials were read.',
        'Potential sensitive material committed as source should be reviewed before sharing.',
    ]
    hitcounts: dict[str, int] = {}
    for title, terms in GROUPS.items():
        report.extend(['', '=' * 76, title, '=' * 76])
        emitted = 0
        total = 0
        for file, text in files:
            lines = text.splitlines()
            for i, line in enumerate(lines):
                matched = next((term for term in terms if term.casefold() in line.casefold()), None)
                if matched is None:
                    continue
                total += 1
                matched_paths[file].add(title)
                if emitted >= MAX_CONTEXT_OCCURRENCES_PER_GROUP:
                    continue
                emitted += 1
                report.append(f'--- {safe_relative(file, source)}:{i + 1} ({matched}) ---')
                for j in range(max(0, i-3), min(len(lines), i+7)):
                    report.append(f'{j + 1:>6}: {lines[j][:480]}')
                report.append('')
        hitcounts[title] = total
        report.append(f'Total matches: {total} (displayed {emitted})')
    report.extend(['', '=' * 76, 'IMPORTANT FULL SOURCE FILES', '=' * 76])

    prioritized = []
    for relative in PRIORITY_FILES:
        path = source / relative
        if path.exists() and path.is_file() and not path.is_symlink() and path.name.lower() not in SKIP_FILENAMES:
            prioritized.append(path)
    matches = sorted(matched_paths.keys(), key=lambda p: (-len(matched_paths[p]), safe_relative(p, source)))

    copied, total_bytes, skipped = [], 0, []
    for path in list(dict.fromkeys(prioritized + matches)):
        if len(copied) >= MAX_MATCHING_FILES:
            skipped.append((safe_relative(path, source), 'file-count limit'))
            continue
        size = path.stat().st_size
        if size > MAX_READ_BYTES or size + total_bytes > MAX_COPY_BYTES:
            skipped.append((safe_relative(path, source), 'size limit'))
            continue
        rel = Path(safe_relative(path, source))
        dest = source_out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        copied.append(rel.as_posix())
        total_bytes += size
    report.extend(f'Copied source: {p}' for p in copied)
    report.extend(f'SKIPPED: {p} ({why})' for p, why in skipped)

    # Package metadata is summarized without running its scripts.
    pkg: dict = {}
    try:
        pkg = json.loads((source / 'package.json').read_text(encoding='utf-8'))
    except (ValueError, OSError) as err:
        report.append(f'package.json read warning: {err}')

    summary = {
        'upstream': 'ifauzeee/QBZ-Downloader',
        'source_commit': rev,
        'inspection_type': 'static source only',
        'desktop_entry': 'electron/main.cjs',
        'package': {
            'name': pkg.get('name'),
            'version': pkg.get('version'),
            'main': pkg.get('main'),
            'engines': pkg.get('engines'),
            'portable_command': (pkg.get('scripts') or {}).get('desktop:dist:portable'),
            'electron_builder_build': pkg.get('build'),
        },
        'match_counts': hitcounts,
        'copied_files': copied,
        'skipped_files': [{'file': p, 'reason': reason} for p, reason in skipped],
        'source_files_scanned': len(files),
        'recommendation': 'Inspect exact path and credential implementation before modifying or rebuilding',
    }
    (output / 'INSPECTION-SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    (output / 'QBZ-Portability-Inspection.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
    (output / 'UPSTREAM-REVISION.txt').write_text(rev + '\n', encoding='utf-8')
    (output / 'README-ARTIFACT.txt').write_text(
        'Upload the complete QBZ-Portable-Inspection-<commit> artifact ZIP to ChatGPT.\n'
        'This report contains checked-out source code only. It does not read your PC data.\n'
        'If your fork includes secret values accidentally committed as source, review the artifact first.\n',
        encoding='utf-8',
    )
    print(f'QBZ inspection completed. Commit={rev}, scanned={len(files)}, copied={len(copied)}')
    print(f'Output: {output}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'QBZ inspection FAILED: {exc}', file=sys.stderr)
        raise
