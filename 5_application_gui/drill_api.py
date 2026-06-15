import requests
import pandas as pd

DRILL_HOST = "192.168.150.178" 
DRILL_PORT = 8047

def execute_drill_query(sql_query, task_name=""):
    """Hàm lõi gọi API Drill dùng chung cho tất cả các bài toán"""
    url = f"http://{DRILL_HOST}:{DRILL_PORT}/query.json"
    payload = {"queryType": "SQL", "query": sql_query}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('rows', [])
            if len(data) > 0:
                print(f"[{task_name}] THÀNH CÔNG: Lấy được {len(data)} dòng dữ liệu.")
                return pd.DataFrame(data)
            else:
                print(f"[{task_name}] CẢNH BÁO: Chưa có dữ liệu trên HDFS (Thư mục rỗng).")
        else:
            print(f"[{task_name}] LỖI TỪ DRILL: {response.text}")
    except Exception as e:
        print(f"[{task_name}] Lỗi mạng/Timeout: {e}")
    
    return pd.DataFrame()

def get_oos_rate_data():
    sql = """
        SELECT columns[0] AS category_name, columns[3] AS oos_rate 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/9_oos_rate_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
        WHERE columns[0] <> 'category_name'
    """
    df = execute_drill_query(sql, "Tỷ lệ cháy hàng")
    if not df.empty:
        df['oos_rate'] = pd.to_numeric(df['oos_rate'])
    return df

def get_price_elasticity_data():
    sql = """
        SELECT columns[0] AS price_bucket, columns[1] AS total_sold_volume 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/10_price_elasticity_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
        WHERE columns[0] <> 'price_bucket'
    """
    df = execute_drill_query(sql, "Độ co giãn giá")
    if not df.empty:
        df['total_sold_volume'] = pd.to_numeric(df['total_sold_volume'])
    return df

def get_category_count_data():
    sql = """
        SELECT columns[0] AS category_name, columns[1] AS total_products 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/11_category_count_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
    """
    df = execute_drill_query(sql, "Bài 1: Phân bố Danh mục")
    if not df.empty:
        df['total_products'] = pd.to_numeric(df['total_products'])
    return df

def get_category_price_data():
    sql = """
        SELECT columns[0] AS category_name, columns[1] AS avg_price, columns[2] AS avg_market_price 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/12_category_price_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
    """
    df = execute_drill_query(sql, "Bài 2: Giá Danh mục")
    if not df.empty:
        df['avg_price'] = pd.to_numeric(df['avg_price'])
        df['avg_market_price'] = pd.to_numeric(df['avg_market_price'])
    return df

def get_brand_price_compare_data():
    sql = """
        SELECT columns[0] AS brand_name, columns[1] AS avg_price_hasaki, columns[2] AS avg_price_lamthao, columns[3] AS total_sold
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/13_brand_price_compare_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
    """
    df = execute_drill_query(sql, "Bài 3: So sánh Shop")
    if not df.empty:
        df['avg_price_hasaki'] = pd.to_numeric(df['avg_price_hasaki'])
        df['avg_price_lamthao'] = pd.to_numeric(df['avg_price_lamthao'])
        df['total_sold'] = pd.to_numeric(df['total_sold'])
    return df

MAPREDUCE_JOBS_CONFIG = {
    "Bài 1: So sánh Thương hiệu theo từng Danh mục": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/category_winner",
        "delimiter": "\\t",
        "columns": ["category", "winning_brand", "max_sold"]
    },
    "Bài 2: Tác động của Hình ảnh đến Sức mua theo Phân khúc Giá": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/image_impact",
        "delimiter": "\\t",
        "columns": ["price_tier", "num_images", "avg_sold_count"]
    },
    "Bài 3: Phân loại Sản phẩm theo Ma trận BCG": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/bcg_matrix", 
        "delimiter": "\\t",
        "columns": ["brand", "product_name", "sold_count", "discount_percent"],
        "include_dir": True  
    },
    "Bài 4: Top 10 Sản phẩm có nhu cầu cao nhất": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/top_10_out_of_stock",
        "delimiter": "\\t",
        "columns": ["category", "brand", "total_stock", "total_capital"]
    },
    "Bài 5: Cán cân Vốn ngâm Hàng tồn kho theo Danh mục": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/inventory_capital",
        "delimiter": "\\t",
        "columns": ["category", "brand", "total_stock", "total_capital"]
    },
    "Bài 6: Tổng doanh thu và Tỷ lệ sale trung bình": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/brand_revenue",
        "delimiter": "\\t",
        "columns": ["brand", "total_revenue"]
    },
    "Bài 7: Cảnh báo tỉ lệ cháy hàng theo ngành hàng": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/9_oos_rate_python",
        "delimiter": ",",
        "columns": ["category_name", "total_products", "total_oos", "oos_rate_percent"]
    },
    "Bài 8: Đo lường độ co giãn của cầu theo phân khúc giá": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/10_price_elasticity_python",
        "delimiter": ",",
        "columns": ["price_bucket", "total_sold_volume"]
    },
    "Bài 9: Phân bố Số lượng Sản phẩm theo Danh mục": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/11_category_count_python",
        "delimiter": ",",
        "columns": ["category_name", "total_products"]
    },
    "Bài 10: So sánh Giá bán trung bình và Giá gốc": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/12_category_price_python",
        "delimiter": ",",
        "columns": ["category_name", "avg_price", "avg_market_price"]
    },
    "Bài 11: Cạnh tranh Giá bán Thương hiệu Hasaki vs Lam Thảo": {
        "path": "/data/bigdata_ecommerce/mapreduce_output/13_brand_price_compare_python",
        "delimiter": ",",
        "columns": ["brand_name", "avg_price_hasaki", "avg_price_lamthao", "total_sold"]
    },
    "Bài 12: Pig - So sánh mức độ Thổi giá (Price Gap) Hasaki vs Lam Thảo": {
        "path": "/output/pig_price_gap",
        "delimiter": "\\t",
        "columns": ["brand", "category", "avg_price_gap"]
    },
    "Bài 13: Pig - Đánh giá Hiệu quả Khoảng Giảm giá của 2 thương hiệu": {
        "path": "/output/pig_discount_bucket",
        "delimiter": ",",
        "columns": ["brand", "discount_bucket", "avg_sold_count"]
    },
    "Bài 14: Pig - Quy mô và Doanh số theo Danh mục": {
        "path": "/output/pig_category_scale",
        "delimiter": ",",
        "columns": ["source_name", "category_name", "total_products", "total_sold"]
    },
    "Bài 15: Pig - Phân khúc Giá theo Danh mục": {
        "path": "/output/pig_price_range",
        "delimiter": ",",
        "columns": ["source_name", "category_name", "min_price", "max_price", "avg_price"]
    }
}

def get_raw_mapreduce_data(job_title):
    """Hàm tự động sinh câu SQL để lấy dữ liệu thô cho một bài toán bất kỳ"""
    config = MAPREDUCE_JOBS_CONFIG.get(job_title)
    if not config: return pd.DataFrame()
    
    # Sinh cú pháp SELECT columns[0] AS col1, columns[1] AS col2...
    select_clause = ", ".join([f"columns[{i}] AS {col}" for i, col in enumerate(config["columns"])])
    
    # NẾU CÓ CỜ INCLUDE_DIR, THÊM CỘT TÊN THƯ MỤC LÊN ĐẦU TIÊN
    if config.get("include_dir"):
        select_clause = "dir0 AS bcg_group, " + select_clause

    path = config["path"]
    delimiter = config["delimiter"]
    first_col = config["columns"][0]
    
    sql = f"""
        SELECT {select_clause} 
        FROM table(dfs.`{path}`(type => 'text', fieldDelimiter => '{delimiter}', extractHeader => false))
        WHERE columns[0] IS NOT NULL AND columns[0] <> '{first_col}'
    """
    
    return execute_drill_query(sql, job_title)