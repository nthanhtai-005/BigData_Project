# -*- coding: utf-8 -*-
import json, urllib.request, ssl, re
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/149 Safari/537.36"
def fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        return r.status, r.read()

# 1) /products.json toàn store
print("=== /products.json (toan store) ===")
st, b = fetch("https://lamthaocosmetics.vn/products.json?page=1&limit=250")
j = json.loads(b)
prods = j.get("products", [])
print("status", st, "| so SP trang 1 =", len(prods))
print("product[0] keys:", list(prods[0].keys()) if prods else None)
# co inventory_quantity + sole_quantity khong?
if prods:
    v = prods[0].get("variants",[{}])[0]
    print("  variant keys:", [k for k in v.keys()])
    print("  inventory_quantity:", v.get("inventory_quantity"), "| price:", v.get("price"))
    print("  sole_quantity:", prods[0].get("sole_quantity"))

# 2) Đếm tổng số SP qua phân trang nhanh (chỉ đếm vài trang đầu để ước lượng)
print("\n=== Uoc luong tong so trang /products.json ===")
total = 0; page=1
while page<=40:
    st,b=fetch(f"https://lamthaocosmetics.vn/products.json?page={page}&limit=250")
    n=len(json.loads(b).get("products",[]))
    total+=n
    if n<250: 
        print(f"  trang {page}: {n} (trang cuoi)"); break
    page+=1
print("  TONG SP toan store (uoc luong) =", total, "qua", page, "trang")

# 3) sitemap collections
print("\n=== sitemap collections ===")
try:
    st,b=fetch("https://lamthaocosmetics.vn/sitemap_collections_1.xml")
    txt=b.decode("utf-8","replace")
    handles=re.findall(r"/collections/([a-z0-9\-]+)", txt)
    print("status",st,"| so collection trong sitemap =", len(set(handles)))
    print("  vai vi du:", sorted(set(handles))[:10])
except Exception as e:
    print("  sitemap_collections loi:", e)
