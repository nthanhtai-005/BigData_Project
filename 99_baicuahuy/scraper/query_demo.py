# -*- coding: utf-8 -*-
import sqlite3, os
db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "all_products.sqlite")
c = sqlite3.connect(db); cur = c.cursor()
print("--- Thong ke theo nguon ---")
for s, n, ap, dp, ar in cur.execute("SELECT source,COUNT(*),AVG(price),AVG(discount_percent),AVG(rating_average) FROM products GROUP BY source"):
    print(f"  {s}: {n} SP | gia TB={int(ap or 0):,}d | giam TB={dp or 0:.0f}% | sao TB={ar or 0:.2f}")
print("--- Top 5 thuong hieu ---")
for b, n in cur.execute("SELECT brand,COUNT(*) n FROM products WHERE brand IS NOT NULL AND brand!='' GROUP BY brand ORDER BY n DESC LIMIT 5"):
    print(f"  {n}  {b}")
print("--- Tong ton kho va luot ban ---")
for s, stock, sold in cur.execute("SELECT source,SUM(stock_quantity),SUM(sold_count) FROM products GROUP BY source"):
    print(f"  {s}: ton_kho={int(stock or 0):,} | luot_ban={int(sold or 0):,}")
c.close()
