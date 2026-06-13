from db_config import get_db_connection

def get_all_from_table(table_name):
    """Kéo toàn bộ dữ liệu từ một bảng bất kỳ về để hiển thị lên giao diện"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # NẾU LÀ BẢNG PRODUCTS -> Dùng LEFT JOIN để lấy Tên thay vì ID
            if table_name == "products":
                sql = """
                    SELECT p.id, s.source_name, c.category_name, b.brand_name, 
                           p.name, p.price, p.stock_quantity, p.scraped_at
                    FROM products p
                    LEFT JOIN sources s ON p.source_id = s.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    ORDER BY p.id DESC
                """
                cursor.execute(sql)
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
                
            records = cursor.fetchall()
            return records
        except Exception as e:
            print(f"❌ Lỗi đọc bảng {table_name}: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def delete_record(table_name, record_id):
    """Xóa một dòng trong bảng dựa vào ID"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql_delete = f"DELETE FROM {table_name} WHERE id = %s"
            cursor.execute(sql_delete, (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Lỗi xóa dữ liệu: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def insert_record(table_name, columns, values):
    """Thêm một dòng mới vào bảng bất kỳ"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cols_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            sql_insert = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
            cursor.execute(sql_insert, values)
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi thêm dữ liệu: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def update_record(table_name, record_id, columns, values):
    """Cập nhật dữ liệu cho một dòng bất kỳ"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{col} = %s" for col in columns])
            sql_update = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
            
            # Thêm ID vào cuối danh sách values để truyền vào biến %s cuối cùng
            update_values = list(values)
            update_values.append(record_id)
            
            cursor.execute(sql_update, tuple(update_values))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi cập nhật dữ liệu: {e}")
            return False
        finally:
            cursor.close()
            conn.close()