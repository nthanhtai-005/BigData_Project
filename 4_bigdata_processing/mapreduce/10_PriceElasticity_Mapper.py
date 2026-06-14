#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    cols = line.split('\t')
    
    # Kiem tra do dai de tranh loi index
    if len(cols) > 15:
        try:
            # Gia thuc te nam o cot index 8, luong ban o index 13
            price = float(cols[8])
            sold_count = int(cols[13])
            
            # Gan tien to 1_, 2_, 3_ de Hadoop Sort tang dan chuan xac
            if price < 100000:
                bucket = "1_<100k"
            elif price <= 300000:
                bucket = "2_100k-300k"
            elif price <= 500000:
                bucket = "3_300k-500k"
            elif price <= 1000000:
                bucket = "4_500k-1M"
            else:
                bucket = "5_>1M"
                
            print(f"{bucket}\t{sold_count}")
            
        except ValueError:
            pass