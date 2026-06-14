# -*- coding: utf-8 -*-
"""
Gộp sản phẩm trùng (cùng product_id xuất hiện ở nhiều danh mục/collection).
Giữ bản ghi đầu, gom tất cả danh mục đã thấy vào `seen_in_categories`.

Dùng:  python dedupe.py output/lamthao_xxx.json
Tạo:   output/lamthao_xxx_unique.json  (+ .csv)
"""
import json, sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.schema import CSV_COLUMNS  # tái dùng cột CSV

def main(path):
    with open(path, encoding="utf-8") as f:
        prods = json.load(f)
    merged = {}
    order = []
    for p in prods:
        key = (p.get("source"), p.get("product_id"))
        cat = p.get("crawl_category_name") or p.get("crawl_category_key")
        if key not in merged:
            p["seen_in_categories"] = [cat] if cat else []
            merged[key] = p
            order.append(key)
        else:
            if cat and cat not in merged[key]["seen_in_categories"]:
                merged[key]["seen_in_categories"].append(cat)

    unique = [merged[k] for k in order]
    base = os.path.splitext(path)[0] + "_unique"

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    # CSV phẳng (thêm cột seen_in_categories)
    from common.schema import UnifiedProduct, to_csv_row
    cols = CSV_COLUMNS + ["seen_in_categories"]
    with open(base + ".csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for p in unique:
            # dựng lại UnifiedProduct tối thiểu để dùng to_csv_row
            row = {c: p.get(c) for c in CSV_COLUMNS if c in p}
            # các trường suy ra
            row["num_images"] = len(p.get("images") or [])
            row["num_variants"] = len(p.get("variants") or [])
            row["num_comments_sampled"] = len(p.get("comments") or [])
            row["num_reviews_sampled"] = len(p.get("reviews") or [])
            sb = p.get("star_breakdown")
            row["star_breakdown"] = json.dumps(sb, ensure_ascii=False) if sb else None
            row["tags"] = "|".join(p.get("tags") or []) if p.get("tags") else None
            row["seen_in_categories"] = "|".join(p.get("seen_in_categories") or [])
            w.writerow(row)

    print(f"Tong dong vao   : {len(prods)}")
    print(f"San pham duy nhat: {len(unique)}")
    print(f"-> {base}.json")
    print(f"-> {base}.csv")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Dung: python dedupe.py <file.json>"); sys.exit(1)
    main(sys.argv[1])
