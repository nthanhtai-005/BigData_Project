# -*- coding: utf-8 -*-
"""Ghi kết quả ra JSONL (streaming), JSON (mảng), và CSV."""
from __future__ import annotations
import json
import csv
import os
from typing import List

from .schema import UnifiedProduct, to_csv_row, CSV_COLUMNS


class OutputWriter:
    """Ghi streaming ra .jsonl; cuối phiên kết xuất thêm .json và .csv."""

    def __init__(self, out_dir: str, basename: str, formats=("jsonl", "json", "csv")):
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir
        self.basename = basename
        self.formats = set(formats)
        self.count = 0
        self._buffer: List[UnifiedProduct] = []
        self._jsonl_path = os.path.join(out_dir, basename + ".jsonl")
        self._jsonl_fh = open(self._jsonl_path, "w", encoding="utf-8") if "jsonl" in self.formats or "json" in self.formats else None

    def write(self, product: UnifiedProduct) -> None:
        d = product.to_dict()
        if self._jsonl_fh:
            self._jsonl_fh.write(json.dumps(d, ensure_ascii=False) + "\n")
            self._jsonl_fh.flush()
        self._buffer.append(product)
        self.count += 1

    def close(self) -> dict:
        paths = {}
        if self._jsonl_fh:
            self._jsonl_fh.close()
            if "jsonl" in self.formats:
                paths["jsonl"] = self._jsonl_path

        if "json" in self.formats:
            p = os.path.join(self.out_dir, self.basename + ".json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump([x.to_dict() for x in self._buffer], f, ensure_ascii=False, indent=2)
            paths["json"] = p

        if "csv" in self.formats:
            p = os.path.join(self.out_dir, self.basename + ".csv")
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
                w.writeheader()
                for x in self._buffer:
                    w.writerow(to_csv_row(x))
            paths["csv"] = p

        # nếu chỉ muốn json mà không muốn giữ jsonl trung gian
        if "jsonl" not in self.formats and os.path.exists(self._jsonl_path):
            try:
                os.remove(self._jsonl_path)
            except OSError:
                pass
        return paths
