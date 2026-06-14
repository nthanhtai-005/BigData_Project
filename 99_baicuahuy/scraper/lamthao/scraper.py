# -*- coding: utf-8 -*-
"""
Lamthao scraper — orchestration.

Luồng: collection -> products.json (phân trang) -> map UnifiedProduct.
Giá lấy từ .json (VND đúng). sole_quantity = số lượt bán. inventory_quantity = tồn kho.
Nền tảng KHÔNG có đánh giá/sao/comment -> các trường đó = None (xem docs/RESEARCH.md §2.4).
Mapping: docs/FIELD_MAPPING.md.
"""
from __future__ import annotations
import datetime
from typing import Iterator, List, Optional, Dict, Any

from common.schema import UnifiedProduct, Variant
from common import normalize as N
from .client import LamthaoClient


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def map_product(prod: dict, collection: Optional[dict]) -> UnifiedProduct:
    """Map 1 product (.json) sang UnifiedProduct."""
    up = UnifiedProduct(source="lamthao", scraped_at=_now())
    if collection:
        up.crawl_category_id = collection.get("id")
        up.crawl_category_key = collection.get("key")
        up.crawl_category_name = collection.get("name")

    up.name = N.clean_text(prod.get("title"))
    up.product_id = prod.get("id")
    up.handle = prod.get("handle")
    if up.handle:
        up.url = f"https://lamthaocosmetics.vn/products/{up.handle}"
    up.brand = N.clean_text(prod.get("vendor"))
    up.product_type = N.clean_text(prod.get("product_type"))
    up.tags = prod.get("tags") or []
    up.description_html = prod.get("body_html")
    up.available = prod.get("available")

    # Ảnh (#2)
    images = prod.get("images") or []
    img_urls = []
    for im in images:
        src = im.get("src") if isinstance(im, dict) else im
        u = N.abs_url(src)
        if u:
            img_urls.append(u)
    up.images = img_urls
    main_img = prod.get("image")
    if isinstance(main_img, dict):
        up.image = N.abs_url(main_img.get("src"))
    up.image = up.image or (img_urls[0] if img_urls else None)

    # (8) số lượt bán = sole_quantity (đã xác minh)
    up.sold_count = N.to_int(prod.get("sole_quantity"))

    # (12) danh mục: collection + product_type + tags (đã set ở trên)
    parts = [up.crawl_category_name, up.product_type]
    up.category_path = " / ".join([p for p in parts if p]) or None

    # Biến thể -> giá, tồn kho (#4,5,6,14)
    variants_raw = prod.get("variants") or []
    total_stock = 0
    prices = []
    vlist: List[Variant] = []
    for v in variants_raw:
        price = N.to_int(v.get("price"))
        compare = N.to_int(v.get("compare_at_price"))
        # Haravan: compare=0 nghĩa là không giảm
        if compare == 0:
            compare = None
        disc = N.compute_discount_percent(compare, price) if compare else 0
        inv = N.to_int(v.get("inventory_quantity"))
        if inv:
            total_stock += inv
        if price:
            prices.append(price)
        vlist.append(Variant(
            variant_id=v.get("id"), sku=v.get("sku"), barcode=v.get("barcode"),
            title=N.clean_text(v.get("title")),
            option1=v.get("option1") or None, option2=v.get("option2") or None,
            option3=v.get("option3") or None,
            price=price, compare_at_price=compare, discount_percent=disc,
            has_voucher=N.has_voucher(compare, price),
            inventory_quantity=inv, available=v.get("available"),
            weight_grams=v.get("grams"),
        ))
    up.variants = vlist
    up.stock_quantity = total_stock

    # Giá đại diện: chọn biến thể có giá thấp nhất (giống thẻ sản phẩm hiển thị)
    if vlist:
        with_price = [v for v in vlist if v.price]
        rep = min(with_price, key=lambda v: v.price) if with_price else vlist[0]
        up.price = rep.price
        up.market_price = rep.compare_at_price
        up.discount_percent = rep.discount_percent
        up.has_voucher = rep.has_voucher
    if prices:
        up.price_min = min(prices)
        up.price_max = max(prices)

    # (7,9,10,11,13): Lamthao không có -> để None (đã mặc định)
    return up


class LamthaoScraper:
    def __init__(self, client: LamthaoClient, limit: int = 50, verbose: bool = True):
        self.client = client
        self.limit = limit
        self.verbose = verbose

    def scrape_collection(self, collection: dict, max_pages: Optional[int] = None,
                          max_products: Optional[int] = None,
                          skip_ids: Optional[set] = None) -> Iterator[UnifiedProduct]:
        handle = collection["key"]
        skip_ids = skip_ids or set()
        count = 0
        page = 1
        while True:
            if max_pages and page > max_pages:
                break
            resp = self.client.collection_products(handle, page=page, limit=self.limit)
            products = (resp or {}).get("products") or []
            if not products:
                break
            if self.verbose:
                print(f"  [lamthao] {handle} trang {page}: {len(products)} sản phẩm")
            for prod in products:
                if str(prod.get("id")) in skip_ids:
                    continue
                up = map_product(prod, collection)
                up.compute_availability()
                yield up
                count += 1
                if max_products and count >= max_products:
                    return
            if len(products) < self.limit:
                break
            page += 1
