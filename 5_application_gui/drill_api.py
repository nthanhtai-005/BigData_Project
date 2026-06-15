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

def get_t1_brand_comparison():
    sql = """
        SELECT columns[0] as category, columns[1] as winning_brand, CAST(columns[2] AS INT) as max_sold 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/category_winner`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 1: So sánh thương hiệu")

def get_t2_image_impact():
    sql = """
        SELECT columns[0] as price_tier, CAST(columns[1] AS INT) as num_images, CAST(columns[2] AS FLOAT) as avg_sold_count 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/image_impact`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 2: Tác động hình ảnh")

def get_t3_bcg_matrix():
    sql = """
        SELECT columns[0] as brand, columns[1] as product_name, CAST(columns[2] AS INT) as sold_count, CAST(columns[3] AS FLOAT) as discount_percent, 'Star' as quadrant
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/bcg_matrix/stars`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
        UNION ALL
        SELECT columns[0] as brand, columns[1] as product_name, CAST(columns[2] AS INT) as sold_count, CAST(columns[3] AS FLOAT) as discount_percent, 'Cash Cow' as quadrant
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/bcg_matrix/cows`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
        UNION ALL
        SELECT columns[0] as brand, columns[1] as product_name, CAST(columns[2] AS INT) as sold_count, CAST(columns[3] AS FLOAT) as discount_percent, 'Dog' as quadrant
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/bcg_matrix/dogs`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 3: Ma trận BCG")

def get_t4_top10_oos():
    sql = """
        SELECT columns[0] as brand, columns[1] as product_name, CAST(columns[2] AS INT) as sold_count
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/top_10_out_of_stock`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 4: Top 10 đứt gãy")

def get_t5_inventory_capital():
    sql = """
        SELECT columns[0] as category, columns[1] as brand, CAST(columns[2] AS INT) as total_stock, CAST(columns[3] AS FLOAT) as total_capital 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/inventory_capital`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 5: Vốn ngâm")

def get_t6_revenue_discount():
    sql = """
        SELECT columns[0] as brand, CAST(columns[1] AS FLOAT) as total_revenue, CAST(columns[2] AS FLOAT) as avg_discount_percent 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/brand_revenue`(type => 'text', fieldDelimiter => '\t', extractHeader => false))
    """
    return execute_drill_query(sql, "Bài 6: Doanh thu & Tỷ lệ sale")