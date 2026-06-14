# -*- coding: utf-8 -*-
"""Hàm chuẩn hoá dùng chung cho cả 2 nguồn."""
from __future__ import annotations
import re
from typing import Optional, Any


def to_int(v: Any) -> Optional[int]:
    """Ép về int VND. Chấp nhận '3000', 3000.0, '3.000 ₫', None."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(round(v))
    if isinstance(v, str):
        digits = re.sub(r"[^\d]", "", v)
        return int(digits) if digits else None
    return None


def abs_url(u: Optional[str], default_scheme: str = "https:") -> Optional[str]:
    """Chuẩn hoá URL ảnh: '//host/x.jpg' -> 'https://host/x.jpg'."""
    if not u:
        return None
    u = u.strip()
    if u.startswith("//"):
        return default_scheme + u
    return u


def compute_discount_percent(market: Optional[int], price: Optional[int]) -> Optional[int]:
    """% giảm = (giá gốc - giá bán)/giá gốc * 100, làm tròn. None nếu không hợp lệ."""
    if not market or not price:
        return None
    if market <= 0 or price <= 0 or price >= market:
        return 0 if (market and price and price >= market) else None
    return int(round((market - price) / market * 100))


def has_voucher(market: Optional[int], price: Optional[int]) -> Optional[bool]:
    if market is None or price is None:
        return None
    return bool(market > price > 0)


def clean_text(s: Optional[str], max_len: Optional[int] = None) -> Optional[str]:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s)).strip()
    if max_len and len(s) > max_len:
        s = s[:max_len].rstrip() + "…"
    return s or None


def extract_id_from_slug(slug: str) -> Optional[int]:
    """'cham-soc-da-mat-c4' -> 4 ; 'lam-sach-da-c1855.html' -> 1855."""
    m = re.search(r"-c(\d+)(?:\.html)?$", slug)
    if m:
        return int(m.group(1))
    m = re.search(r"-c(\d+)", slug)
    return int(m.group(1)) if m else None
