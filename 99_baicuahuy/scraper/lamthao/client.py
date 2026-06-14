# -*- coding: utf-8 -*-
"""
Lamthao (Haravan) API client — 3 endpoint .json công khai (xem docs/RESEARCH.md §2).
Không cần header đặc biệt.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

from common.http_client import HttpClient

BASE = "https://lamthaocosmetics.vn"


class LamthaoClient:
    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient(base_headers={"Referer": BASE + "/"})

    def collections(self, page: int = 1, limit: int = 250) -> Optional[dict]:
        """GET /collections.json?page=&limit= -> {collections:[...]}"""
        url = f"{BASE}/collections.json?page={page}&limit={limit}"
        return self.http.get(url)

    def collection_products(self, handle: str, page: int = 1, limit: int = 50) -> Optional[dict]:
        """GET /collections/<handle>/products.json?page=&limit= -> {products:[...]}"""
        url = f"{BASE}/collections/{handle}/products.json?page={page}&limit={limit}"
        return self.http.get(url, headers={"Referer": f"{BASE}/collections/{handle}"})

    def product(self, handle: str) -> Optional[dict]:
        """GET /products/<handle>.json -> {product:{...}}"""
        url = f"{BASE}/products/{handle}.json"
        return self.http.get(url, headers={"Referer": f"{BASE}/products/{handle}"})

    def collection_handles_from_sitemap(self) -> list:
        """Đọc /sitemap_collections_1.xml -> danh sách handle collection (đầy đủ ~149)."""
        import re
        xml = self.http.get(f"{BASE}/sitemap_collections_1.xml", as_json=False)
        if not xml:
            return []
        handles = re.findall(r"/collections/([a-z0-9\-]+)", xml)
        # giữ thứ tự, loại trùng
        seen = []
        for h in handles:
            if h not in seen:
                seen.append(h)
        return seen
