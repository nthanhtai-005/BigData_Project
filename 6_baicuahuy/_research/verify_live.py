# -*- coding: utf-8 -*-
"""Kiem tra live cac endpoint (read-only GET) de xac minh cau truc that."""
import json, urllib.request, urllib.error, ssl, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"

def fetch(url, headers=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            data = r.read()
            return r.status, r.headers.get("Content-Type", ""), data
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read()
    except Exception as e:
        return None, "ERROR", str(e).encode()

def test_lamthao_product():
    print("="*80)
    print("TEST 1: Lamthao product .json")
    url = "https://lamthaocosmetics.vn/products/sua-tam-nuoc-hoa-tesori-d-oriente-bath-cream.json"
    st, ct, body = fetch(url)
    print(f"status={st} ct={ct} len={len(body)}")
    if st == 200 and b'{' in body[:5]:
        j = json.loads(body)
        p = j.get("product", j)
        print("product keys:", list(p.keys())[:25])
        v0 = p.get("variants", [{}])[0]
        print("variant[0] keys:", list(v0.keys()))
        for k in ["price", "compare_at_price", "inventory_quantity", "sku", "barcode"]:
            print(f"  variant.{k} = {v0.get(k)}")
    else:
        print("  -> Khong phai JSON / loi. Dau body:", body[:200])

def test_lamthao_collection():
    print("="*80)
    print("TEST 2: Lamthao collection products.json")
    url = "https://lamthaocosmetics.vn/collections/cham-soc-co-the/products.json?page=1&limit=3"
    st, ct, body = fetch(url)
    print(f"status={st} ct={ct} len={len(body)}")
    if st == 200 and b'{' in body[:5]:
        j = json.loads(body)
        prods = j.get("products", [])
        print(f"  so products tra ve: {len(prods)}")
        if prods:
            print("  product[0] keys:", list(prods[0].keys()))
            v0 = prods[0].get("variants",[{}])[0]
            print("  variant[0] keys:", list(v0.keys()))
            print("  variant[0].price =", v0.get("price"), " compare =", v0.get("compare_at_price"), " inv =", v0.get("inventory_quantity"))
    else:
        print("  -> body:", body[:200])

def test_lamthao_collections_list():
    print("="*80)
    print("TEST 3: Lamthao collections.json (danh sach collection)")
    url = "https://lamthaocosmetics.vn/collections.json?limit=5"
    st, ct, body = fetch(url)
    print(f"status={st} ct={ct} len={len(body)}")
    if st == 200 and b'{' in body[:5]:
        j = json.loads(body)
        cols = j.get("collections", [])
        print(f"  so collections: {len(cols)}")
        for c in cols[:5]:
            print(f"   - {c.get('handle')}  id={c.get('id')}  title={c.get('title')}")
    else:
        print("  -> body:", body[:200])

def test_hasaki():
    print("="*80)
    print("TEST 4: Hasaki listing API (voi header mobiledeviceid)")
    url = "https://hasaki.vn/mobile/v3/main/products?cate_path=cham-soc-da-mat-c4&page=1&size=3&has_meta_data=1&is_desktop=1"
    headers = {
        "Referer": "https://hasaki.vn/danh-muc/cham-soc-da-mat-c4.html",
        "mobiledeviceid": "60fff625-b379-42fa-a60e-f13760c01174",
    }
    st, ct, body = fetch(url, headers)
    print(f"status={st} ct={ct} len={len(body)}")
    if st == 200 and b'{' in body[:5]:
        j = json.loads(body)
        print("  status.error_code =", j.get("status", {}).get("error_code"))
        prods = j.get("data", {}).get("products", [])
        print(f"  so products: {len(prods)}")
        if prods:
            p = prods[0]
            print("  product[0].id =", p.get("id"), " name =", str(p.get("name"))[:40])
            print("  market_price =", p.get("market_price"), " price =", p.get("price"), " discount% =", p.get("discount_percent"))
            print("  quantity =", p.get("quantity"), " bought_count =", p.get("bought_count"))
            print("  rating =", p.get("rating"))
    else:
        print("  -> body:", body[:300])

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all","1"): test_lamthao_product()
    if which in ("all","2"): test_lamthao_collection()
    if which in ("all","3"): test_lamthao_collections_list()
    if which in ("all","4"): test_hasaki()
