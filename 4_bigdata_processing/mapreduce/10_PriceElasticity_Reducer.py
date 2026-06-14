#!/usr/bin/env python3
import sys

current_bucket = None
total_sold = 0

# In header cho CSV
print("price_bucket,total_sold_volume")

for line in sys.stdin:
    line = line.strip()
    try:
        bucket, count_str = line.split('\t', 1)
        count = int(count_str)
    except ValueError:
        continue

    if current_bucket == bucket:
        total_sold += count
    else:
        if current_bucket:
            # Boc tien to 1_, 2_ ra khoi ten bucket truoc khi in
            clean_bucket = current_bucket.split('_', 1)[1]
            print(f"{clean_bucket},{total_sold}")
            
        current_bucket = bucket
        total_sold = count

if current_bucket == bucket:
    clean_bucket = current_bucket.split('_', 1)[1]
    print(f"{clean_bucket},{total_sold}")