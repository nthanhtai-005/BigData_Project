import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        # Thay IP bằng IP máy Windows chứa MySQL
        connection = mysql.connector.connect(
            host='127.0.0.1', 
            database='bigdata_ecommerce',
            user='root',
            password='nthanhtai'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
    return None