#!/usr/bin/env python3
import sys

current_brand = None
total_sold = 0
shop_data = {
    'hasaki': {'sum_price': 0.0, 'count': 0},
    'lamthao': {'sum_price': 0.0, 'count': 0}
}

def print_brand_result():
    if shop_data['hasaki']['count'] > 0 and shop_data['lamthao']['count'] > 0:
        avg_price_hasaki = shop_data['hasaki']['sum_price'] / shop_data['hasaki']['count']
        avg_price_lamthao = shop_data['lamthao']['sum_price'] / shop_data['lamthao']['count']
        
        print(f"{current_brand},{avg_price_hasaki:.2f},{avg_price_lamthao:.2f},{total_sold}")

for line in sys.stdin:
    line = line.strip()
    try:
        brand, values = line.split('\t', 1)
        source, price, sold = values.split(',')
        price = float(price)
        sold = int(sold)
    except ValueError:
        continue

    shop_key = 'hasaki' if 'hasaki' in source else 'lamthao'

    if current_brand == brand:
        shop_data[shop_key]['sum_price'] += price
        shop_data[shop_key]['count'] += 1
        total_sold += sold
    else:
        if current_brand:
            print_brand_result()
            
        current_brand = brand
        total_sold = sold
        shop_data = {
            'hasaki': {'sum_price': 0.0, 'count': 0},
            'lamthao': {'sum_price': 0.0, 'count': 0}
        }
        shop_data[shop_key]['sum_price'] += price
        shop_data[shop_key]['count'] += 1

if current_brand:
    print_brand_result()