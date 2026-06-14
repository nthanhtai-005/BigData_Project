#!/bin/bash
# ============================================================
# run_all.sh - Chay lan luot ca 4 chuong trinh MapReduce bang Pig
# Cach dung:  bash run_all.sh
# (Dat file nay cung thu muc voi 4 file .pig)
# ============================================================

set -e  # gap loi la dung

# Thu muc chua cac file .pig (mac dinh la thu muc hien tai)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===================================================="
echo " XOA CAC THU MUC OUTPUT CU TREN HDFS (neu co)"
echo "===================================================="
hdfs dfs -rm -r -f /output/pig_price_gap
hdfs dfs -rm -r -f /output/pig_discount_bucket
hdfs dfs -rm -r -f /output/pig_category_scale
hdfs dfs -rm -r -f /output/pig_price_range

echo "===================================================="
echo " [1/4] BAI TOAN 1: PRICE GAP"
echo "===================================================="
pig -x mapreduce "$SCRIPT_DIR/01_price_gap.pig"

echo "===================================================="
echo " [2/4] BAI TOAN 2: DISCOUNT BUCKET"
echo "===================================================="
pig -x mapreduce "$SCRIPT_DIR/02_discount_bucket.pig"

echo "===================================================="
echo " [3/4] BAI TOAN 3: CATEGORY SCALE (COUNT + SUM)"
echo "===================================================="
pig -x mapreduce "$SCRIPT_DIR/03_category_scale.pig"

echo "===================================================="
echo " [4/4] BAI TOAN 4: PRICE RANGE (MIN + MAX + AVG)"
echo "===================================================="
pig -x mapreduce "$SCRIPT_DIR/04_price_range.pig"

echo ""
echo "===================================================="
echo " XONG! XEM KET QUA TREN HDFS:"
echo "===================================================="
echo "--- /output/pig_price_gap ---"
hdfs dfs -cat /output/pig_price_gap/part-*
echo "--- /output/pig_discount_bucket ---"
hdfs dfs -cat /output/pig_discount_bucket/part-*
echo "--- /output/pig_category_scale ---"
hdfs dfs -cat /output/pig_category_scale/part-*
echo "--- /output/pig_price_range ---"
hdfs dfs -cat /output/pig_price_range/part-*
