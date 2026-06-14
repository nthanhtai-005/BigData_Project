import requests
import pandas as pd

DRILL_HOST = "192.168.150.178" 
DRILL_PORT = 8047

def get_oos_rate_data():
    # Lưu ý: Cần kiểm tra kỹ tên file part-00000 hay part-r-00000
    sql = """
        SELECT columns[0] AS category_name, 
               columns[3] AS oos_rate 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/9_oos_rate_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
        WHERE columns[0] <> 'category_name'
    """
    
    url = f"http://{DRILL_HOST}:{DRILL_PORT}/query.json"
    payload = {"queryType": "SQL", "query": sql}
    headers = {"Content-Type": "application/json"}

    try:
        print("⏳ Đang gọi dữ liệu từ Apache Drill...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Nếu thành công 100%
        if response.status_code == 200:
            data = response.json().get('rows', [])
            if len(data) > 0:
                print(f"THÀNH CÔNG: Lấy được {len(data)} dòng dữ liệu từ HDFS!")
                df = pd.DataFrame(data)
                df['oos_rate'] = pd.to_numeric(df['oos_rate'])
                return df
            else:
                print("CẢNH BÁO: Drill chạy thành công nhưng file không có dữ liệu (0 dòng).")
        # Nếu SQL sai hoặc đường dẫn sai
        else:
            print(f"LỖI TỪ DRILL (Mã {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"Lỗi mạng/Timeout: {e}")
    
    return pd.DataFrame()

# ================= 2. HÀM LẤY DỮ LIỆU ĐỘ CO GIÃN THEO GIÁ =================
def get_price_elasticity_data():
    sql = """
        SELECT columns[0] AS price_bucket, 
               columns[1] AS total_sold_volume 
        FROM table(dfs.`/data/bigdata_ecommerce/mapreduce_output/10_price_elasticity_python/part-00000`(type => 'text', fieldDelimiter => ',', extractHeader => false))
        WHERE columns[0] <> 'price_bucket'
    """
    
    url = f"http://{DRILL_HOST}:{DRILL_PORT}/query.json"
    payload = {"queryType": "SQL", "query": sql}
    headers = {"Content-Type": "application/json"}

    try:
        print("⏳ Đang gọi dữ liệu Độ co giãn giá từ Apache Drill...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json().get('rows', [])
            if len(data) > 0:
                print(f"THÀNH CÔNG: Lấy được {len(data)} dòng dữ liệu Độ co giãn giá!")
                df = pd.DataFrame(data)
                df['total_sold_volume'] = pd.to_numeric(df['total_sold_volume'])
                return df
            else:
                print("CẢNH BÁO (Độ co giãn): Drill chạy thành công nhưng file không có dữ liệu (0 dòng).")
        else:
            print(f"LỖI TỪ DRILL (Độ co giãn - Mã {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"Lỗi mạng/Timeout (Độ co giãn): {e}")
    
    return pd.DataFrame()