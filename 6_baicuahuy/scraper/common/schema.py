# -*- coding: utf-8 -*-
"""
Unified product schema — schema thống nhất cho sản phẩm từ Hasaki & Lamthao.

Thiết kế bao phủ đủ 14 trường yêu cầu + trường mở rộng. Trường nào nguồn không có
sẽ để None và được đánh dấu trong `data_availability` để minh bạch.

Tham chiếu mapping: docs/FIELD_MAPPING.md
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


# Danh sách 14 trường yêu cầu (dùng cho data_availability & kiểm thử)
REQUIRED_FIELDS = [
    "name",                      # 1  tên sản phẩm
    "image",                     # 2  url ảnh
    "product_id",                # 3  id
    "market_price",              # 4  giá trước giảm
    "price",                     # 5  giá sau giảm
    "discount_percent",          # 6  voucher %
    "rating_average",            # 7  số sao
    "sold_count",                # 8  số lượt bán
    "comment_count",             # 9  số comment
    "comment_with_image_count",  # 10 số comment có ảnh
    "star_breakdown",            # 11 phân bố sao
    "category_path",             # 12 danh mục
    "comments",                  # 13 nội dung comment
    "stock_quantity",            # 14 tồn kho
]


@dataclass
class Variant:
    """Một biến thể (Lamthao có nhiều; Hasaki thường 1)."""
    variant_id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    title: Optional[str] = None
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    price: Optional[int] = None              # giá sau giảm (VND)
    compare_at_price: Optional[int] = None   # giá trước giảm (VND)
    discount_percent: Optional[int] = None
    has_voucher: Optional[bool] = None
    inventory_quantity: Optional[int] = None # tồn kho biến thể
    available: Optional[bool] = None
    weight_grams: Optional[float] = None


@dataclass
class ReviewSample:
    """Một đánh giá (có sao) — chủ yếu Hasaki."""
    content: Optional[str] = None
    star: Optional[int] = None
    user: Optional[str] = None
    created_at: Optional[int] = None     # epoch giây
    has_image: bool = False
    is_bought: Optional[bool] = None
    images: List[str] = field(default_factory=list)
    reply: Optional[str] = None          # câu trả lời của shop (nếu có)


@dataclass
class CommentSample:
    """Một bình luận/hỏi đáp — chủ yếu Hasaki."""
    content: Optional[str] = None
    user: Optional[str] = None
    created_at: Optional[int] = None
    like_count: Optional[int] = None
    replies: List[str] = field(default_factory=list)


@dataclass
class UnifiedProduct:
    # ---- Metadata cào ----
    source: str = ""                      # "hasaki" | "lamthao"
    scraped_at: Optional[str] = None      # ISO timestamp
    crawl_category_id: Optional[Any] = None     # danh mục đang duyệt khi bắt được SP
    crawl_category_key: Optional[str] = None    # slug (Hasaki) / handle (Lamthao)
    crawl_category_name: Optional[str] = None

    # ---- (1) Tên ----
    name: Optional[str] = None
    english_name: Optional[str] = None

    # ---- (3) ID ----
    product_id: Optional[Any] = None
    sku: Optional[str] = None
    url: Optional[str] = None
    handle: Optional[str] = None          # Lamthao

    # ---- Thương hiệu ----
    brand: Optional[str] = None
    brand_id: Optional[Any] = None

    # ---- (2) Ảnh ----
    image: Optional[str] = None           # ảnh đại diện
    images: List[str] = field(default_factory=list)

    # ---- (4,5,6) Giá & voucher (cấp sản phẩm, đại diện) ----
    price: Optional[int] = None           # giá sau giảm
    market_price: Optional[int] = None    # giá trước giảm
    discount_percent: Optional[int] = None
    has_voucher: Optional[bool] = None
    voucher_text: Optional[str] = None    # Hasaki: tiền coupon / text KM
    price_min: Optional[int] = None
    price_max: Optional[int] = None

    # ---- (7) Sao ----
    rating_average: Optional[float] = None

    # ---- (8) Lượt bán ----
    sold_count: Optional[int] = None
    sold_count_30d: Optional[int] = None  # Hasaki order_count_30

    # ---- (9,10,11) Bình luận & đánh giá (số lượng) ----
    comment_count: Optional[int] = None
    comment_with_image_count: Optional[int] = None
    review_count: Optional[int] = None
    star_breakdown: Optional[Dict[str, int]] = None   # {"5":..,"4":..,..}

    # ---- (12) Danh mục ----
    category_path: Optional[str] = None               # "A / B / C"
    category_breadcrumb: List[Dict[str, Any]] = field(default_factory=list)
    product_type: Optional[str] = None                # Lamthao
    tags: List[str] = field(default_factory=list)     # Lamthao

    # ---- (13) Nội dung comment/review ----
    comments: List[CommentSample] = field(default_factory=list)
    reviews: List[ReviewSample] = field(default_factory=list)

    # ---- (14) Tồn kho ----
    stock_quantity: Optional[int] = None

    # ---- Biến thể ----
    variants: List[Variant] = field(default_factory=list)

    # ---- Mở rộng ----
    promotion_text: Optional[str] = None
    deal: Optional[Dict[str, Any]] = None       # flash sale (Hasaki)
    announce_number: Optional[str] = None        # số công bố BYT (Hasaki)
    description_html: Optional[str] = None
    available: Optional[bool] = None

    # ---- Minh bạch độ phủ ----
    data_availability: Dict[str, bool] = field(default_factory=dict)

    def compute_availability(self) -> None:
        """Đánh dấu trường yêu cầu nào thực sự có dữ liệu."""
        av = {}
        for f in REQUIRED_FIELDS:
            v = getattr(self, f)
            if isinstance(v, (list, dict)):
                av[f] = len(v) > 0
            else:
                av[f] = v is not None
        self.data_availability = av

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---- Cột cho xuất CSV (phẳng hoá) ----
CSV_COLUMNS = [
    "source", "product_id", "sku", "name", "english_name", "brand", "url",
    "image", "num_images",
    "market_price", "price", "discount_percent", "has_voucher", "voucher_text",
    "price_min", "price_max",
    "rating_average", "sold_count", "sold_count_30d",
    "comment_count", "comment_with_image_count", "review_count", "star_breakdown",
    "category_path", "product_type", "tags",
    "stock_quantity", "num_variants",
    "promotion_text", "announce_number", "available",
    "crawl_category_key", "crawl_category_name", "scraped_at",
    "num_comments_sampled", "num_reviews_sampled",
]


def to_csv_row(p: UnifiedProduct) -> Dict[str, Any]:
    """Phẳng hoá UnifiedProduct thành 1 dòng CSV."""
    import json as _json
    return {
        "source": p.source,
        "product_id": p.product_id,
        "sku": p.sku,
        "name": p.name,
        "english_name": p.english_name,
        "brand": p.brand,
        "url": p.url,
        "image": p.image,
        "num_images": len(p.images),
        "market_price": p.market_price,
        "price": p.price,
        "discount_percent": p.discount_percent,
        "has_voucher": p.has_voucher,
        "voucher_text": p.voucher_text,
        "price_min": p.price_min,
        "price_max": p.price_max,
        "rating_average": p.rating_average,
        "sold_count": p.sold_count,
        "sold_count_30d": p.sold_count_30d,
        "comment_count": p.comment_count,
        "comment_with_image_count": p.comment_with_image_count,
        "review_count": p.review_count,
        "star_breakdown": _json.dumps(p.star_breakdown, ensure_ascii=False) if p.star_breakdown else None,
        "category_path": p.category_path,
        "product_type": p.product_type,
        "tags": "|".join(p.tags) if p.tags else None,
        "stock_quantity": p.stock_quantity,
        "num_variants": len(p.variants),
        "promotion_text": p.promotion_text,
        "announce_number": p.announce_number,
        "available": p.available,
        "crawl_category_key": p.crawl_category_key,
        "crawl_category_name": p.crawl_category_name,
        "scraped_at": p.scraped_at,
        "num_comments_sampled": len(p.comments),
        "num_reviews_sampled": len(p.reviews),
    }
