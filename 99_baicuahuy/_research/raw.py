# -*- coding: utf-8 -*-
import json, sys
path, substr = sys.argv[1], sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
length = int(sys.argv[4]) if len(sys.argv) > 4 else 2000
idx = int(sys.argv[5]) if len(sys.argv) > 5 else 0
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
matches = [r for r in data['records'] if substr in r.get('url','')]
body = matches[idx].get('responseBody') or ''
print(f"URL: {matches[idx]['url']}")
print(f"LEN: {len(body)}")
print('='*80)
print(body[start:start+length])
