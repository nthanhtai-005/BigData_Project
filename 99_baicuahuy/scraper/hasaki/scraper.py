# -*- coding: utf-8 -*-
"""
Hasaki scraper — orchestration.

Luồng: category -> listing (phân trang) -> [detail] -> [reviews + comments]
=> map sang UnifiedProduct (đủ 14 trường). Mapping chi tiết: docs/FIELD_MAPPING.md.
"""
from __future__ import annotations
import datetime
from typing import Iterator, List, Optional, Dict, Any

from common.schema import UnifiedProduct, Variant, ReviewSample, CommentSample
from common import normalize as N
from .client import HasakiClient


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def map_listing_product(prod: dict, category: Optional[dict]) -> UnifiedProduct:
    """Map 1 phần tử data.products[] (listing) sang UnifiedProduct (trường cơ bản)."""
    up = UnifiedProduct(source="hasaki", scraped_at=_now())
    if category:
        up.crawl_category_id = category.get("id")
        up.crawl_category_key = category.get("key")
        up.crawl_category_name = category.get("name")

    up.name = N.clean_text(prod.get("name"))
    up.english_name = N.clean_text(prod.get("english_name"))
    up.product_id = prod.get("id")
    up.sku = prod.get("sku")
    up.url = prod.get("product_url")

    brand = prod.get("brand") or {}
    up.brand = N.clean_text(brand.get("name"))
    up.brand_id = brand.get("id")

    up.image = N.abs_url(prod.get("image"))
    if up.image:
        up.images = [up.image]

    up.market_price = N.to_int(prod.get("market_price"))
    up.price = N.to_int(prod.get("price"))
    up.discount_percent = prod.get("discount_percent")
    if up.discount_percent is None:
        up.discount_percent = N.compute_discount_percent(up.market_price, up.price)
    up.has_voucher = N.has_voucher(up.market_price, up.price)
    up.price_min = up.price
    up.price_max = up.market_price
    up.promotion_text = N.clean_text(prod.get("promotion_text"))

    rating = prod.get("rating") or {}
    up.rating_average = rating.get("average")
    up.review_count = rating.get("total")

    up.sold_count = prod.get("bought_count")
    up.sold_count_30d = prod.get("order_count_30")

    up.category_path = N.clean_text(prod.get("category_name_level"))

    up.stock_quantity = N.to_int(prod.get("quantity"))

    if prod.get("deal"):
        up.deal = prod.get("deal")

    # listing = 1 biến thể đại diện
    up.variants = [Variant(
        variant_id=prod.get("id"), sku=prod.get("sku"), title=up.name,
        price=up.price, compare_at_price=up.market_price,
        discount_percent=up.discount_percent, has_voucher=up.has_voucher,
        inventory_quantity=up.stock_quantity,
    )]
    return up


def enrich_with_detail(up: UnifiedProduct, common: dict) -> None:
    """Bổ sung từ detail.common_data: comment.total, voucher tiền, breadcrumb, gallery, announce."""
    if not common:
        return
    # gallery -> images
    gallery = common.get("gallery") or []
    imgs = [N.abs_url(g.get("image")) for g in gallery if g.get("image")]
    imgs = [i for i in imgs if i]
    if imgs:
        up.images = imgs
        up.image = up.image or imgs[0]

    # comment total (#9)
    comment = common.get("comment") or {}
    if comment.get("total") is not None:
        up.comment_count = comment.get("total")

    # rating (đồng bộ)
    rating = common.get("rating") or {}
    if rating.get("average") is not None:
        up.rating_average = rating.get("average")
    if rating.get("total") is not None:
        up.review_count = rating.get("total")

    # voucher tiền + giá chi tiết (#6)
    pd = common.get("price_detail") or {}
    if pd.get("coupons"):
        up.voucher_text = N.clean_text(pd.get("coupons"))
    # final_price (chuỗi) -> nếu price listing thiếu thì lấy
    if up.price is None and pd.get("final_price"):
        up.price = N.to_int(pd.get("final_price"))

    # breadcrumb danh mục (#12)
    clist = common.get("category_list") or []
    if clist:
        up.category_breadcrumb = [
            {"id": c.get("id"), "name": c.get("name"),
             "level": c.get("level"), "url": c.get("url")} for c in clist
        ]
        if not up.category_path:
            up.category_path = " / ".join([c.get("name") for c in clist if c.get("name")])

    # announce (số công bố BYT)
    ann = common.get("announce") or {}
    if ann.get("number"):
        up.announce_number = N.clean_text(ann.get("number"))

    # mô tả/title
    if common.get("quantity") is not None and up.stock_quantity is None:
        up.stock_quantity = N.to_int(common.get("quantity"))


def enrich_with_reviews(up: UnifiedProduct, rr: dict, sample_reviews: int = 5) -> None:
    """Bổ sung phân bố sao (#11), comment có ảnh (#10), mẫu review (#13)."""
    if not rr:
        return
    data = rr.get("data") or {}
    rating = data.get("rating") or {}

    # phân bố sao (#11)
    stars = rating.get("stars") or []
    if stars:
        up.star_breakdown = {str(s.get("star")): s.get("count", 0) for s in stars}

    # số review có ảnh (#10) + tổng review
    for f in rating.get("filter") or []:
        if f.get("key") == "filter_has_image":
            up.comment_with_image_count = f.get("count")
        if f.get("key") == "filter_all" and up.review_count is None:
            up.review_count = f.get("count")
    if data.get("total") is not None:
        up.review_count = data.get("total")

    # mẫu review (#13)
    for rv in (data.get("reviews") or [])[:sample_reviews]:
        imgs = rv.get("images") or []
        imgs = [N.abs_url(x) for x in imgs] if isinstance(imgs, list) else []
        rstar = (rv.get("rating") or {}).get("star")
        up.reviews.append(ReviewSample(
            content=N.clean_text(rv.get("content"), 500),
            star=rstar,
            user=N.clean_text(rv.get("user_fullname")),
            created_at=rv.get("created_at"),
            has_image=bool(imgs),
            is_bought=rv.get("is_bought"),
            images=[i for i in imgs if i],
            reply=N.clean_text(rv.get("answer_rating"), 300),
        ))


def enrich_with_comments(up: UnifiedProduct, cm: dict, sample_comments: int = 5) -> None:
    """Bổ sung số comment (#9) + mẫu comment hỏi đáp (#13)."""
    if not cm:
        return
    data = cm.get("data") or {}
    meta = data.get("meta_data") or {}
    if meta.get("comments_total") is not None:
        up.comment_count = meta.get("comments_total")
    for c in (data.get("comments") or [])[:sample_comments]:
        replies = [N.clean_text(s.get("content"), 300)
                   for s in (c.get("sub_comments") or [])]
        up.comments.append(CommentSample(
            content=N.clean_text(c.get("content"), 500),
            user=N.clean_text((c.get("user") or {}).get("fullname")),
            created_at=c.get("created_at"),
            like_count=c.get("like_count"),
            replies=[r for r in replies if r],
        ))


class HasakiScraper:
    def __init__(self, client: HasakiClient, with_detail: bool = True,
                 with_reviews: bool = True, sample_reviews: int = 5,
                 sample_comments: int = 5, size: int = 40, verbose: bool = True):
        self.client = client
        self.with_detail = with_detail
        self.with_reviews = with_reviews
        self.sample_reviews = sample_reviews
        self.sample_comments = sample_comments
        self.size = size
        self.verbose = verbose

    def scrape_category(self, category: dict, max_pages: Optional[int] = None,
                        max_products: Optional[int] = None,
                        skip_ids: Optional[set] = None) -> Iterator[UnifiedProduct]:
        cate_path = category["key"]
        skip_ids = skip_ids or set()
        first = self.client.list_products(cate_path, page=1, size=self.size)
        if not first:
            if self.verbose:
                print(f"  [hasaki] không lấy được listing: {cate_path}")
            return
        total_pages = self.client.total_pages(first, self.size)
        if max_pages:
            total_pages = min(total_pages, max_pages)
        meta = (first.get("data") or {}).get("meta_data") or {}
        if self.verbose:
            print(f"  [hasaki] {cate_path}: products_total={meta.get('products_total')} "
                  f"-> duyệt {total_pages} trang")

        count = 0
        for page in range(1, total_pages + 1):
            resp = first if page == 1 else self.client.list_products(cate_path, page, self.size)
            if not resp:
                continue
            products = (resp.get("data") or {}).get("products") or []
            for prod in products:
                if str(prod.get("id")) in skip_ids:
                    continue
                up = map_listing_product(prod, category)
                if self.with_detail:
                    self._enrich_one(up)
                up.compute_availability()
                yield up
                count += 1
                if max_products and count >= max_products:
                    return

    def _enrich_one(self, up: UnifiedProduct) -> None:
        pid = up.product_id
        if pid is None:
            return
        detail = self.client.product_detail(pid)
        common = self.client.get_common_data(detail) if detail else None
        if common:
            enrich_with_detail(up, common)
        if self.with_reviews:
            rr = self.client.rating_reviews(pid, page=1, size=max(self.sample_reviews, 5))
            if rr:
                enrich_with_reviews(up, rr, self.sample_reviews)
            cm = self.client.comments(pid, page=1, size=max(self.sample_comments, 5))
            if cm:
                enrich_with_comments(up, cm, self.sample_comments)
