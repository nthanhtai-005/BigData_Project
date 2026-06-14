# -*- coding: utf-8 -*-
"""Trich JSON nhung (meta, product data) + sold count + rating tu HTML Lamthao."""
import re, json, sys

def extract_balanced(text, start_idx):
    """Trich object JSON can bang dau { } bat dau tu start_idx (vi tri '{')."""
    depth = 0
    in_str = False
    esc = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == '\\':
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]
    return None

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()
print(f"FILE LEN: {len(html)}")

# 1) var meta = {...}
m = re.search(r'var meta\s*=\s*\{', html)
if m:
    obj = extract_balanced(html, m.end()-1)
    try:
        j = json.loads(obj)
        print("\n===== META =====")
        print(json.dumps(j, ensure_ascii=False, indent=2)[:1500])
    except Exception as e:
        print("meta parse err", e)

# 2) data: {...} (product object) - tim "available":true gan dau
m = re.search(r'data:\s*\{"available"', html)
if m:
    obj = extract_balanced(html, m.end()-len('{"available"'))
    if obj:
        try:
            j = json.loads(obj)
            print("\n===== PRODUCT DATA (keys) =====")
            print("KEYS:", list(j.keys()))
            # variants
            if 'variants' in j and j['variants']:
                print("\n-- variant[0] --")
                print(json.dumps(j['variants'][0], ensure_ascii=False, indent=2))
                print(f"\nTONG SO VARIANTS: {len(j['variants'])}")
            for k in ['id','title','price','compare_at_price','vendor','type','tags','available','sold','published_at','created_at']:
                if k in j:
                    v = j[k]
                    if isinstance(v,str) and len(v)>80: v=v[:80]+'...'
                    print(f"  {k} = {v}")
            if 'images' in j:
                print(f"  images count = {len(j['images'])}")
                if j['images']:
                    print(f"  images[0] = {j['images'][0]}")
            if 'options' in j:
                print(f"  options = {j.get('options')}")
        except Exception as e:
            print("data parse err", e)
            print(obj[:500])

# 3) Sold count "Đã bán N"
solds = re.findall(r'Đã bán\s*([\d.,]+)', html)
print(f"\n===== SOLD COUNTS tim thay: {len(solds)} =====")
print("Cac gia tri (10 dau):", solds[:10])

# 4) Rating / review markers
for marker in ['rating','review','star','sao','đánh giá','vote','Đã bán','aggregateRating']:
    cnt = len(re.findall(re.escape(marker), html, re.IGNORECASE))
    if cnt:
        print(f"  marker '{marker}': {cnt}")
