#!/usr/bin/env python3
import sys

current_category = None
total_products = 0
total_oos = 0

# In ra header cho file CSV output
print("category_name,total_products,total_oos,oos_rate_percent")

for line in sys.stdin:
    line = line.strip()
    
    try:
        # Tach Key va Value
        category, value = line.split('\t', 1)
        # Tach tiep Value de lay is_oos va count
        oos_str, count_str = value.split(',')
        oos = int(oos_str)
        count = int(count_str)
    except ValueError:
        continue

    # Neu dang doc cung mot category, tiep tuc cong don
    if current_category == category:
        total_products += count
        total_oos += oos
    else:
        # Neu chuyen sang category moi, in ra ket qua cua category cu
        if current_category:
            oos_rate = (total_oos / total_products) * 100
            print(f"{current_category},{total_products},{total_oos},{oos_rate:.2f}")
        
        # Reset lai bien cho category moi
        current_category = category
        total_products = count
        total_oos = oos

# Dung quen in ra category cuoi cung sau khi thoat vong lap
if current_category == category:
    oos_rate = (total_oos / total_products) * 100
    print(f"{current_category},{total_products},{total_oos},{oos_rate:.2f}")