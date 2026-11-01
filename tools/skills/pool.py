#!/usr/bin/env python3
"""Materialize and verify a passive, self-contained skill pool; execute no upstream code.

Spec: knowledge/operations/skill-selection.md
"""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT.parent
POOL = ROOT / 'skills'
GENERATOR = 'aeion-skill-files-v2'
SOURCES = {
    'ecc': ('affaan-m/ECC', 'ecc', ('skills/*/SKILL.md',), ('agents/*.md',)),
    'agent-skills': ('addyosmani/agent-skills', 'agent-skills', ('skills/*/SKILL.md',), ('agents/*.md',)),
    'claude-plugins-official': ('anthropics/claude-plugins-official', 'aeion-factory/claude-plugins-official',
                                ('plugins/*/skills/*/SKILL.md',), ('plugins/*/agents/*.md',)),
    'knowledge-work-plugins': ('anthropics/knowledge-work-plugins', 'knowledge-work-plugins',
                               ('*/skills/*/SKILL.md',), ('*/agents/*.md',)),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def materialized_bytes(path):
    """Apply only reviewed, exact-source-bound scanner annotations; preserve runtime behavior."""
    data = path.read_bytes()
    registry = ROOT / 'tools/skills/annotations.json'
    annotations = json.loads(registry.read_text()) if registry.exists() else []
    for annotation in annotations:
        if path.relative_to(WORKSPACE).as_posix() != annotation['file']:
            continue
        if hashlib.sha256(data).hexdigest() != annotation['source_sha256']:
            raise ValueError(f'Review annotation against changed upstream source: {path}')
        text = data.decode('utf-8')
        needle = annotation['needle']
        if text.count(needle) != 1:
            raise ValueError(f'Annotation target is missing or ambiguous: {path}')
        indent = needle[:len(needle) - len(needle.lstrip())]
        replacement = indent + '# ' + annotation['reason'] + '\n' + needle + '  # nosemgrep: ' + annotation['rule']
        return text.replace(needle, replacement, 1).encode('utf-8')
    return data


def inside(path, root):
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError(f'Unexpected source symlink or escaping path: {path}')
    return path


def metadata(path):
    text = path.read_text(encoding='utf-8')
    front = re.match(r'\A---\n(.*?)\n---', text, re.S)
    description = ''
    if front:
        match = re.search(r'(?m)^description:[^\S\n]*(.+)', front[1])
        if match:
            description = match[1].strip().strip('\"\'')
            if description in {'|', '>', '|-', '>-'}:
                description = ' '.join(re.findall(r'(?m)^ +(.+)', front[1]))
    title = re.search(r'(?m)^# +(.+)', text)
    return title[1] if title else path.stem, description[:600]


def license_for(path, root):
    directory = path.parent
    while True:
        for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt'):
            candidate = directory / name
            if candidate.is_file():
                inside(candidate, root)
                text = candidate.read_text(encoding='utf-8')
                label = 'restricted-or-unreviewed'
                if 'Permission is hereby granted, free of charge' in text:
                    label = 'MIT'
                elif 'Apache License' in text and 'Version 2.0' in text:
                    label = 'Apache-2.0'
                return label, candidate
        if directory == root:
            return 'unreviewed', None
        directory = directory.parent


def source_pins():
    lock = json.loads((WORKSPACE / 'third-party/sources.lock.json').read_text())
    pins = {}
    for name, (repository, folder, _, _) in SOURCES.items():
        root = WORKSPACE / 'third-party' / folder
        inside(root, WORKSPACE / 'third-party')
        if not root.is_dir():
            raise ValueError(f'Missing source: {name}; update the four sources first')
        pin = lock.get(name)
        marker = json.loads((root / '.aeion-upstream.json').read_text())
        if not pin or marker != pin or pin.get('repository') != repository:
            raise ValueError(f'Source lock/provenance mismatch: {name}')
        pins[name] = pin
    return pins


def source_catalog():
    pins, entries = source_pins(), []
    for source, (_, folder, skill_patterns, agent_patterns) in SOURCES.items():
        root = WORKSPACE / 'third-party' / folder
        for kind, patterns in (('skill', skill_patterns), ('agent', agent_patterns)):
            for path in sorted({p for pattern in patterns for p in root.glob(pattern)}):
                relative = path.relative_to(root).as_posix()
                if relative.startswith('partner-built/'):
                    continue
                inside(path, root)
                label, license_path = license_for(path, root)
                title, description = metadata(path)
                stem = relative.removesuffix('/SKILL.md').removesuffix('.md')
                identifier = source + '--' + re.sub(r'[^a-z0-9-]+', '-', stem.lower()).strip('-')
                portable = label in {'MIT', 'Apache-2.0'}
                location = ('agents/' + identifier + '.md' if kind == 'agent' else identifier) if portable else None
                files = {}
                if portable:
                    candidates = sorted(path.parent.rglob('*')) if kind == 'skill' else [path]
                    for candidate in candidates:
                        inside(candidate, root)
                        if candidate.is_file() and candidate.name != '.DS_Store':
                            key = candidate.relative_to(path.parent).as_posix() if kind == 'skill' else path.name
                            files[key] = {'sha256': hashlib.sha256(materialized_bytes(candidate)).hexdigest(),
                                          'source_sha256': digest(candidate),
                                          'executable': bool(candidate.stat().st_mode & 0o111)}
                entries.append({'id': identifier, 'source': source, 'kind': kind, 'title': title,
                                'description': description, 'upstream_file': relative,
                                'file': path.relative_to(WORKSPACE).as_posix(), 'sha256': digest(path),
                                'commit': pins[source]['commit'], 'license': label,
                                'license_file': license_path.relative_to(WORKSPACE).as_posix() if license_path else None,
                                'license_sha256': digest(license_path) if license_path else None,
                                'portable_reference': portable, 'link': location, 'files': files})
    if source_pins() != pins:
        raise ValueError('Sources changed while indexing; retry after source sync')
    entries.sort(key=lambda e: (e['source'], e['kind'], e['id']))
    if len({e['id'] for e in entries}) != len(entries):
        raise ValueError('Catalog identifier collision')
    return {'generator': GENERATOR, 'sources': pins, 'entries': entries}


def licenses(data):
    return {'licenses/' + e['license_sha256'] + '.txt': e['license_file']
            for e in data['entries'] if e['portable_reference']}


def local_files(data):
    files = {}
    for entry in data['entries']:
        if entry['portable_reference']:
            for relative, info in entry['files'].items():
                location = entry['link'] + '/' + relative if entry['kind'] == 'skill' else entry['link']
                files[location] = info['sha256']
    for location in licenses(data):
        files[location] = Path(location).stem
    return files


def inventory(data):
    counts = Counter((e['source'], e['kind']) for e in data['entries'] if e['portable_reference'])
    lines = ['# Local skill and agent files', '',
             'These are real versioned files, including resources and upstream licenses. No source symlinks.',
             'Read README.md first. Agent profiles are passive documents; nothing is launched automatically.', '',
             "From Factory: `python3 tools/skills/pool.py search 'code reviewer' --source ecc --kind agent`", '',
             '| Source | Skills | Agent profiles |', '| --- | ---: | ---: |']
    for source in SOURCES:
        lines.append(f'| {source} | {counts[source, "skill"]} | {counts[source, "agent"]} |')
    lines += ['', 'Restricted/unreviewed definitions are metadata-only; they are not materialized.',
              'Refreshing needs the four third-party sources. Reading, searching and checking do not.', '']
    return '\n'.join(lines)


def verify(data, directory=None):
    directory = POOL if directory is None else directory
    if data.get('generator') != GENERATOR or directory.is_symlink():
        raise ValueError('Unknown or symlink pool')
    expected = local_files(data)
    actual = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink in materialized pool: {path}')
        if path.is_file() and path.name != '.DS_Store':
            actual[path.relative_to(directory).as_posix()] = path
    controls = {'README.md', 'INDEX.md', 'catalog.json'}
    if set(actual) != set(expected) | controls:
        raise ValueError(f'Unmanaged or missing pool files: {sorted(set(actual) ^ (set(expected) | controls))[:8]}')
    for relative, sha in expected.items():
        if digest(actual[relative]) != sha:
            raise ValueError(f'Locally modified pool file; preserve/review before refresh: {relative}')
    if json.loads((directory / 'catalog.json').read_text()) != data:
        raise ValueError('Catalog changed during maintenance')
    if (directory / 'INDEX.md').read_text() != inventory(data):
        raise ValueError('Generated index changed')


def refresh(data):
    if POOL.is_symlink():
        raise ValueError('Refusing symlink pool root')
    policy = (POOL / 'README.md').read_text()
    existing = {p.name for p in POOL.iterdir() if p.name != '.DS_Store'}
    old = None
    if existing != {'README.md'}:
        old = json.loads((POOL / 'catalog.json').read_text())
        verify(old)
    state = ROOT / '.aeion'
    state.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='skill-build-', dir=state) as temporary:
        candidate = Path(temporary) / 'skills'
        candidate.mkdir()
        (candidate / 'agents').mkdir()
        (candidate / 'licenses').mkdir()
        (candidate / 'README.md').write_text(policy)
        if (POOL / '.DS_Store').is_file() and not (POOL / '.DS_Store').is_symlink():
            shutil.copyfile(POOL / '.DS_Store', candidate / '.DS_Store')
        for entry in data['entries']:
            if not entry['portable_reference']:
                continue
            source = WORKSPACE / entry['file']
            for relative, info in entry['files'].items():
                original = source.parent / relative if entry['kind'] == 'skill' else source
                location = candidate / entry['link']
                target = location / relative if entry['kind'] == 'skill' else location
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(materialized_bytes(original))
                target.chmod(0o755 if info['executable'] else 0o644)
                if digest(target) != info['sha256']:
                    raise ValueError('Source changed during copy; retry after sync')
        for relative, source in licenses(data).items():
            shutil.copyfile(WORKSPACE / source, candidate / relative)
        (candidate / 'catalog.json').write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
        (candidate / 'INDEX.md').write_text(inventory(data))
        # Keep the previous tree outside temporary cleanup, including writes from an already-open editor.
        previous = Path(tempfile.mkdtemp(prefix='skill-pool-backup-', dir=state)) / 'skills'
        try:
            POOL.rename(previous)
            if old:
                verify(old, previous)
            if (previous / 'README.md').read_text() != policy:
                raise ValueError('Pool policy changed during maintenance')
            candidate.rename(POOL)
            verify(data)
        except (OSError, ValueError, KeyboardInterrupt):
            if previous.exists():
                if POOL.exists():
                    POOL.rename(previous.parent / 'failed-new')
                previous.rename(POOL)
            raise


def search(query, limit, source=None, kind=None):
    data = json.loads((POOL / 'catalog.json').read_text())
    terms = re.findall(r'[a-z0-9]+', query.lower())
    ranked = []
    for entry in data['entries']:
        if not entry['portable_reference'] or (source and entry['source'] != source) or (kind and entry['kind'] != kind):
            continue
        words = (entry['id'] + ' ' + entry['title'] + ' ' + entry['description']).lower()
        score = sum((4 if t in entry['id'] else 0) + (2 if t in entry['title'].lower() else 0) + (t in words) for t in terms)
        if score:
            ranked.append((-score, entry['id'], entry))
    for _, _, entry in sorted(ranked)[:limit]:
        path = POOL / entry['link']
        if entry['kind'] == 'skill':
            path /= 'SKILL.md'
        if path.is_symlink() or digest(path) != entry['sha256']:
            raise ValueError(f'Changed local entrypoint: {path}')
        print(f"{entry['id']} [{entry['kind']}; {entry['license']}]\n  {entry['description'][:220]}\n  {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('refresh', 'check', 'search'))
    parser.add_argument('query', nargs='?', default='')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--source', choices=tuple(SOURCES))
    parser.add_argument('--kind', choices=('skill', 'agent'))
    parser.add_argument('--sources', action='store_true', help='Also compare current third-party source files')
    args = parser.parse_args()
    if args.action == 'search':
        if not args.query or not 1 <= args.limit <= 30:
            parser.error('Supply a query and a limit between 1 and 30')
        search(args.query, args.limit, args.source, args.kind)
        return
    state = ROOT / '.aeion'
    state.mkdir(exist_ok=True)
    descriptor = os.open(state / 'skill-pool.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another pool maintenance run is active') from None
        data = source_catalog() if args.action == 'refresh' else json.loads((POOL / 'catalog.json').read_text())
        if args.action == 'refresh':
            refresh(data)
        verify(data)
        if args.sources and source_catalog() != data:
            raise ValueError('Source files changed; review and refresh')
    counts = Counter(e['kind'] for e in data['entries'] if e['portable_reference'])
    print(f"PASS: {counts['skill']} materialized skills; {counts['agent']} materialized agent profiles; no upstream execution")


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
