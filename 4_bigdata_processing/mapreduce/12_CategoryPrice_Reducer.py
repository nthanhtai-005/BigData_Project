#!/usr/bin/env python3
import sys

current_category = None
sum_price = 0.0
sum_market_price = 0.0
count = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
        
    try:
        category, values = line.split('\t', 1)
        p, m, c = map(float, values.split(','))
    except ValueError:
        continue

    if current_category == category:
        sum_price += p
        sum_market_price += m
        count += int(c)
    else:
        if current_category and count > 0:
            avg_price = sum_price / count
            avg_market = sum_market_price / count
            print(f"{current_category},{avg_price:.2f},{avg_market:.2f}")
        
        current_category = category
        sum_price = p
        sum_market_price = m
        count = int(c)

if current_category and count > 0:
    avg_price = sum_price / count
    avg_market = sum_market_price / count
    print(f"{current_category},{avg_price:.2f},{avg_market:.2f}")