# -*- coding: utf-8 -*-
"""Phan tich file API capture de hieu cau truc endpoint."""
import json, sys, os
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

def strip_path(url):
    """Bo phan query, gom nhom theo path co thay so bang {id}."""
    p = urlparse(url)
    host = p.netloc
    parts = []
    for seg in p.path.split('/'):
        if seg.isdigit():
            parts.append('{id}')
        else:
            parts.append(seg)
    return host + '/'.join(parts)

def analyze(path, label):
    print('='*100)
    print(f'FILE: {label}  ->  {path}')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    records = data.get('records', [])
    print(f"exportedAt={data.get('exportedAt')}  total={data.get('total')}  len(records)={len(records)}")

    groups = defaultdict(list)
    for r in records:
        url = r.get('url', '')
        key = strip_path(url)
        groups[key].append(r)

    print(f"\nSO NHOM ENDPOINT: {len(groups)}\n")
    # Sap xep theo so luong giam dan
    for key in sorted(groups, key=lambda k: -len(groups[k])):
        recs = groups[key]
        sample = recs[0]
        ct = sample.get('contentType', '') or ''
        status = sample.get('status')
        sizes = [len(r.get('responseBody') or '') for r in recs]
        avg = sum(sizes)//len(sizes) if sizes else 0
        method = sample.get('method')
        print(f"[{len(recs):3d}x] {method:4s} {status} ct={ct[:30]:30s} avgBody={avg:8d}  {key}")

    return data, records, groups

if __name__ == '__main__':
    base = r'D:\Learning\Nhap_moi_big_data\Test\Data_Research'
    hasaki = os.path.join(base, 'Hasaki', 'API', 'api-capture-2026-06-09_00-49-37-091.json')
    lamthao = os.path.join(base, 'Lamthao', 'API', 'api-capture-2026-06-09_00-51-30-710.json')
    analyze(hasaki, 'HASAKI')
    analyze(lamthao, 'LAMTHAO')
