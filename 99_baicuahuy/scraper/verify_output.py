# -*- coding: utf-8 -*-
"""
Kiểm thử output: đo độ phủ 14 trường yêu cầu + đối chiếu vài giá trị đã biết
từ nghiên cứu (RESEARCH.md) để chứng minh tính đúng đắn.
"""
import json, sys, os, glob

REQUIRED = [
    ("name", "1 Tên"), ("image", "2 Ảnh"), ("product_id", "3 ID"),
    ("market_price", "4 Giá gốc"), ("price", "5 Giá bán"),
    ("discount_percent", "6 Voucher %"), ("rating_average", "7 Sao"),
    ("sold_count", "8 Lượt bán"), ("comment_count", "9 Số comment"),
    ("comment_with_image_count", "10 Comment có ảnh"), ("star_breakdown", "11 Phân bố sao"),
    ("category_path", "12 Danh mục"), ("comments", "13 Comment"), ("stock_quantity", "14 Tồn kho"),
]

def has_val(v):
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return v is not None

def latest(site, out_dir):
    files = sorted(glob.glob(os.path.join(out_dir, f"{site}_*.json")))
    return files[-1] if files else None

def check(path):
    with open(path, encoding="utf-8") as f:
        prods = json.load(f)
    print(f"\n=== {os.path.basename(path)} — {len(prods)} sản phẩm ===")
    n = len(prods)
    print(f"{'Trường':28s} | {'Có dữ liệu':>10s} | %")
    print("-" * 50)
    for key, label in REQUIRED:
        c = sum(1 for p in prods if has_val(p.get(key)))
        pct = (c / n * 100) if n else 0
        flag = "" if c else "  <-- KHÔNG có (nguồn thiếu)"
        print(f"{label:28s} | {c:>4}/{n:<4} | {pct:5.0f}%{flag}")
    return prods

def cross_check(prods, pid, field, expected, tol=None):
    p = next((x for x in prods if str(x.get("product_id")) == str(pid)), None)
    if not p:
        print(f"  [!] Không tìm thấy product_id={pid}")
        return
    actual = p.get(field)
    if tol is not None and isinstance(actual, (int, float)):
        ok = abs(actual - expected) <= tol
    else:
        ok = actual == expected
    mark = "OK " if ok else "SAI"
    print(f"  [{mark}] id={pid} {field}={actual} (kỳ vọng≈{expected})")

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    hp = latest("hasaki", out_dir)
    lp = latest("lamthao", out_dir)
    if hp:
        prods = check(hp)
        print("\n  -- Đối chiếu giá trị đã biết (Hasaki) --")
        cross_check(prods, 102959, "market_price", 490000)
        cross_check(prods, 102959, "discount_percent", 25)
        cross_check(prods, 102959, "sold_count", 1397)
        cross_check(prods, 102959, "comment_count", 625)
        cross_check(prods, 102959, "star_breakdown", {"5":106,"4":10,"3":0,"2":0,"1":0})
    if lp:
        prods = check(lp)
        print("\n  -- Đối chiếu giá trị đã biết (Lamthao) --")
        cross_check(prods, 1054074766, "sold_count", 48949)
        cross_check(prods, 1054074766, "price", 3000)
        cross_check(prods, 1054074766, "market_price", 6000)
        cross_check(prods, 1054074766, "discount_percent", 50)
