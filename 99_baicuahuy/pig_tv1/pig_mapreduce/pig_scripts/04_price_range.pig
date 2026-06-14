-- ============================================================
-- BAI TOAN 4 (Pig - DE TAI MOI): Khung gia san pham theo Danh muc
--   Gia thap nhat (MIN) - cao nhat (MAX) - trung binh (AVG)
--   cua moi san Hasaki va Lam Thao, theo tung Danh muc
-- Phep toan co ban: FILTER, GROUP BY, MIN, MAX, AVG, ORDER BY
-- Output: source_name , category_name , min_price , max_price , avg_price
-- Thu muc output: /output/pig_price_range
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

-- 2. Bo cac dong gia khong hop le (phong khi du lieu ban)
valid = FILTER two_sources BY price > 0;

-- 3. Chi lay 3 cot can dung
proj = FOREACH valid GENERATE source_name, category_name, price;

-- 4. Gom nhom theo (san, danh muc)
grp = GROUP proj BY (source_name, category_name);

-- 5. Tinh MIN, MAX, AVG gia trong moi nhom
result = FOREACH grp GENERATE
             group.source_name    AS source_name,
             group.category_name  AS category_name,
             (long) MIN(proj.price)        AS min_price,
             (long) MAX(proj.price)        AS max_price,
             (long) ROUND(AVG(proj.price)) AS avg_price;

-- 6. Sap xep: theo san, gia cao nhat giam dan
ordered = ORDER result BY source_name ASC, max_price DESC;

-- 7. Ghi ket qua ra HDFS (CSV) va in ra man hinh
STORE ordered INTO '/output/pig_price_range' USING PigStorage(',');
DUMP ordered;
