-- TẠO 4 BẢNG CHÍNH THỨC (Parquet + Partition)
CREATE TABLE sources (id INT, source_name STRING) STORED AS PARQUET;
CREATE TABLE categories (id INT, category_name STRING) STORED AS PARQUET;
CREATE TABLE brands (id INT, brand_name STRING) STORED AS PARQUET;
CREATE TABLE final_products (
    id INT, source_id INT, brand_id INT, name STRING, num_images INT, price BIGINT, 
    market_price BIGINT, discount_amount BIGINT, discount_percent FLOAT, 
    has_discount INT, sold_count INT, stock_quantity INT, scraped_at STRING
) PARTITIONED BY (category_id INT) STORED AS PARQUET;

-- TẠO BẢNG PHẲNG (Phục vụ riêng cho MapReduce)
CREATE TABLE flat_products_for_mapreduce (
    id INT, name STRING, source_name STRING, category_name STRING, brand_name STRING,
    price BIGINT, discount_percent FLOAT, sold_count INT
) STORED AS PARQUET;

-- KHÔNG DÙNG NỮA