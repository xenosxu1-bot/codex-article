# -*- coding: utf-8 -*-
"""Normalize active formal article IDs and related assets after retirement."""
from __future__ import annotations
import argparse, json, os, re, shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / '07-\u8d44\u6599\u4e0e\u6d41\u7a0b' / '\u6587\u7ae0\u8d44\u4ea7\u767b\u8bb0\u8868.md'
META_DIR = ROOT / '07-\u8d44\u6599\u4e0e\u6d41\u7a0b' / '\u6587\u7ae0\u5143\u6570\u636e'
DIR = re.compile(r'^0[1-6]-')
ART = re.compile(r'^(\d{2})-(.+)\.md$')
TEXT = {'.md', '.json', '.py', '.txt'}

def articles():
    result = []
    for directory in ROOT.iterdir():
        if directory.is_dir() and DIR.match(directory.name):
            for source in directory.glob('*.md'):
                match = ART.match(source.name)
                if match:
                    result.append((int(match[1]), match[1], match[2], source))
    result.sort(key=lambda item: (item[0], str(item[3])))
    return [(old, f'{index:02d}', title, source) for index, (_, old, title, source) in enumerate(result, 1)]

def mapping(items):
    return {f'{old}-{title}': f'{new}-{title}' for old, new, title, _ in items if old != new}

def xform(value, replacements):
    if not replacements:
        return value
    # Replace original identifiers in one pass so 19->18 and 18->17 never cascade.
    pattern = re.compile('|'.join(re.escape(old) for old in sorted(replacements, key=len, reverse=True)))
    return pattern.sub(lambda match: replacements[match.group(0)], value)

def planned(replacements):
    result = []
    for source in ROOT.rglob('*'):
        if not source.is_file() or '.git' in source.parts or '.tmp' in source.parts or META_DIR in source.parents:
            continue
        for old, new in replacements.items():
            stem, extension = os.path.splitext(source.name)
            if stem == old:
                result.append((source, source.with_name(new + extension)))
                break
            if source.name.startswith(old + '-'):
                result.append((source, source.with_name(new + source.name[len(old):])))
                break
    result.sort(key=lambda pair: str(pair[0]))
    return result

def table_rows(text):
    lines = text.splitlines()
    header = next(index for index, line in enumerate(lines) if line.startswith('|') and '\u7f16\u53f7' in line)
    start = header + 2
    end = start
    rows = []
    while end < len(lines) and lines[end].startswith('|'):
        cells = [cell.strip() for cell in lines[end].strip().strip('|').split('|')]
        if len(cells) >= 8 and cells[0].isdigit():
            rows.append(cells)
        end += 1
    return lines, start, end, rows

def path_cell(value):
    match = re.search(r'`([^`]+)`', value)
    return (match[1] if match else value).replace('\\', '/')

def sync_register(items):
    text = REG.read_text(encoding='utf-8')
    lines, start, end, rows = table_rows(text)
    by_path = {path_cell(row[5]): row for row in rows}
    by_title = {row[1]: row for row in rows}
    rebuilt = []
    for old, new, title, source in items:
        target_path = source.with_name(f'{new}-{title}.md').relative_to(ROOT).as_posix()
        row = by_path.get(target_path) or by_title.get(title)
        if row is None:
            raise RuntimeError('Missing asset register record: ' + target_path)
        row[0] = new
        row[1] = title
        row[5] = chr(96) + target_path + chr(96)
        rebuilt.append('| ' + ' | '.join(row) + ' |')
    first_quote = next((index for index, line in enumerate(lines) if line.startswith('> ')), 1)
    quote_end = first_quote
    while quote_end < len(lines) and lines[quote_end].startswith('> '):
        quote_end += 1
    preface = [
        f'> \u66f4\u65b0\u65f6\u95f4\uff1a{date.today().isoformat()}',
        f'> \u5f53\u524d\u6b63\u5f0f\u6587\u7ae0\uff1a{len(items)} \u7bc7\u3002',
        '> \u6b63\u5f0f\u6587\u7ae0\u7f16\u53f7\uff1a\u5220\u9664\u6216\u4e0b\u67b6\u540e\u81ea\u52a8\u8fde\u7eed\u8865\u4f4d\uff0c\u4e0d\u4fdd\u7559\u7f3a\u53f7\u3002',
        '> 下架原因与替代内容见[下架文章与替代关系](<下架文章与替代关系.md>)。'
    ]
    lines[first_quote:quote_end] = preface
    shift = len(preface) - (quote_end - first_quote)
    lines[start + shift:end + shift] = rebuilt
    REG.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8', newline='\n')

def title_replacements(items):
    """Repair auxiliary assets that still carry a retired prefix for an active title."""
    result = {}
    for source in ROOT.rglob('*'):
        if not source.is_file() or '.git' in source.parts or '.tmp' in source.parts:
            continue
        for _, article_id, title, _ in items:
            match = re.match(r'^(\d{2})-' + re.escape(title) + r'(?=$|-|\.)', source.name)
            if match and match[1] != article_id:
                result[f'{match[1]}-{title}'] = f'{article_id}-{title}'
                break
    return result

def sync_metadata(items):
    """Align metadata filenames and article identity with the canonical formal source."""
    by_title = {title: (article_id, source.with_name(f'{article_id}-{title}.md')) for _, article_id, title, source in items}
    for manifest in list(META_DIR.glob('*.json')):
        match = re.match(r'^(\d{2})-(.+)\.json$', manifest.name)
        if not match or match[2] not in by_title:
            continue
        article_id, source = by_title[match[2]]
        target_manifest = manifest.with_name(f'{article_id}-{match[2]}.json')
        if manifest != target_manifest:
            if target_manifest.exists():
                # A prior interrupted renumber may have already created the canonical copy.
                manifest.unlink()
                manifest = target_manifest
            else:
                shutil.copy2(manifest, target_manifest)
                manifest.unlink()
                manifest = target_manifest
        data = json.loads(manifest.read_text(encoding='utf-8'))
        article = data.setdefault('article', {})
        desired = {
            'id': article_id,
            'title': match[2],
            'category': source.parent.name,
            'path': source.relative_to(ROOT).as_posix(),
        }
        if any(article.get(key) != value for key, value in desired.items()):
            article.update(desired)
            manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def run(dry_run=False, check=False):
    items = articles()
    replacements = mapping(items)
    replacements.update(title_replacements(items))
    renames = planned(replacements)
    required = {source.with_name(f'{new}-{title}.md').relative_to(ROOT).as_posix() for _, new, title, source in items}
    _, _, _, rows = table_rows(REG.read_text(encoding='utf-8'))
    known = {xform(path_cell(row[5]), replacements) for row in rows}
    missing = required - known
    if missing:
        raise RuntimeError('Missing asset register records: ' + ', '.join(sorted(missing)))
    # Make a retried interrupted run idempotent: remove only byte-identical target copies.
    for source, target in renames:
        if target.exists() and target not in {item[0] for item in renames}:
            if source.read_bytes() != target.read_bytes():
                raise RuntimeError('Renumber target content conflict: ' + str(target))
            target.unlink()
    targets = [target for _, target in renames]
    sources = {source for source, _ in renames}
    if len(targets) != len(set(targets)) or any(target.exists() and target not in sources for target in targets):
        raise RuntimeError('Renumber target conflict')
    print('Plan: ' + (', '.join(f'{old}->{new}' for old, new, _, _ in items if old != new) or 'already continuous'))
    print(f'Files to rename: {len(renames)}')
    if check:
        return 1 if replacements else 0
    if dry_run:
        return 0
    for source, target in renames:
        shutil.copy2(source, target)
    if any(not target.exists() for _, target in renames):
        raise RuntimeError('Rename write failed')
    for source in ROOT.rglob('*'):
        if source.is_file() and source.suffix.lower() in TEXT and '.git' not in source.parts and '.tmp' not in source.parts:
            before = source.read_text(encoding='utf-8')
            after = xform(before, replacements)
            if after != before:
                source.write_text(after, encoding='utf-8', newline='\n')
    sync_register(items)
    sync_metadata(items)
    for source, _ in renames:
        source.unlink()
    expected = [f'{index:02d}' for index in range(1, len(items) + 1)]
    if [item[1] for item in articles()] != expected:
        raise RuntimeError('Formal article IDs are not continuous after renumber')
    print('Completed: synced formal files, assets, metadata and asset register.')
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--check', action='store_true')
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.dry_run, arguments.check))
