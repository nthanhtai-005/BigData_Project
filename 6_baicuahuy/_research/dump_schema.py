# -*- coding: utf-8 -*-
"""Dump schema (cay khoa + kieu + gia tri mau) cho 1 endpoint cu the."""
import json, os, sys

def short(v):
    if isinstance(v, str):
        s = v.replace('\n', ' ')
        return '"' + (s[:60] + ('...' if len(s) > 60 else '')) + '"'
    return repr(v)

def walk(obj, prefix='', depth=0, maxdepth=6, seen_lists=None):
    lines = []
    if depth > maxdepth:
        return lines
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                lines.append(f'{p}  (object, {len(v)} keys)')
                lines += walk(v, p, depth+1, maxdepth)
            elif isinstance(v, list):
                lines.append(f'{p}  (array, len={len(v)})')
                if v:
                    # chi xet phan tu dau tien
                    if isinstance(v[0], (dict, list)):
                        lines += walk(v[0], p+'[0]', depth+1, maxdepth)
                    else:
                        lines.append(f'{p}[0] = {short(v[0])}')
            else:
                lines.append(f'{p} = {short(v)}')
    elif isinstance(obj, list):
        lines.append(f'{prefix}  (array, len={len(obj)})')
        if obj and isinstance(obj[0], (dict, list)):
            lines += walk(obj[0], prefix+'[0]', depth+1, maxdepth)
    return lines

def find_records(path, url_substr, want_index=0):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    matches = [r for r in data['records'] if url_substr in r.get('url','')]
    print(f"### Tim '{url_substr}': {len(matches)} record(s)")
    for i, r in enumerate(matches):
        print(f"  [{i}] {r['method']} status={r['status']} bodyLen={len(r.get('responseBody') or '')}")
        print(f"      URL: {r['url']}")
    if not matches:
        return None
    return matches[want_index]

if __name__ == '__main__':
    path = sys.argv[1]
    substr = sys.argv[2]
    idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    maxd = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    r = find_records(path, substr, idx)
    if r is None:
        sys.exit(0)
    print('\n' + '='*90)
    print('FULL URL:', r['url'])
    print('='*90)
    body = r.get('responseBody') or ''
    try:
        j = json.loads(body)
    except Exception as e:
        print('KHONG PHAI JSON:', e)
        print(body[:2000])
        sys.exit(0)
    for line in walk(j, '', 0, maxd):
        print(line)
