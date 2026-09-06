#!/usr/bin/env python3
"""Audit copying and attribution offline, on either supported database schema.

    uv run scripts/revision_audit.py
    uv run scripts/revision_audit.py --db /path/to/upstream.db

Counts editor labels, not authenticated agents. Emits metrics and revision IDs,
never raw bodies or credentials. Does not access external services.
"""
import argparse
import collections
import difflib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote


def audit(path):
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    columns = {r['name'] for r in con.execute('PRAGMA table_info(revisions)')}
    rid, base = ('rev_id', 'diff_base') if 'rev_id' in columns else ('revision_id', 'diff_base_revision_id')
    rows = [dict(r) for r in con.execute('SELECT * FROM revisions ORDER BY time')]
    by_id = {r[rid]: r for r in rows}
    loop = [r for r in rows if re.fullmatch(r'dse~LoopNextWord\d+', r['page_key'])]
    heads = {r['page_key']: r for r in loop}
    digest, count = collections.Counter(r['body_sha256'] for r in heads.values()).most_common(1)[0]
    clones = [r for r in rows if r['body_sha256'] == digest]
    family_clones = [r for r in loop if r['body_sha256'] == digest]
    edges = set()
    for r in loop:
        body = r['body']
        for _ in range(4):
            body = unquote(body)
        for target in re.findall(r'LoopNextWord\d+', body):
            if 'dse~' + target != r['page_key']:
                edges.add((r['page_key'], target))
    matching = [r for r in rows if 'mileshilliard' in r['body'].lower()]
    introductions = []
    for r in matching:
        old = by_id.get(r[base], {}).get('body', '')
        delta = difflib.ndiff(old.splitlines(), r['body'].splitlines())
        if any(s.startswith('+ ') and 'mileshilliard' in s.lower() for s in delta):
            introductions.append(r[rid])
    encoding = []
    recovered = []
    for seq in range(14, 21):
        r = by_id[f'dse~DataUSAClothingStateSequenceCollabOct10@{seq}']
        line = next(s for s in r['body'].splitlines() if 'wording was exactly' in s)
        text, depth = line, 0
        while depth < 20:
            try:
                fixed = text.encode('latin1').decode('utf8')
            except UnicodeError:
                break
            if fixed == text:
                break
            text, depth = fixed, depth + 1
        recovered.append(text)
        encoding.append({'revision_id': r[rid], 'layers': depth, 'characters': len(line)})
    def span(items):
        first, last = items[0]['time'], items[-1]['time']
        return {'first': first, 'last': last, 'seconds': int((datetime.fromisoformat(last.replace('Z', '+00:00')) - datetime.fromisoformat(first.replace('Z', '+00:00'))).total_seconds())}
    result = {
        'revisions': len(rows),
        'loop_pages': len(heads), 'loop_revisions': len(loop),
        'loop_distinct_bodies': len({r['body_sha256'] for r in loop}),
        'loop_identical_heads': count, 'loop_cross_node_references': len(edges),
        'loop_clone_window': span(family_clones),
        'all_clone_pages': len({r['page_key'] for r in clones}),
        'all_clone_labels': len({r['label'] for r in clones}),
        'all_clone_window': span(clones),
        'counter_matching_revisions': len(matching),
        'counter_editor_labels': len({r['label'] for r in matching}),
        'counter_introductions': introductions,
        'encoding_trail': encoding, 'encoding_recovers_identical_text': len(set(recovered)) == 1,
        'gzip_prose_revisions': sum('gzip' in r['body'].lower() for r in rows),
    }
    con.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=Path(__file__).resolve().parents[1] / 'data/collusion-wiki.db')
    args = parser.parse_args()
    print(json.dumps(audit(args.db), indent=2))


if __name__ == '__main__':
    main()
