# -*- coding: utf-8 -*-
"""Bao cao do phu 14 truong - doc streaming tu .jsonl (nhanh, it RAM)."""
import json, os
REQ = ["name","image","product_id","market_price","price","discount_percent",
       "rating_average","sold_count","comment_count","comment_with_image_count",
       "star_breakdown","category_path","comments","stock_quantity"]
def hv(v): return len(v)>0 if isinstance(v,(list,dict)) else v is not None
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),"output")
for fname,title in [("hasaki_listing.jsonl","HASAKI listing (toan catalog)"),
                    ("hasaki_full.jsonl","HASAKI deep 14/14"),
                    ("lamthao_full.jsonl","LAMTHAO (toan bo collection)")]:
    p=os.path.join(OUT,fname)
    if not os.path.exists(p):
        print(f"\n### {title}: (chua co {fname})"); continue
    cnt=[0]*14; n=0; ids=set()
    with open(p,encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            try: d=json.loads(ln)
            except: continue
            ids.add(str(d.get("product_id"))); n+=1
            for i,k in enumerate(REQ):
                if hv(d.get(k)): cnt[i]+=1
    print(f"\n### {title} -- {n} dong / {len(ids)} SP duy nhat ({fname})")
    print("   "+" | ".join(f"{i+1}:{cnt[i]*100//n if n else 0}%" for i in range(14)))
print("\n(Cot 1..14 = 14 truong yeu cau theo thu tu)")
