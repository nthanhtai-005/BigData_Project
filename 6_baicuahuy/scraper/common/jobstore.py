# -*- coding: utf-8 -*-
"""
JobStore — hỗ trợ crawl lớn có RESUME (chạy theo mẻ, không mất tiến trình).

Cơ chế:
- Ghi streaming mỗi sản phẩm vào `<basename>.jsonl` (mở chế độ append).
- Khi khởi động, quét lại jsonl để dựng tập `done` = {(source, product_id)}
  -> lần chạy sau tự bỏ qua sản phẩm đã cào (tiết kiệm request, nhất là Hasaki detail).
- `finalize()` đọc jsonl, gộp trùng theo (source, product_id) (giữ bản đầy đủ nhất),
  gom `seen_in_categories`, rồi xuất `.json` + `.csv`.

Nhờ vậy có thể chạy lại cùng `--job <name>` nhiều lần để hoàn tất "cào tất cả".
"""
from __future__ import annotations
import os
import json
import csv
from typing import Set, Tuple, Optional

from .schema import UnifiedProduct, to_csv_row, CSV_COLUMNS


class JobStore:
    def __init__(self, out_dir: str, basename: str):
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir
        self.basename = basename
        self.jsonl_path = os.path.join(out_dir, basename + ".jsonl")
        self.done: Set[Tuple[str, str]] = set()
        self.count = 0           # số bản ghi ghi trong phiên hiện tại
        self._load_done()
        self._fh = open(self.jsonl_path, "a", encoding="utf-8")

    def _load_done(self) -> None:
        if not os.path.exists(self.jsonl_path):
            return
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    self.done.add((d.get("source"), str(d.get("product_id"))))
                except json.JSONDecodeError:
                    continue
        print(f"  [job] đã có sẵn {len(self.done)} sản phẩm trong {os.path.basename(self.jsonl_path)} (sẽ bỏ qua)")

    def is_done(self, source: str, product_id) -> bool:
        return (source, str(product_id)) in self.done

    def skip_ids_for(self, source: str) -> Set[str]:
        return {pid for (s, pid) in self.done if s == source}

    def add(self, product: UnifiedProduct) -> None:
        key = (product.source, str(product.product_id))
        if key in self.done:
            return
        self._fh.write(json.dumps(product.to_dict(), ensure_ascii=False) + "\n")
        self._fh.flush()
        self.done.add(key)
        self.count += 1

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass

    def finalize(self, formats=("json", "csv")) -> dict:
        """Đọc lại toàn bộ jsonl -> gộp trùng -> xuất json/csv."""
        self.close()
        merged = {}
        order = []
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (d.get("source"), str(d.get("product_id")))
                cat = d.get("crawl_category_name") or d.get("crawl_category_key")
                if key not in merged:
                    d["seen_in_categories"] = [cat] if cat else []
                    merged[key] = d
                    order.append(key)
                else:
                    cats = merged[key].get("seen_in_categories", [])
                    if cat and cat not in cats:
                        cats.append(cat)
                    merged[key]["seen_in_categories"] = cats
                    # ưu tiên bản có nhiều trường hơn (nhiều dữ liệu detail/reviews)
                    if len(json.dumps(d)) > len(json.dumps(merged[key])) - 50:
                        d["seen_in_categories"] = cats
                        merged[key] = d

        unique = [merged[k] for k in order]
        paths = {}
        if "json" in formats:
            p = os.path.join(self.out_dir, self.basename + ".json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(unique, f, ensure_ascii=False, indent=2)
            paths["json"] = p
        if "csv" in formats:
            p = os.path.join(self.out_dir, self.basename + ".csv")
            cols = CSV_COLUMNS + ["seen_in_categories"]
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                for d in unique:
                    row = {c: d.get(c) for c in CSV_COLUMNS if c in d}
                    row["num_images"] = len(d.get("images") or [])
                    row["num_variants"] = len(d.get("variants") or [])
                    row["num_comments_sampled"] = len(d.get("comments") or [])
                    row["num_reviews_sampled"] = len(d.get("reviews") or [])
                    sb = d.get("star_breakdown")
                    row["star_breakdown"] = json.dumps(sb, ensure_ascii=False) if sb else None
                    row["tags"] = "|".join(d.get("tags") or []) if d.get("tags") else None
                    row["seen_in_categories"] = "|".join(d.get("seen_in_categories") or [])
                    w.writerow(row)
            paths["csv"] = p
        paths["jsonl"] = self.jsonl_path
        paths["unique_count"] = len(unique)
        return paths
