#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    
    parts = line.split('\t')
    
    if len(parts) > 5:
        category_name = parts[5].strip()
        if category_name:
            print(f"{category_name}\t1")