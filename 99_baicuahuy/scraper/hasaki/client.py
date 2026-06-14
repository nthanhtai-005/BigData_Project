# -*- coding: utf-8 -*-
"""
Hasaki API client — gói gọn 5 endpoint đã nghiên cứu (xem docs/RESEARCH.md §1).
Tất cả request đều cần header `mobiledeviceid` (UUID bất kỳ) + Referer.
"""
from __future__ import annotations
import uuid
import math
from typing import Optional, Dict, Any, List

from common.http_client import HttpClient

BASE = "https://hasaki.vn"


class HasakiClient:
    def __init__(self, http: Optional[HttpClient] = None, device_id: Optional[str] = None):
        self.device_id = device_id or str(uuid.uuid4())
        headers = {
            "mobiledeviceid": self.device_id,
            "Referer": BASE + "/",
            "Origin": BASE,
        }
        self.http = http or HttpClient(base_headers=headers)
        # đảm bảo header bắt buộc luôn có ngay cả khi http truyền từ ngoài
        self.http.base_headers.setdefault("mobiledeviceid", self.device_id)

    # ---- Cây danh mục ----
    def category_left(self, category_slug: str) -> Optional[dict]:
        """GET /api/v4/main/category-left?category_slug=<slug>-c<id>"""
        url = f"{BASE}/api/v4/main/category-left?category_slug={category_slug}"
        return self.http.get(url, headers={"Referer": f"{BASE}/danh-muc/{category_slug}.html"})

    # ---- Listing theo danh mục ----
    def list_products(self, cate_path: str, page: int = 1, size: int = 40) -> Optional[dict]:
        """GET /mobile/v3/main/products?cate_path=...&page=&size=&has_meta_data=1&is_desktop=1"""
        url = (f"{BASE}/mobile/v3/main/products?cate_path={cate_path}"
               f"&page={page}&size={size}&has_meta_data=1&is_desktop=1")
        ref = f"{BASE}/danh-muc/{cate_path}.html"
        return self.http.get(url, headers={"Referer": ref})

    # ---- Chi tiết sản phẩm ----
    def product_detail(self, product_id: Any) -> Optional[dict]:
        """GET /mobile/v3/detail/product?product_id=<id>&is_desktop=1"""
        url = f"{BASE}/mobile/v3/detail/product?product_id={product_id}&is_desktop=1"
        return self.http.get(url)

    # ---- Đánh giá (sao + review) ----
    def rating_reviews(self, product_id: Any, page: int = 1, size: int = 5,
                       sort: str = "create", filt: str = "filter_all") -> Optional[dict]:
        url = (f"{BASE}/mobile/v3/detail/product/rating-reviews?product_id={product_id}"
               f"&page={page}&size={size}&sort={sort}&filter={filt}&is_desktop=1")
        return self.http.get(url)

    # ---- Bình luận / hỏi đáp ----
    def comments(self, product_id: Any, page: int = 1, size: int = 5) -> Optional[dict]:
        url = f"{BASE}/mobile/v1/detail/product/comments?product_id={product_id}&page={page}&size={size}"
        return self.http.get(url)

    # ---- Tiện ích ----
    @staticmethod
    def get_common_data(detail_resp: dict) -> Optional[dict]:
        """Lấy block CommonInfo.common_data từ response detail."""
        if not detail_resp:
            return None
        blocks = (detail_resp.get("data") or {}).get("blocks") or []
        for b in blocks:
            if b.get("type") == "CommonInfo":
                return b.get("common_data")
        return None

    @staticmethod
    def total_pages(list_resp: dict, size: int = 40) -> int:
        meta = (list_resp.get("data") or {}).get("meta_data") or {}
        total = meta.get("products_total") or 0
        return max(1, math.ceil(total / size)) if total else 1
