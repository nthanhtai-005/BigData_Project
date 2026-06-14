# -*- coding: utf-8 -*-
"""Tim cac dau hieu nen tang + JSON nhung trong HTML cua Lamthao."""
import json, sys, re

path = sys.argv[1]
substr = sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
matches = [r for r in data['records'] if substr in r.get('url','')]
print(f"Tim '{substr}': {len(matches)} record(s)")
if not matches:
    sys.exit(0)
body = matches[0].get('responseBody') or ''
print(f"URL: {matches[0]['url']}  len={len(body)}")
print('='*80)

# Cac dau hieu nen tang
markers = ['haravan', 'Haravan', 'shopify', 'Shopify', 'compare_at_price',
           'application/ld+json', 'var product', 'window.product', 'productJson',
           'spr-badge', 'product-reviews', 'judgeme', 'review', 'rating',
           'available', 'inventory_quantity', 'variants', 'BoldApps',
           'data-product-json', 'ProductJson', 'og:', 'sold', 'da ban']
for m in markers:
    cnt = body.count(m)
    if cnt:
        print(f"  '{m}': {cnt}")
