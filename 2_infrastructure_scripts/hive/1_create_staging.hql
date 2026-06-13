CREATE DATABASE IF NOT EXISTS bigdata_ecommerce;
USE bigdata_ecommerce;

-- TẠO 4 BẢNG STAGING (Đón dữ liệu từ Sqoop)
CREATE TABLE staging_sources (id INT, source_name STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;
CREATE TABLE staging_categories (id INT, category_name STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;
CREATE TABLE staging_brands (id INT, brand_name STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;
CREATE TABLE staging_products (
    id INT, source_id INT, category_id INT, brand_id INT, name STRING,
    num_images INT, price BIGINT, market_price BIGINT, discount_amount BIGINT,
    discount_percent FLOAT, has_discount INT, sold_count INT, stock_quantity INT, scraped_at STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;

-- KHÔNG DÙNG NỮA
