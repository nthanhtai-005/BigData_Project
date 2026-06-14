-- ============================================================
-- BAI TOAN 3 (Pig - DE TAI MOI): Quy mo Danh muc & Tong luong ban
--   So sanh SO SAN PHAM va TONG LUOT BAN theo tung Danh muc
--   giua 2 san Hasaki va Lam Thao
-- Phep toan co ban: FILTER, GROUP BY, COUNT, SUM
-- Output: source_name , category_name , total_products , total_sold
-- Thu muc output: /output/pig_category_scale
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

-- 2. Chi lay 3 cot can dung
proj = FOREACH two_sources GENERATE source_name, category_name, sold_count;

-- 3. Gom nhom theo (san, danh muc)
grp = GROUP proj BY (source_name, category_name);

-- 4. Dem so san pham (COUNT) va tinh tong luong ban (SUM)
result = FOREACH grp GENERATE
             group.source_name    AS source_name,
             group.category_name  AS category_name,
             COUNT(proj)           AS total_products,
             SUM(proj.sold_count)  AS total_sold;

-- 5. Sap xep: theo san, tong luong ban giam dan
ordered = ORDER result BY source_name ASC, total_sold DESC;

-- 6. Ghi ket qua ra HDFS (CSV) va in ra man hinh
STORE ordered INTO '/output/pig_category_scale' USING PigStorage(',');
DUMP ordered;
