# -*- coding: utf-8 -*-
"""
crawl_all.py — Chạy "CÀO TẤT CẢ, ĐẦY ĐỦ" cho cả 2 trang, KHÔNG cần trông coi.

- Tự gọi run.py nhiều lần (mỗi lần là 1 "pass"), nhờ cơ chế --job nên RESUME:
  pass sau bỏ qua sản phẩm đã cào, chỉ làm phần còn lại. Lặp đến khi không thêm
  được sản phẩm mới (đã xong) hoặc đạt --max-passes.
- Chịu được gián đoạn/timeout: nếu 1 pass bị dừng giữa chừng, pass kế tiếp tiếp tục.

Ví dụ:
  python crawl_all.py                # cào đầy đủ cả 2 trang (Hasaki 14/14 + Lamthao)
  python crawl_all.py --site hasaki  # chỉ Hasaki deep 14/14
  python crawl_all.py --delay 0.3 --max-passes 100
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
RUN = os.path.join(HERE, "run.py")

def jsonl_count(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for ln in f if ln.strip())

def loop(site_args, jsonl_name, label, max_passes, delay):
    path = os.path.join(HERE, "output", jsonl_name)
    print(f"\n########## {label} ##########")
    for i in range(1, max_passes + 1):
        before = jsonl_count(path)
        print(f"\n----- {label} | PASS {i} (dang co {before} SP) -----")
        cmd = [PY, RUN] + site_args + ["--delay", str(delay), "--quiet"]
        try:
            subprocess.run(cmd, cwd=HERE, check=False)
        except KeyboardInterrupt:
            print("  (dung boi nguoi dung)"); return
        after = jsonl_count(path)
        print(f"  -> sau pass {i}: {after} SP (+{after - before})")
        if after == before:
            print(f"  [DONE] {label}: HOAN TAT (khong con SP moi).")
            return
    print(f"  [STOP] {label}: dat max-passes={max_passes} (chay lai de tiep tuc).")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=["both", "hasaki", "lamthao"], default="both")
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--max-passes", type=int, default=200)
    ap.add_argument("--job", default="full")
    args = ap.parse_args()

    if args.site in ("lamthao", "both"):
        loop(["lamthao", "--all-collections", "--job", args.job],
             f"lamthao_{args.job}.jsonl", "LAMTHAO (toan bo collection)",
             args.max_passes, args.delay)

    if args.site in ("hasaki", "both"):
        loop(["hasaki", "--top-only", "--detail", "--reviews", "--job", args.job],
             f"hasaki_{args.job}.jsonl", "HASAKI deep 14/14 (toan catalog)",
             args.max_passes, args.delay)

    print("\n=== XONG. Ket qua o output/*.json, *.csv, *.jsonl ===")

if __name__ == "__main__":
    main()
