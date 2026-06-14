#!/usr/bin/env python3
import sys

for line in sys.stdin:
    # Xoa khoang trang/xuong dong o 2 dau
    line = line.strip()
    
    # Tach du lieu dua tren ky tu Tab
    cols = line.split('\t')
    
    # Kiem tra xem dong co du so luong cot hay khong (dam bao khong bi loi index)
    if len(cols) > 15:
        try:
            category_name = cols[5]
            # Lay so luong ton kho o cot index 14
            stock_quantity = int(cols[14])
            
            # Gan co is_oos (1 neu het hang, 0 neu con hang)
            is_oos = 1 if stock_quantity == 0 else 0
            
            # Xuat Key (category_name) va Value (is_oos, 1) phan cach bang Tab
            print(f"{category_name}\t{is_oos},1")
        except ValueError:
            # Bo qua cac dong bi loi parse so (vi du dong header neu co)
            pass