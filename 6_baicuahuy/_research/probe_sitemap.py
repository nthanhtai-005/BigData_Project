# -*- coding: utf-8 -*-
import urllib.request, ssl, re, gzip
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/149 Safari/537.36"
def fetch(url):
    try:
        req=urllib.request.Request(url, headers={"User-Agent":UA})
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            d=r.read()
            if r.headers.get("Content-Encoding")=="gzip" or url.endswith(".gz"):
                try: d=gzip.decompress(d)
                except: pass
            return r.status, d.decode("utf-8","replace")
    except Exception as e:
        return None, str(e)

for u in ["https://lamthaocosmetics.vn/sitemap.xml"]:
    st,t=fetch(u)
    print(f"=== {u} -> {st} ===")
    if st==200:
        locs=re.findall(r"<loc>(.*?)</loc>", t)
        print(f"  {len(locs)} <loc>:")
        for l in locs[:20]: print("   ", l)

# product sitemap (thu vai bien the ten)
for u in ["https://lamthaocosmetics.vn/sitemap_products_1.xml",
          "https://lamthaocosmetics.vn/sitemap_products_1.xml?from=1&to=100000",
          "https://lamthaocosmetics.vn/sitemap_collections_1.xml"]:
    st,t=fetch(u)
    print(f"\n=== {u} -> {st} ===")
    if st==200:
        prod=re.findall(r"/products/([a-z0-9\-]+)", t)
        col=re.findall(r"/collections/([a-z0-9\-]+)", t)
        print(f"  products handles = {len(set(prod))} | collections handles = {len(set(col))}")
        ex = sorted(set(prod))[:5] if prod else sorted(set(col))[:8]
        print("  vi du:", ex)
