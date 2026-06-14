# -*- coding: utf-8 -*-
"""
CLI cào dữ liệu sản phẩm Hasaki & Lamthao theo danh mục.

Ví dụ:
  python run.py hasaki  --categories cham-soc-da-mat-c4 --max-pages 1 --detail --reviews
  python run.py hasaki  --all-categories --max-pages 1 --no-detail
  python run.py lamthao --collections cham-soc-co-the --max-pages 2
  python run.py lamthao --all-collections --max-products 200

Output: scraper/output/<site>_<...>.{jsonl,json,csv}
"""
from __future__ import annotations
import argparse
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.http_client import HttpClient
from common.writer import OutputWriter
from common.schema import REQUIRED_FIELDS


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def run_hasaki(args) -> None:
    from hasaki.client import HasakiClient
    from hasaki import categories as cat
    from hasaki.scraper import HasakiScraper

    http = HttpClient(delay=args.delay, max_retries=args.retries, verbose=not args.quiet)
    client = HasakiClient(http=http, device_id=args.device_id)

    if args.top_only:
        cats = [{"key": k, "id": cat._id_from_key(k), "name": None} for k in cat.SEED_TOP_CATEGORIES]
    elif args.all_categories:
        cats = cat.discover(client, expand=not args.no_expand, verbose=not args.quiet)
    else:
        keys = args.categories or cat.SEED_TOP_CATEGORIES[:1]
        cats = [{"key": k, "id": cat._id_from_key(k), "name": None} for k in keys]

    scraper = HasakiScraper(
        client,
        with_detail=args.detail,
        with_reviews=args.reviews and args.detail,
        sample_reviews=args.sample_reviews,
        sample_comments=args.sample_comments,
        size=args.size,
        verbose=not args.quiet,
    )
    print(f"[HASAKI] {len(cats)} danh mục | detail={args.detail} reviews={scraper.with_reviews}"
          + (f" | JOB={args.job} (resume)" if args.job else ""))

    sink = _make_sink(args, "hasaki")
    skip = sink.skip_ids_for("hasaki") if args.job else set()
    try:
        for c in cats:
            print(f"\n>> Danh mục: {c['key']} ({c.get('name') or ''})")
            for up in scraper.scrape_category(c, max_pages=args.max_pages,
                                              max_products=args.max_products,
                                              skip_ids=skip):
                _emit(sink, up, args)
    finally:
        paths = _finish(sink, args)
        _summary("HASAKI", sink.count, paths, http)


def run_lamthao(args) -> None:
    from lamthao.client import LamthaoClient
    from lamthao import collections as col
    from lamthao.scraper import LamthaoScraper

    http = HttpClient(delay=args.delay, max_retries=args.retries, verbose=not args.quiet)
    client = LamthaoClient(http=http)

    if args.all_collections:
        cols = col.discover(client, verbose=not args.quiet)
    else:
        keys = args.collections or ["cham-soc-co-the"]
        cols = [{"key": k, "id": None, "name": None} for k in keys]

    scraper = LamthaoScraper(client, limit=args.size, verbose=not args.quiet)
    print(f"[LAMTHAO] {len(cols)} collection" + (f" | JOB={args.job} (resume)" if args.job else ""))

    sink = _make_sink(args, "lamthao")
    skip = sink.skip_ids_for("lamthao") if args.job else set()
    try:
        for c in cols:
            print(f"\n>> Collection: {c['key']} ({c.get('name') or ''})")
            for up in scraper.scrape_collection(c, max_pages=args.max_pages,
                                                max_products=args.max_products,
                                                skip_ids=skip):
                _emit(sink, up, args)
    finally:
        paths = _finish(sink, args)
        _summary("LAMTHAO", sink.count, paths, http)


def _make_sink(args, site):
    """Trả JobStore (nếu --job) hoặc OutputWriter (timestamp)."""
    if args.job:
        from common.jobstore import JobStore
        return JobStore(args.out_dir, f"{site}_{args.job}")
    return OutputWriter(args.out_dir, f"{site}_{_timestamp()}", formats=args.formats)


def _emit(sink, up, args) -> None:
    if hasattr(sink, "add"):      # JobStore
        sink.add(up)
    else:                          # OutputWriter
        sink.write(up)
    if not args.quiet:
        _print_progress(up, sink.count)


def _finish(sink, args):
    if hasattr(sink, "finalize"):  # JobStore
        fmts = [f for f in args.formats if f in ("json", "csv")]
        return sink.finalize(formats=fmts or ("json", "csv"))
    return sink.close()


def _print_progress(up, n) -> None:
    price = f"{up.price:,}".replace(",", ".") if up.price else "?"
    market = f"{up.market_price:,}".replace(",", ".") if up.market_price else "?"
    print(f"   #{n:<4} [{up.product_id}] {str(up.name)[:46]:46s} "
          f"{price}đ/{market}đ -{up.discount_percent or 0}% "
          f"⭐{up.rating_average or '-'} bán={up.sold_count or '-'} kho={up.stock_quantity or '-'}")


def _summary(site, count, paths, http) -> None:
    print("\n" + "=" * 70)
    print(f"[{site}] HOÀN TẤT: {count} sản phẩm")
    print(f"  HTTP: requests={http.stats['requests']} retries={http.stats['retries']} errors={http.stats['errors']}")
    for fmt, p in paths.items():
        print(f"  -> {fmt}: {p}")
    print("=" * 70)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cào sản phẩm Hasaki & Lamthao theo danh mục")
    sub = p.add_subparsers(dest="site", required=True)

    def common_opts(sp):
        sp.add_argument("--max-pages", type=int, default=None, help="Giới hạn số trang/danh mục")
        sp.add_argument("--max-products", type=int, default=None, help="Giới hạn tổng sản phẩm")
        sp.add_argument("--size", type=int, default=40, help="Số sản phẩm mỗi trang (Hasaki<=40, Lamthao<=50)")
        sp.add_argument("--delay", type=float, default=0.6, help="Độ trễ giữa request (giây)")
        sp.add_argument("--retries", type=int, default=4, help="Số lần retry")
        sp.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"))
        sp.add_argument("--formats", nargs="+", default=["jsonl", "json", "csv"],
                        choices=["jsonl", "json", "csv"])
        sp.add_argument("--job", default=None,
                        help="Tên job để RESUME (chạy lại sẽ tiếp tục, bỏ qua SP đã cào). "
                             "Ghi vào output/<site>_<job>.jsonl + .json + .csv")
        sp.add_argument("--quiet", action="store_true")

    # hasaki
    h = sub.add_parser("hasaki", help="Cào Hasaki.vn")
    common_opts(h)
    h.add_argument("--categories", nargs="+", help="slug-c<id>, vd cham-soc-da-mat-c4")
    h.add_argument("--all-categories", action="store_true", help="Tự khám phá toàn bộ danh mục")
    h.add_argument("--top-only", action="store_true",
                   help="Chỉ dùng các danh mục cấp cao (phủ toàn sàn, ít trùng) — tốt cho cào TẤT CẢ")
    h.add_argument("--no-expand", action="store_true", help="Không mở rộng cây con khi --all-categories")
    h.add_argument("--detail", dest="detail", action="store_true", default=True,
                   help="Lấy chi tiết (mặc định bật)")
    h.add_argument("--no-detail", dest="detail", action="store_false",
                   help="Chỉ lấy listing (nhanh, vẫn đủ #1-8,12,14)")
    h.add_argument("--reviews", dest="reviews", action="store_true", default=True,
                   help="Lấy sao/comment (mặc định bật, cần --detail)")
    h.add_argument("--no-reviews", dest="reviews", action="store_false")
    h.add_argument("--sample-reviews", type=int, default=5, help="Số review mẫu/sản phẩm")
    h.add_argument("--sample-comments", type=int, default=5, help="Số comment mẫu/sản phẩm")
    h.add_argument("--device-id", default=None, help="mobiledeviceid (mặc định random UUID)")
    h.set_defaults(func=run_hasaki)

    # lamthao
    l = sub.add_parser("lamthao", help="Cào Lamthaocosmetics.vn")
    common_opts(l)
    l.add_argument("--collections", nargs="+", help="handle collection, vd cham-soc-co-the")
    l.add_argument("--all-collections", action="store_true", help="Tự khám phá toàn bộ collection")
    l.set_defaults(func=run_lamthao)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    # Lamthao size mặc định 50
    if args.site == "lamthao" and args.size == 40:
        args.size = 50
    args.func(args)


if __name__ == "__main__":
    main()
