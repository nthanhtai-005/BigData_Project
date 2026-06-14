-- ============================================================
-- BAI TOAN 1 (Pig): So sanh muc "Thoi gia" (Price Gap)
--   giua 2 san Hasaki va Lam Thao theo tung Danh muc
-- Phep toan co ban: FILTER, FOREACH (tinh hieu so), GROUP BY, AVG
-- Output: source_name , category_name , avg_price_gap
-- Thu muc output: /output/pig_price_gap
-- ============================================================

-- 1. Nap du lieu TSV (dau vao MapReduce do ETL sinh ra tren HDFS).
--    Day chinh la du lieu nam duoi bang Hive external 'mapreduce_input_tsv',
--    KHONG phai file csv mau o may ca nhan.
raw = LOAD '/data/bigdata_ecommerce/mapreduce_input/part-*'
      USING PigStorage('\t') AS (
          id:int,
          name:chararray,
          source_id:int,
          brand_id:int,
          source_name:chararray,
          category_name:chararray,
          brand_name:chararray,
          num_images:int,
          price:double,
          market_price:double,
          discount_amount:double,
          discount_percent:double,
          has_discount:int,
          sold_count:long,
          stock_quantity:long,
          scraped_at:chararray,
          category_id:int
      );

-- 2. Chi giu 2 san can so sanh (Hasaki vs Lam Thao)
two_sources = FILTER raw BY (source_name == 'hasaki' OR source_name == 'lamthao');

-- 3. Tinh hieu so market_price - price (muc tro gia / thoi gia)
with_gap = FOREACH two_sources GENERATE
               source_name,
               category_name,
               (market_price - price) AS price_gap;

-- 4. Gom nhom theo (san, danh muc)
grp = GROUP with_gap BY (source_name, category_name);

-- 5. Tinh trung binh price_gap cho tung nhom
result = FOREACH grp GENERATE
             group.source_name             AS source_name,
             group.category_name           AS category_name,
             (long) ROUND(AVG(with_gap.price_gap)) AS avg_price_gap;

-- 6. Sap xep cho de doc: theo san, gap giam dan
ordered = ORDER result BY source_name ASC, avg_price_gap DESC;

-- 7. Ghi ket qua ra HDFS (CSV) va in ra man hinh de chup hinh
STORE ordered INTO '/output/pig_price_gap' USING PigStorage(',');
DUMP ordered;
