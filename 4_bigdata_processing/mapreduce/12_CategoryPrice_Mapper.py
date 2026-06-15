#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    
    parts = line.split('\t')
    
    if len(parts) > 9:
        category_name = parts[5].strip()
        try:
            price = float(parts[8])
            market_price = float(parts[9])
            print(f"{category_name}\t{price},{market_price},1")
        except ValueError:
            continue