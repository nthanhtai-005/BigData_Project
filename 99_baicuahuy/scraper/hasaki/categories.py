# -*- coding: utf-8 -*-
"""
Duyệt cây danh mục Hasaki.

- SEED_TOP_CATEGORIES: các danh mục cấp cao quan sát được trong capture (docs/RESEARCH.md §1.4).
- discover(): từ seed, gọi category-left để mở rộng ra các danh mục anh em + con,
  trả về danh sách category duy nhất {key(slug-c<id>), id, name}.
- cate_path dùng cho listing chính là `slug-c<id>` (vd 'cham-soc-da-mat-c4').
"""
from __future__ import annotations
import re
from typing import List, Dict, Optional

from .client import HasakiClient

SEED_TOP_CATEGORIES = [
    "cham-soc-da-mat-c4",
    "trang-diem-c23",
    "cham-soc-toc-c96",
    "cham-soc-co-the-c12",
    "nuoc-hoa-c103",
    "thoi-trang-c2351",
    "gia-dung-doi-song-c2440",
    "hasaki-clinic-spa-c331",
    "my-pham-high-end-c1907",
]


def _key_from_url(url: str) -> Optional[str]:
    """'https://hasaki.vn/danh-muc/lam-sach-da-c1855.html' -> 'lam-sach-da-c1855'."""
    if not url:
        return None
    m = re.search(r"/danh-muc/([a-z0-9\-]+-c\d+)\.html", url)
    return m.group(1) if m else None


def _id_from_key(key: str) -> Optional[int]:
    m = re.search(r"-c(\d+)$", key)
    return int(m.group(1)) if m else None


def discover(client: HasakiClient, seeds: Optional[List[str]] = None,
             expand: bool = True, verbose: bool = True) -> List[Dict]:
    """
    Trả về list danh mục: [{key, id, name}].
    expand=True: gọi category-left cho từng seed để lấy thêm subCate + subCateItem.
    """
    seeds = seeds or SEED_TOP_CATEGORIES
    found: Dict[str, Dict] = {}

    def add(key: str, name: Optional[str] = None):
        if not key:
            return
        if key not in found:
            found[key] = {"key": key, "id": _id_from_key(key), "name": name}
        elif name and not found[key].get("name"):
            found[key]["name"] = name

    for s in seeds:
        add(s)

    if expand:
        for seed in list(seeds):
            if verbose:
                print(f"  [cat] mở rộng cây từ: {seed}")
            resp = client.category_left(seed)
            if not resp:
                continue
            cat_left = (resp.get("data") or {}).get("categoryLeft") or {}
            for sub in cat_left.get("subCate") or []:
                key = _key_from_url(sub.get("url", "")) or _key_from_url(sub.get("path", ""))
                add(key, sub.get("name"))
                for item in sub.get("subCateItem") or []:
                    k2 = _key_from_url(item.get("url", "")) or _key_from_url(item.get("path", ""))
                    add(k2, item.get("name"))

    result = [v for v in found.values() if v["key"]]
    if verbose:
        print(f"  [cat] tổng số danh mục thu được: {len(result)}")
    return result
