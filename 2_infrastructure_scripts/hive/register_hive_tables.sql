CREATE DATABASE IF NOT EXISTS bigdata_ecommerce;

USE bigdata_ecommerce;

-- Xóa các định nghĩa bảng cũ (nếu có)
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS brands;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS sources;

-- Đăng ký bảng sources
CREATE EXTERNAL TABLE sources (
    id BIGINT,
    source_name STRING
)
STORED AS PARQUET
LOCATION 'hdfs:///data/bigdata_ecommerce/hive/sources';

-- Đăng ký bảng categories
CREATE EXTERNAL TABLE categories (
    id BIGINT,
    category_name STRING
)
STORED AS PARQUET
LOCATION 'hdfs:///data/bigdata_ecommerce/hive/categories';

-- Đăng ký bảng brands
CREATE EXTERNAL TABLE brands (
    id BIGINT,
    brand_name STRING
)
STORED AS PARQUET
LOCATION 'hdfs:///data/bigdata_ecommerce/hive/brands';

-- Đăng ký bảng products (ĐÃ BỔ SUNG ĐẦY ĐỦ CÁC CỘT)
CREATE EXTERNAL TABLE products (
    id BIGINT,
    name STRING,
    source_id BIGINT,
    brand_id BIGINT,
    price DOUBLE,
    discount_percent DOUBLE,
    sold_count BIGINT,
    -- CÁC CỘT MỚI BỔ SUNG
    num_images BIGINT,
    market_price DOUBLE,
    discount_amount DOUBLE,
    has_discount INT,
    stock_quantity BIGINT,
    scraped_at STRING
)
PARTITIONED BY (
    category_id BIGINT
)
STORED AS PARQUET
LOCATION 'hdfs:///data/bigdata_ecommerce/hive/final_products';

-- Cập nhật partition cho bảng products
MSCK REPAIR TABLE products;

-- Kiểm tra lại danh sách bảng
SHOW TABLES;

-- Kiểm tra lại các partition
SHOW PARTITIONS products;

-- Đếm số lượng sản phẩm để xác nhận dữ liệu đã được nạp đủ
SELECT COUNT(*) AS total_products
FROM products;