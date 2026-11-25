#!/usr/bin/env python3
"""One-time, verified migration requested on 20 November 2026.

Run without arguments for a read-only preflight; --execute performs the move.
The original project path becomes a compatibility symlink only after every
original file has been copied and hash-verified. Existing different files are
never overwritten. A changed source aborts cleanup.
"""
from pathlib import Path
import argparse
from datetime import datetime
import hashlib
import json
import shutil
import zipfile

SOURCE = Path('/Users/jingwen.hu/Files/Projects/Trash Bin Pro Max')
DESTINATION = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def inventory(root):
    result = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Source contains a symlink requiring review: {path}')
        if path.is_file():
            result.append({'path': path.relative_to(root).as_posix(),
                           'bytes': path.stat().st_size, 'sha256': digest(path)})
    return result


def write_report(report):
    target = DESTINATION / 'docs/MIGRATION.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if SOURCE.is_symlink() and SOURCE.resolve() == DESTINATION.resolve():
        print('Already migrated; compatibility link points to this repository.')
        return
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    if SOURCE.samefile(DESTINATION):
        raise ValueError('Source and destination must be separate directories.')
    original = inventory(SOURCE)
    conflicts = [r['path'] for r in original if (DESTINATION / r['path']).exists()
                 and (not (DESTINATION / r['path']).is_file()
                      or digest(DESTINATION / r['path']) != r['sha256'])]
    if conflicts:
        raise ValueError(f'Different destination files would be overwritten: {conflicts}')
    attachment_paths = json.loads((DESTINATION / 'docs/migration-attachment-sources.json').read_text())
    attachments, missing = [], []
    for name in attachment_paths:
        path = Path(name)
        if not path.is_file():
            missing.append(name)
            continue
        relative = Path('Reference Inputs') / (path.parent.name[:8] + '--' + path.name)
        if (DESTINATION / relative).exists() and digest(DESTINATION / relative) != digest(path):
            raise ValueError(f'Attachment name conflict: {relative}')
        attachments.append({'source': name, 'path': relative.as_posix(),
                            'bytes': path.stat().st_size, 'sha256': digest(path)})
    print(json.dumps({'source_files': len(original), 'source_bytes': sum(r['bytes'] for r in original),
                      'available_attachments': len(attachments), 'missing_attachments': missing,
                      'conflicts': conflicts, 'execute': args.execute}, indent=2))
    if not args.execute:
        return
    for child in SOURCE.iterdir():
        target = DESTINATION / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True, copy_function=shutil.copy2)
        elif not target.exists():
            shutil.copy2(child, target)
    for record in original:
        if digest(DESTINATION / record['path']) != record['sha256']:
            raise ValueError(f'Copy hash mismatch: {record["path"]}')
    for record in attachments:
        target = DESTINATION / record['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(record['source'], target)
        if digest(target) != record['sha256']:
            raise ValueError(f'Attachment hash mismatch: {target}')
    archives = []
    for record in original:
        if record['path'].lower().endswith('.zip'):
            with zipfile.ZipFile(DESTINATION / record['path']) as archive:
                failure = archive.testzip()
                if failure:
                    raise ValueError(f'Archive corruption: {record["path"]} / {failure}')
                archives.append({'path': record['path'], 'entries': len(archive.namelist()), 'crc_pass': True})
    if inventory(SOURCE) != original:
        raise ValueError('Source changed during migration. Original folder retained; rerun after work stops.')
    report = {'date': '2026-11-20', 'destination': str(DESTINATION), 'source': str(SOURCE),
              'status': 'copied_and_sha256_verified', 'source_file_count': len(original),
              'source_bytes': sum(r['bytes'] for r in original), 'files': original,
              'reference_attachments': attachments, 'unavailable_attachments': missing,
              'archives': archives, 'source_originals_byte_identical': True,
              'history': {'mechanical_turns': 13, 'materials_turns': 5, 'vision_turns': 6,
                          'scope': 'Available user-visible messages returned by the chat reader; not hidden tool traces.'},
              'dataset_note': 'Downloaded HGI-30 images were not in the saved project folder; no dataset location was supplied.',
              'git_note': 'Existing .git, LICENSE and .gitattributes retained; no commit or push performed.'}
    write_report(report)
    # Rename before replacing with a link: failures leave an intact recoverable
    # source backup. Delete the duplicate only after checking the compatibility path.
    backup = SOURCE.with_name('.Trash Bin Pro Max migration backup ' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    if backup.exists():
        raise FileExistsError(backup)
    SOURCE.rename(backup)
    try:
        SOURCE.symlink_to(DESTINATION, target_is_directory=True)
        if not SOURCE.samefile(DESTINATION):
            raise ValueError('Compatibility link does not point to destination.')
        for record in original:
            if digest(SOURCE / record['path']) != record['sha256']:
                raise ValueError(f'Compatibility path failed: {record["path"]}')
    except BaseException:
        if SOURCE.is_symlink():
            SOURCE.unlink()
        backup.rename(SOURCE)
        raise
    shutil.rmtree(backup)
    report.update(status='complete', compatibility_link=str(SOURCE),
                  compatibility_target=str(DESTINATION), compatibility_hash_checks_pass=True,
                  duplicate_source_backup_removed=True)
    write_report(report)
    print(f'COMPLETE: {len(original)} project files + {len(attachments)} original inputs verified.')
    print(f'Previous location now links to {DESTINATION}')


if __name__ == '__main__':
    main()
