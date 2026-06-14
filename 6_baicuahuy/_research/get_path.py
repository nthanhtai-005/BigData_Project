# -*- coding: utf-8 -*-
"""Trich xuat gia tri raw tai duong dan cu the trong response cua 1 endpoint."""
import json, sys

def get_path(obj, path):
    cur = obj
    for seg in path.split('.'):
        if seg == '':
            continue
        if '[' in seg:
            name, idx = seg[:-1].split('[')
            if name:
                cur = cur[name]
            cur = cur[int(idx)]
        else:
            cur = cur[seg]
    return cur

if __name__ == '__main__':
    path, substr, jsonpath = sys.argv[1], sys.argv[2], sys.argv[3]
    idx = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    matches = [r for r in data['records'] if substr in r.get('url','')]
    r = matches[idx]
    j = json.loads(r['responseBody'])
    val = get_path(j, jsonpath)
    print(json.dumps(val, ensure_ascii=False, indent=2)[:4000])
