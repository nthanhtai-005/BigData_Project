#!/usr/bin/env python3
import sys

for line in sys.stdin:
    line = line.strip()
    parts = line.split('\t')
    
    if len(parts) > 13:
        source_name = parts[4].strip().lower()
        
        if source_name in ['hasaki', 'lamthao']:
            brand_name = parts[6].strip()
            
            if not brand_name or brand_name.lower() == 'no brand':
                continue
                
            try:
                price = float(parts[8])
                sold_count = int(float(parts[13])) 
                print(f"{brand_name}\t{source_name},{price},{sold_count}")
            except ValueError:
                continue