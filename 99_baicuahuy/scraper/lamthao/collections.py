# -*- coding: utf-8 -*-
"""Liệt kê collection Lamthao qua /collections.json (phân trang đến khi rỗng)."""
from __future__ import annotations
from typing import List, Dict, Optional

from .client import LamthaoClient

# Một số collection "kỹ thuật" nên bỏ qua khi cào toàn bộ
SKIP_HANDLES = {"test", "test-nhom-qua-tang", "frontpage", "all"}


def discover(client: LamthaoClient, max_pages: int = 20, limit: int = 250,
             skip_technical: bool = True, use_sitemap: bool = True, verbose: bool = True) -> List[Dict]:
    """
    Trả về [{key(handle), id, name(title)}] cho TẤT CẢ collection.

    use_sitemap=True (mặc định): lấy handle đầy đủ từ /sitemap_collections_1.xml (~149),
    rồi bổ sung tên/id từ /collections.json (vốn chỉ liệt kê ~49). Đây là nguồn ĐẦY ĐỦ nhất.
    """
    # 1) Tên/id từ collections.json (không đầy đủ nhưng có title đẹp)
    titles: Dict[str, Dict] = {}
    for page in range(1, max_pages + 1):
        resp = client.collections(page=page, limit=limit)
        cols = (resp or {}).get("collections") or []
        if not cols:
            break
        for c in cols:
            h = c.get("handle")
            if h:
                titles[h] = {"id": c.get("id"), "name": c.get("title")}
        if len(cols) < limit:
            break

    # 2) Handle đầy đủ từ sitemap
    handles: List[str] = []
    if use_sitemap:
        handles = client.collection_handles_from_sitemap()
        if verbose:
            print(f"  [col] sitemap: {len(handles)} collection | collections.json: {len(titles)} có tên")
    if not handles:
        handles = list(titles.keys())  # fallback nếu sitemap lỗi

    found: Dict[str, Dict] = {}
    for h in handles:
        if skip_technical and h in SKIP_HANDLES:
            continue
        meta = titles.get(h, {})
        found[h] = {"key": h, "id": meta.get("id"), "name": meta.get("name") or h}

    result = list(found.values())
    if verbose:
        print(f"  [col] tổng số collection sẽ cào: {len(result)}")
    return result
