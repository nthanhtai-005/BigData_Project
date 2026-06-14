# -*- coding: utf-8 -*-
"""Kiem tra bo sung: sole_quantity Lamthao + Hasaki detail/comments/rating-reviews."""
import json, urllib.request, urllib.error, ssl, sys

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"

def fetch(url, headers=None, timeout=25):
    h = {"User-Agent": UA, "Accept":"application/json, text/plain, */*"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()

# 1) sole_quantity cua san pham co sold=48949, inv=7331
print("="*80); print("Lamthao product.json -> sole_quantity & tong inventory")
st, body = fetch("https://lamthaocosmetics.vn/products/sua-tam-nuoc-hoa-tesori-d-oriente-bath-cream.json")
if st==200:
    p = json.loads(body)["product"]
    print("  sole_quantity =", p.get("sole_quantity"))
    print("  product.available =", p.get("available"))
    invs = [(v.get("title"), v.get("price"), v.get("compare_at_price"), v.get("inventory_quantity")) for v in p["variants"]]
    print("  variants (title, price, compare, inv):")
    for x in invs: print("    ", x)
    print("  tong inventory cac variant =", sum(v.get("inventory_quantity") or 0 for v in p["variants"]))

H = {"Referer":"https://hasaki.vn/","mobiledeviceid":"60fff625-b379-42fa-a60e-f13760c01174"}
# 2) Hasaki detail
print("="*80); print("Hasaki detail live")
st, body = fetch("https://hasaki.vn/mobile/v3/detail/product?product_id=102959&is_desktop=1", H)
print("  status=", st, "len=", len(body))
if st==200:
    j = json.loads(body)
    cd = j["data"]["blocks"][0]["common_data"]
    print("  name=", cd.get("name")[:40])
    print("  comment.total=", cd.get("comment"))
    print("  rating=", cd.get("rating"))
    print("  price_detail.coupons=", cd.get("price_detail",{}).get("coupons"))

# 3) Hasaki rating-reviews
print("="*80); print("Hasaki rating-reviews live")
st, body = fetch("https://hasaki.vn/mobile/v3/detail/product/rating-reviews?product_id=102959&page=1&size=2&sort=create&filter=filter_all&is_desktop=1", H)
print("  status=", st, "len=", len(body))
if st==200:
    j = json.loads(body)
    print("  stars=", [(s["star"],s["count"]) for s in j["data"]["rating"]["stars"]])
    print("  filters=", [(f["key"],f["count"]) for f in j["data"]["rating"]["filter"]])
    print("  total reviews=", j["data"].get("total"))

# 4) Hasaki comments
print("="*80); print("Hasaki comments live")
st, body = fetch("https://hasaki.vn/mobile/v1/detail/product/comments?product_id=102959&page=1&size=2", H)
print("  status=", st, "len=", len(body))
if st==200:
    j = json.loads(body)
    print("  comments_total=", j["data"]["meta_data"]["comments_total"])
    print("  so comment tra ve=", len(j["data"]["comments"]))
