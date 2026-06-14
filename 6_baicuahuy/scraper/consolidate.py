# -*- coding: utf-8 -*-
"""
consolidate.py — Hợp nhất dữ liệu Hasaki + Lamthao thành MỘT dataset thống nhất:
  - output/all_products.json   (mảng tất cả sản phẩm, schema thống nhất)
  - output/all_products.csv    (bảng phẳng, mở Excel)
  - output/all_products.sqlite (CSDL SQLite: bảng `products` + index, sẵn sàng truy vấn)

Nguồn ưu tiên (đầy đủ nhất), đọc streaming từ .jsonl:
  - Hasaki : hasaki_full.jsonl  (deep 14/14)  -> fallback hasaki_listing.jsonl
  - Lamthao: lamthao_full.jsonl

Dùng: python consolidate.py
"""
import json, os, csv, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

# Cột phẳng cho CSV + SQLite (vô hướng); phần lồng nhau lưu dạng JSON text.
FLAT = ["source", "product_id", "sku", "name", "english_name", "brand", "brand_id",
        "url", "handle", "image", "num_images",
        "market_price", "price", "discount_percent", "has_voucher", "voucher_text",
        "price_min", "price_max", "rating_average", "sold_count", "sold_count_30d",
        "comment_count", "comment_with_image_count", "review_count",
        "category_path", "product_type", "tags", "stock_quantity", "num_variants",
        "promotion_text", "announce_number", "available",
        "crawl_category_key", "crawl_category_name", "scraped_at"]
JSON_COLS = ["star_breakdown", "images", "variants", "reviews", "comments",
             "category_breadcrumb", "data_availability"]


def iter_jsonl(fname):
    p = os.path.join(OUT, fname)
    if not os.path.exists(p):
        return
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    yield json.loads(ln)
                except json.JSONDecodeError:
                    continue


def flat_row(d):
    row = {c: d.get(c) for c in FLAT}
    row["num_images"] = len(d.get("images") or [])
    row["num_variants"] = len(d.get("variants") or [])
    row["tags"] = "|".join(d.get("tags") or []) if d.get("tags") else None
    row["has_voucher"] = 1 if d.get("has_voucher") else (0 if d.get("has_voucher") is not None else None)
    row["available"] = 1 if d.get("available") else (0 if d.get("available") is not None else None)
    return row


def collect():
    """Gộp theo (source, product_id). Đọc nguồn ĐẦY ĐỦ trước -> giữ bản đầu (nhanh)."""
    merged = {}
    order = []
    sources = ["hasaki_full.jsonl",     # deep 14/14 (ưu tiên)
               "hasaki_listing.jsonl",  # bổ sung SP chỉ có ở listing
               "lamthao_full.jsonl"]
    for fname in sources:
        for d in iter_jsonl(fname):
            key = (d.get("source"), str(d.get("product_id")))
            if key not in merged:        # giữ bản gặp đầu tiên (nguồn đầy đủ đọc trước)
                merged[key] = d
                order.append(key)
    return [merged[k] for k in order]


def main():
    rows = collect()
    print(f"Tổng sản phẩm hợp nhất: {len(rows)}")
    by_src = {}
    for d in rows:
        by_src[d.get("source")] = by_src.get(d.get("source"), 0) + 1
    for s, n in by_src.items():
        print(f"  - {s}: {n}")

    # 1) JSON
    pj = os.path.join(OUT, "all_products.json")
    with open(pj, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print(f"-> {pj}")

    # 2) CSV
    pc = os.path.join(OUT, "all_products.csv")
    with open(pc, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FLAT, extrasaction="ignore")
        w.writeheader()
        for d in rows:
            w.writerow(flat_row(d))
    print(f"-> {pc}")

    # 3) SQLite
    ps = os.path.join(OUT, "all_products.sqlite")
    if os.path.exists(ps):
        os.remove(ps)
    con = sqlite3.connect(ps)
    cur = con.cursor()
    INT_COLS = {"product_id", "brand_id", "num_images", "market_price", "price",
                "discount_percent", "price_min", "price_max", "sold_count",
                "sold_count_30d", "comment_count", "comment_with_image_count",
                "review_count", "stock_quantity", "num_variants", "has_voucher", "available"}
    REAL_COLS = {"rating_average"}

    def coltype(c):
        if c in INT_COLS:
            return "INTEGER"
        if c in REAL_COLS:
            return "REAL"
        return "TEXT"

    cols_def = ", ".join(f'"{c}" {coltype(c)}' for c in FLAT)
    json_def = ", ".join(f'"{c}" TEXT' for c in JSON_COLS)
    cur.execute(f'CREATE TABLE products ({cols_def}, {json_def}, '
                f'PRIMARY KEY (source, product_id))')
    # chèn
    allcols = FLAT + JSON_COLS
    ph = ", ".join("?" for _ in allcols)
    qcols = ", ".join(f'"{c}"' for c in allcols)
    ins = f'INSERT OR REPLACE INTO products ({qcols}) VALUES ({ph})'
    for d in rows:
        fr = flat_row(d)
        vals = [fr.get(c) for c in FLAT]
        for c in JSON_COLS:
            v = d.get(c)
            vals.append(json.dumps(v, ensure_ascii=False) if v not in (None, [], {}) else None)
        cur.execute(ins, vals)
    for idx in ["source", "brand", "category_path", "price", "sold_count",
                "rating_average", "discount_percent"]:
        cur.execute(f'CREATE INDEX idx_{idx} ON products("{idx}")')
    con.commit()

    # vài truy vấn minh hoạ
    print(f"-> {ps}")
    print("\n--- Kiểm chứng SQLite ---")
    cur.execute("SELECT source, COUNT(*) FROM products GROUP BY source")
    for s, n in cur.fetchall():
        print(f"  {s}: {n} SP")
    cur.execute("SELECT name, sold_count FROM products WHERE source='hasaki' "
                "ORDER BY sold_count DESC LIMIT 3")
    print("  Top bán chạy Hasaki:")
    for name, sc in cur.fetchall():
        print(f"    {sc} | {str(name)[:50]}")
    con.close()
    print("\nVí dụ truy vấn:")
    print('  SELECT brand, COUNT(*) n, AVG(price) FROM products GROUP BY brand ORDER BY n DESC;')
    print('  SELECT name,price,discount_percent FROM products WHERE discount_percent>=50 ORDER BY sold_count DESC;')


if __name__ == "__main__":
    main()
