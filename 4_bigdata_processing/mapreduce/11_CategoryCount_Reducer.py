#!/usr/bin/env python3
import sys

current_category = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    
    try:
        category, count = line.split('\t', 1)
        count = int(count)
    except ValueError:
        continue
        
    if current_category == category:
        current_count += count
    else:
        if current_category:
            print(f"{current_category},{current_count}")
        current_category = category
        current_count = count

if current_category:
    print(f"{current_category},{current_count}")