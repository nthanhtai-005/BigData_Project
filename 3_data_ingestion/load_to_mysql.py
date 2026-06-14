import pandas as pd
from sqlalchemy import create_engine, text

# 1. Kết nối MySQL
USER = 'root'
PASSWORD = '123456'
HOST = 'localhost'
PORT = '3306'
DATABASE = 'bigdata_ecommerce'

engine = create_engine(f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")

# 2. Đọc và làm sạch CSV
df = pd.read_csv('all_products_analysis_ready.csv')

# Điền giá trị mặc định theo đúng kiểu dữ liệu
str_cols = ['source', 'category', 'brand', 'name', 'scraped_at']
int_cols = ['num_images', 'price', 'market_price', 'discount_amount',
            'sold_count', 'stock_quantity', 'has_discount']

for col in str_cols:
    if col in df.columns:
        df[col] = df[col].fillna('Unknown').str.strip()

for col in int_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

if 'discount_percent' in df.columns:
    df['discount_percent'] = df['discount_percent'].fillna(0.0)

# Lọc bỏ hàng thiếu các trường quan trọng
df = df[(df['source'] != '') & (df['category'] != '') & (df['brand'] != '')]
print(f"   Số dòng hợp lệ: {len(df)}")

# 3. Đẩy vào bảng tạm
df.to_sql(name='staging_products', con=engine, if_exists='replace', index=False)

# 4. Phân bổ vào 4 bảng chính
with engine.begin() as conn:
    # Xóa dữ liệu cũ để tránh trùng lặp khi chạy lại
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    conn.execute(text("TRUNCATE TABLE products;"))
    conn.execute(text("TRUNCATE TABLE sources;"))
    conn.execute(text("TRUNCATE TABLE categories;"))
    conn.execute(text("TRUNCATE TABLE brands;"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

    # Insert vào bảng lookup
    conn.execute(text("INSERT IGNORE INTO sources (source_name) SELECT DISTINCT source FROM staging_products;"))
    conn.execute(text("INSERT IGNORE INTO categories (category_name) SELECT DISTINCT category FROM staging_products;"))
    conn.execute(text("INSERT IGNORE INTO brands (brand_name) SELECT DISTINCT brand FROM staging_products;"))

    # Insert vào bảng chính
    conn.execute(text("""
        INSERT INTO products (
            source_id, category_id, brand_id, name, num_images,
            price, market_price, discount_amount, discount_percent,
            has_discount, sold_count, stock_quantity, scraped_at
        )
        SELECT
            s.id, c.id, b.id,
            st.name, st.num_images, st.price, st.market_price, st.discount_amount,
            st.discount_percent, st.has_discount, st.sold_count, st.stock_quantity, st.scraped_at
        FROM staging_products st
        JOIN sources s ON st.source = s.source_name
        JOIN categories c ON st.category = c.category_name
        JOIN brands b ON st.brand = b.brand_name;
    """))

    # Kiểm tra số dòng đã insert
    count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
    print(f"  Đã insert {count} sản phẩm vào bảng products")

    # Dọn bảng tạm
    conn.execute(text("DROP TABLE staging_products;"))

print(" Dữ liệu đã được đưa vào MySQL thành công.")
