#!/usr/bin/env python3
"""Clean product CSV data into an analysis-ready table.

Default usage:
    python clean_products.py

The script reads all_products.csv and writes all_products_analysis_ready.csv.
It keeps only comparable analysis columns, normalizes category/brand/price,
removes noise rows (missing/0/1 price, price greater than market price),
removes non-product/service rows, fixes impossible stock values, and
de-duplicates by source + name.

Noise-removal rules for price:
    * price missing/empty  -> drop row
    * price == 0           -> drop row
    * price == 1           -> drop row (placeholder for gifts / recalls)
    * price  > market_price -> drop row (impossible)
    * market_price missing  -> set market_price = price
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


OUTPUT_FIELDS = [
    "source",
    "name",
    "brand",
    "category",
    "num_images",
    "price",
    "market_price",
    "discount_amount",
    "discount_percent",
    "has_discount",
    "sold_count",
    "stock_quantity",
    "scraped_at",
]

# Stock sentinel values that mean "effectively unlimited" rather than a real count.
STOCK_SENTINEL = 99_999_999     

SERVICE_CATEGORIES = {
    "Dịch Vụ Phòng Khám",
    "Triệt Lông Diode Laser",
    "Thư Giãn & Chăm Sóc",
}

HASAKI_CATEGORY_MAP = {
    "Chăm Sóc Da Mặt": "Chăm Sóc Da Mặt",
    "Trang Điểm": "Trang Điểm",
    "Chăm Sóc Cơ Thể": "Chăm Sóc Cơ Thể",
    "Chăm Sóc Tóc Và Da Đầu": "Chăm Sóc Tóc Và Da Đầu",
    "Nước Hoa": "Nước Hoa",
    "Chăm Sóc Cá Nhân": "Chăm Sóc Cá Nhân",
    "Thực Phẩm Chức Năng": "Thực Phẩm Chức Năng",
    "Dịch Vụ Phòng Khám": "Dịch Vụ Phòng Khám",
    "Triệt Lông Diode Laser": "Triệt Lông Diode Laser",
    "Thư Giãn & Chăm Sóc": "Thư Giãn & Chăm Sóc",
    "Clearance Sale": "Khuyến Mãi",
    "Gift": "Khuyến Mãi",
    "Mini": "Khuyến Mãi",
    "Mỹ Phẩm High-End": "Khác",
    "Thời Trang Nam": "Khác",
    "Thời Trang Nữ": "Khác",
    "Thời Trang Trẻ Em": "Khác",
    "Phụ Kiện Điện Thoại": "Khác",
    "Phụ Kiện Thời Trang": "Khác",
    "Quạt Mini & Quạt Cầm Tay": "Khác",
    "Sữa Tắm Gội Cho Bé": "Khác",
    "Kem Dưỡng Ẩm Cho Bé": "Khác",
    "Kem Chống Nắng Cho Bé": "Khác",
    "Chống Muỗi Cho Bé": "Khác",
    "Khử Mùi & Làm Thơm Phòng": "Khác",
    "Nước Xả": "Khác",
    "Nước Giặt": "Khác",
    "Bông Tắm": "Khác",
    "Khăn Tắm": "Khác",
}

LAMTHAO_SLUG_MAP = {
    "cham-soc-da-mat": "Chăm Sóc Da Mặt",
    "serum-essence-tinh-chat-duong": "Chăm Sóc Da Mặt",
    "kem-duong-gel-duong": "Chăm Sóc Da Mặt",
    "best-seller-cham-soc-da-mat": "Chăm Sóc Da Mặt",
    "trang-diem": "Trang Điểm",
    "kem-nen-cushion-bb-cream": "Trang Điểm",
    "bong-mut-trang-diem": "Trang Điểm",
    "kem-lot": "Trang Điểm",
    "phan-nen": "Trang Điểm",
    "phan-phu": "Trang Điểm",
    "son-thoi": "Trang Điểm",
    "son-kem-bong-tint": "Trang Điểm",
    "son-duong-mat-na-ngu-moi": "Trang Điểm",
    "kich-mi": "Trang Điểm",
    "duong-mi": "Trang Điểm",
    "mascara-mascara-chan-may": "Trang Điểm",
    "tao-khoi-highlight": "Trang Điểm",
    "ma-hong": "Trang Điểm",
    "best-seller-trang-diem": "Trang Điểm",
    "sua-tam": "Chăm Sóc Cơ Thể",
    "duong-the": "Chăm Sóc Cơ Thể",
    "cham-soc-co-the": "Chăm Sóc Cơ Thể",
    "tay-te-bao-chet-body": "Chăm Sóc Cơ Thể",
    "dau-goi-dau-xa": "Chăm Sóc Tóc Và Da Đầu",
    "duong-toc-u-toc": "Chăm Sóc Tóc Và Da Đầu",
    "nuoc-hoa": "Nước Hoa",
    "xit-thom-toan-than-body-mist": "Nước Hoa",
    "kem-danh-rang": "Chăm Sóc Cá Nhân",
    "nuoc-suc-mieng": "Chăm Sóc Cá Nhân",
    "thiet-bi-lam-dep": "Thiết Bị & Phụ Kiện Làm Đẹp",
    "phu-kien-lam-dep": "Thiết Bị & Phụ Kiện Làm Đẹp",
    "co-trang-diem": "Thiết Bị & Phụ Kiện Làm Đẹp",
    "tia-chan-may": "Thiết Bị & Phụ Kiện Làm Đẹp",
    "thuc-pham-chuc-nang": "Thực Phẩm Chức Năng",
    "sieu-deal-duoi-100k": "Khuyến Mãi",
    "best-seller": "Khuyến Mãi",
    "san-pham-moi": "Khuyến Mãi",
    "lam-thao-beauty": "Khuyến Mãi",
}

WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: Any) -> str:
    return WHITESPACE_RE.sub(" ", str(value or "").strip())


def fold_text(value: str) -> str:
    text = unicodedata.normalize("NFD", value.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d")


def slugify(value: str) -> str:
    folded = fold_text(value)
    folded = re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
    return folded


def to_int(value: Any) -> int | None:
    """Parse an integer, returning None when the value is missing/blank."""
    text = clean_text(value)
    if not text or text.lower() in {"nan", "none"}:
        return None
    try:
        return int(float(text.replace(",", "")))
    except ValueError:
        digits = re.sub(r"[^0-9-]", "", text)
        if digits in {"", "-"}:
            return None
        return int(digits)


def first_category(category_path: str) -> str:
    return clean_text(category_path).split("/")[0].strip()


def category_from_product_type(product_type: str) -> str | None:
    folded = fold_text(product_type)
    if not folded:
        return None

    hair_terms = [
        "toc",
        "dau goi",
        "dau xa",
        "u toc",
        "nhuom toc",
        "luoc",
    ]
    body_terms = [
        "body",
        "duong the",
        "sua tam",
        "khu mui",
        "vung kin",
        "cao long",
        "tay long",
        "bang ve sinh",
        "da tay",
        "tay/chan",
        "mun lung",
        "cham soc co the",
    ]
    skincare_terms = [
        "tinh chat",
        "serum",
        "mat na",
        "chong nang",
        "kem duong",
        "sua rua mat",
        "toner",
        "nuoc hoa hong",
        "nuoc tay trang",
        "tay trang",
        "tay te bao chet",
        "xit khoang",
        "mieng dan mun",
        "kem mat",
        "cham soc mat",
        "duong da",
        "sap tay trang",
    ]
    makeup_terms = [
        "son",
        "phan",
        "kem nen",
        "cushion",
        "ma hong",
        "ke mat",
        "ke chan may",
        "mascara",
        "long mi",
        "bam mi",
        "kich mi",
        "che khuyet",
        "tao khoi",
        "highlight",
        "co trang diem",
        "bong mut",
        "dung cu trang diem",
        "kem lot",
        "xit khoa nen",
        "nhu mat",
        "duong mi",
    ]
    personal_terms = [
        "rang mieng",
        "kem danh rang",
        "nuoc suc mieng",
        "cham soc ca nhan",
        "khau trang",
        "giay tham dau",
    ]
    accessory_terms = [
        "thiet bi",
        "dung cu",
        "tui dung my pham",
        "phu kien",
        "khan",
        "gau bong",
        "dao cao",
    ]

    if any(term in folded for term in hair_terms):
        return "Chăm Sóc Tóc Và Da Đầu"
    if "nuoc hoa hong" not in folded and (
        "nuoc hoa" in folded or "xit thom" in folded
    ):
        return "Nước Hoa"
    if any(term in folded for term in body_terms):
        return "Chăm Sóc Cơ Thể"
    if any(term in folded for term in skincare_terms):
        return "Chăm Sóc Da Mặt"
    if any(term in folded for term in makeup_terms):
        return "Trang Điểm"
    if any(term in folded for term in personal_terms):
        return "Chăm Sóc Cá Nhân"
    if "thuc pham chuc nang" in folded:
        return "Thực Phẩm Chức Năng"
    if "qua tang" in folded or "combo" in folded or "hang date" in folded:
        return "Khuyến Mãi"
    if any(term in folded for term in accessory_terms):
        return "Thiết Bị & Phụ Kiện Làm Đẹp"
    if folded == "khac":
        return "Khác"

    return None


def normalize_category(row: dict[str, str]) -> str:
    source = clean_text(row.get("source"))
    root = first_category(row.get("category_path", ""))

    if source == "hasaki":
        return HASAKI_CATEGORY_MAP.get(root, root or "Khác")

    product_type_category = category_from_product_type(clean_text(row.get("product_type")))
    if product_type_category:
        return product_type_category

    slug = slugify(root or clean_text(row.get("crawl_category_name")))
    return LAMTHAO_SLUG_MAP.get(slug, root or "Khác")


def parse_timestamp(value: str) -> datetime:
    text = clean_text(value)
    if not text:
        return datetime.min
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.min


def clean_row(row: dict[str, str], report: Counter[str]) -> dict[str, Any] | None:
    source = clean_text(row.get("source"))
    name = clean_text(row.get("name"))
    category = normalize_category(row)

    # --- Price noise filtering -------------------------------------------
    price = to_int(row.get("price"))

    if price is None:
        report["dropped_missing_price"] += 1
        return None
    if price == 0:
        report["dropped_price_zero"] += 1
        return None
    if price == 1:
        report["dropped_price_one"] += 1
        return None

    market_raw = to_int(row.get("market_price"))
    if market_raw is None:
        market_price = price
        report["market_price_imputed_from_price"] += 1
    else:
        market_price = market_raw
        if price > market_price:
            report["dropped_price_above_market"] += 1
            return None

    # --- Drop service / spa rows -----------------------------------------
    if category in SERVICE_CATEGORIES:
        report["dropped_service_spa"] += 1
        return None

    # --- Brand normalization ---------------------------------------------
    brand = clean_text(row.get("brand"))
    if not brand or brand == "Unknown":
        brand = "Không rõ"
        report["brand_unknown_to_khong_ro"] += 1

    # --- Stock normalization ---------------------------------------------
    stock_quantity = to_int(row.get("stock_quantity")) or 0
    if stock_quantity < 0:
        stock_quantity = 0
        report["stock_negative_to_zero"] += 1
    if stock_quantity >= STOCK_SENTINEL:
        stock_quantity = 0
        report["stock_sentinel_to_zero"] += 1

    sold_count = to_int(row.get("sold_count")) or 0
    if sold_count < 0:
        sold_count = 0
        report["sold_count_negative_to_zero"] += 1

    num_images = to_int(row.get("num_images")) or 0

    # --- Discount derivation ---------------------------------------------
    discount_amount = max(market_price - price, 0)
    discount_percent: float | int = (
        round((discount_amount / market_price) * 100, 2) if market_price else 0
    )
    if discount_percent == int(discount_percent):
        discount_percent = int(discount_percent)

    return {
        "source": source,
        "name": name,
        "brand": brand,
        "category": category,
        "num_images": num_images,
        "price": price,
        "market_price": market_price,
        "discount_amount": discount_amount,
        "discount_percent": discount_percent,
        "has_discount": 1 if discount_amount > 0 else 0,
        "sold_count": sold_count,
        "stock_quantity": stock_quantity,
        "scraped_at": clean_text(row.get("scraped_at")),
    }


def dedupe_rows(rows: list[dict[str, Any]], report: Counter[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["source"], row["name"]), []).append(row)

    output: list[dict[str, Any]] = []
    duplicate_keys = 0
    duplicate_rows_removed = 0

    for candidates in grouped.values():
        if len(candidates) == 1:
            output.append(candidates[0])
            continue

        duplicate_keys += 1
        duplicate_rows_removed += len(candidates) - 1
        candidates.sort(
            key=lambda row: (
                parse_timestamp(row["scraped_at"]),
                -int(row["price"]),
                int(row["stock_quantity"]),
                int(row["sold_count"]),
            ),
            reverse=True,
        )
        output.append(candidates[0])

    report["duplicate_keys_resolved"] = duplicate_keys
    report["duplicate_rows_removed"] = duplicate_rows_removed
    return output


def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = Counter((row["source"], row["name"]) for row in rows)
    categories = Counter(row["category"] for row in rows)

    return {
        "rows": len(rows),
        "duplicate_keys_remaining": sum(1 for count in keys.values() if count > 1),
        "negative_stock_remaining": sum(1 for row in rows if row["stock_quantity"] < 0),
        "missing_or_invalid_price_remaining": sum(
            1 for row in rows if row["price"] is None or row["price"] <= 1
        ),
        "service_spa_remaining": sum(
            1 for row in rows if row["category"] in SERVICE_CATEGORIES
        ),
        "price_above_market_remaining": sum(
            1 for row in rows if row["price"] > row["market_price"]
        ),
        "max_stock_quantity": max((row["stock_quantity"] for row in rows), default=0),
        "max_sold_count": max((row["sold_count"] for row in rows), default=0),
        "category_counts": categories.most_common(),
    }


def run(input_path: Path, output_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    report: Counter[str] = Counter()
    cleaned_rows: list[dict[str, Any]] = []
    for row in raw_rows:
        cleaned = clean_row(row, report)
        if cleaned is not None:
            cleaned_rows.append(cleaned)

    deduped_rows = dedupe_rows(cleaned_rows, report)
    deduped_rows.sort(key=lambda row: (row["source"], row["category"], row["name"]))

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(deduped_rows)

    return {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_rows": len(raw_rows),
        "output_rows": len(deduped_rows),
        "actions": dict(report),
        "validation": validate(deduped_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="all_products.csv", type=Path)
    parser.add_argument("--output", default="all_products_analysis_ready.csv", type=Path)
    args = parser.parse_args()

    report = run(args.input, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()