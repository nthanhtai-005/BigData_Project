-- ============================================================
-- BAI TOAN 2 (Pig): Hieu qua cua Khoang Giam gia (Discount Bucket)
--   Hasaki vs Lam Thao
-- Phep toan co ban: FILTER, bincond (phan nhom), GROUP BY, AVG, COUNT
-- Output: source_name , discount_bucket , avg_sold_count , num_products
-- Thu muc output: /output/pig_discount_bucket
-- ============================================================

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

-- 1. Chi giu 2 san can so sanh
two_sources = FILTER raw BY (source_name == 'hasaki' OR source_name == 'lamthao');

-- 2. Phan nhom discount_percent thanh cac phan doan (bucket) bang toan tu dieu kien
bucketed = FOREACH two_sources GENERATE
    source_name,
    sold_count,
    (
        (discount_percent <= 10.0 ? '00-10%' :
        (discount_percent <= 20.0 ? '11-20%' :
        (discount_percent <= 30.0 ? '21-30%' :
        (discount_percent <= 50.0 ? '31-50%' : 'tren-50%'))))
    ) AS discount_bucket;

-- 3. Gom nhom theo (san, bucket)
grp = GROUP bucketed BY (source_name, discount_bucket);

-- 4. Tinh sold_count trung binh + dem so san pham trong moi bucket
result = FOREACH grp GENERATE
             group.source_name              AS source_name,
             group.discount_bucket           AS discount_bucket,
             (long) ROUND(AVG(bucketed.sold_count)) AS avg_sold_count,
             COUNT(bucketed)                 AS num_products;

-- 5. Sap xep theo san roi theo bucket
ordered = ORDER result BY source_name ASC, discount_bucket ASC;

-- 6. Ghi ket qua ra HDFS (CSV) va in ra man hinh
STORE ordered INTO '/output/pig_discount_bucket' USING PigStorage(',');
DUMP ordered;
