CREATE DATABASE IF NOT EXISTS bigdata_ecommerce;
USE bigdata_ecommerce;

-- 1. Tạo bảng Nguồn dữ liệu
CREATE TABLE sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE -- UNIQUE để không bị trùng lặp tên nguồn
);

-- 2. Tạo bảng Danh mục
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE
);

-- 3. Tạo bảng Thương hiệu
CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE
);

-- 4. Tạo bảng Sản phẩm (Bảng chính có chứa Khóa ngoại)
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT,        -- Khóa ngoại liên kết bảng sources
    category_id INT,      -- Khóa ngoại liên kết bảng categories
    brand_id INT,         -- Khóa ngoại liên kết bảng brands
    name VARCHAR(500),
    num_images INT,
    price BIGINT,
    market_price BIGINT,
    discount_amount BIGINT,
    discount_percent FLOAT,
    has_discount TINYINT(1),
    sold_count INT,
    stock_quantity INT,
    scraped_at VARCHAR(50),
    
    -- Khai báo các ràng buộc Khóa ngoại
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);
