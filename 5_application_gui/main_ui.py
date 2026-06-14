import customtkinter as ctk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from drill_api import get_oos_rate_data, get_price_elasticity_data

# IMPORT CÁC HÀM XỬ LÝ DATABASE THẬT
from crud_mysql import get_all_from_table, insert_record, update_record, delete_record

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_SCHEMA = {
    "products": {"columns": ["id", "source_id", "category_id", "brand_id", "name", "price", "stock_quantity"], "foreign_keys": {"source_id": "sources", "category_id": "categories", "brand_id": "brands"}},
    "brands": {"columns": ["id", "brand_name"], "foreign_keys": {}},
    "categories": {"columns": ["id", "category_name"], "foreign_keys": {}},
    "sources": {"columns": ["id", "source_name"], "foreign_keys": {}}
}

class ECommerceDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Data Warehouse Dashboard - Group 10")
        
        # Mở full màn hình (Maximized) ngay khi khởi động
        self.after(0, lambda: self.state('zoomed'))
        
        self.current_table = "products"

        self.setup_sidebar()
        self.setup_crud_frame()
        self.setup_mapreduce_frame()

        self.select_frame("CRUD")

    # ================= 1. SIDEBAR =================
    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#e9ecef")
        self.sidebar_frame.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar_frame, text="ADMIN PANEL", font=("Arial", 20, "bold"), text_color="black").pack(pady=(30, 20))

        self.btn_menu_crud = ctk.CTkButton(self.sidebar_frame, text="📦 Quản lý Dữ liệu", command=lambda: self.select_frame("CRUD"), fg_color="transparent", text_color="black", hover_color="#dee2e6", anchor="w")
        self.btn_menu_crud.pack(pady=10, padx=20, fill="x")

        self.btn_menu_chart = ctk.CTkButton(self.sidebar_frame, text="📊 Báo cáo MapReduce", command=lambda: self.select_frame("CHART"), fg_color="transparent", text_color="black", hover_color="#dee2e6", anchor="w")
        self.btn_menu_chart.pack(pady=10, padx=20, fill="x")

    def select_frame(self, frame_name):
        self.btn_menu_crud.configure(fg_color=("#ced4da" if frame_name == "CRUD" else "transparent"))
        self.btn_menu_chart.configure(fg_color=("#ced4da" if frame_name == "CHART" else "transparent"))

        if frame_name == "CRUD":
            self.mapreduce_frame.pack_forget()
            self.crud_frame.pack(side="right", fill="both", expand=True)
        else:
            self.crud_frame.pack_forget()
            self.mapreduce_frame.pack(side="right", fill="both", expand=True)

    # ================= 2. KHÔNG GIAN QUẢN LÝ DỮ LIỆU (CRUD) =================
    def setup_crud_frame(self):
        self.crud_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        top_frame = ctk.CTkFrame(self.crud_frame, fg_color="#f8f9fa")
        top_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(top_frame, text="Bảng:", font=("Arial", 14, "bold"), text_color="black").pack(side="left", padx=10, pady=15)
        self.combo_tables = ctk.CTkComboBox(top_frame, values=list(DB_SCHEMA.keys()), command=self.on_table_change, width=130)
        self.combo_tables.set(self.current_table)
        self.combo_tables.pack(side="left", padx=10)

        ctk.CTkLabel(top_frame, text="  |  Tìm kiếm:", font=("Arial", 14, "bold"), text_color="black").pack(side="left", padx=10)
        self.combo_search_cols = ctk.CTkComboBox(top_frame, values=DB_SCHEMA[self.current_table]["columns"], width=130)
        self.combo_search_cols.pack(side="left", padx=5)

        self.entry_search = ctk.CTkEntry(top_frame, placeholder_text="Nhập từ khóa...", width=200)
        self.entry_search.pack(side="left", padx=5)
        self.entry_search.bind("<Return>", lambda event: self.handle_search())

        ctk.CTkButton(top_frame, text="Tìm / Lọc", command=self.handle_search, width=80, fg_color="#17a2b8", hover_color="#138496").pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Làm mới", command=self.load_table_data, width=80, fg_color="#6c757d", hover_color="#5a6268").pack(side="left", padx=5)

        mid_frame = ctk.CTkFrame(self.crud_frame, fg_color="transparent")
        mid_frame.pack(fill="both", expand=True, padx=20, pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", borderwidth=1)
        style.map('Treeview', background=[('selected', '#007bff')], foreground=[('selected', 'white')])
        style.configure("Treeview.Heading", background="#e9ecef", foreground="black", font=('Arial', 10, 'bold'))

        tree_scroll_y = ttk.Scrollbar(mid_frame)
        tree_scroll_y.pack(side="right", fill="y")
        self.tree = ttk.Treeview(mid_frame, yscrollcommand=tree_scroll_y.set)
        self.tree.pack(fill="both", expand=True)
        tree_scroll_y.config(command=self.tree.yview)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        bottom_frame = ctk.CTkFrame(self.crud_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=20)

        self.btn_add = ctk.CTkButton(bottom_frame, text="+ Thêm dòng mới", command=lambda: self.open_add_edit_window("ADD"), fg_color="#28a745", hover_color="#218838", font=("Arial", 14, "bold"))
        self.btn_add.pack(side="left", padx=10, pady=10)

        self.btn_edit = ctk.CTkButton(bottom_frame, text="Sửa dòng chọn", command=lambda: self.open_add_edit_window("EDIT"), fg_color="#ffc107", text_color="black", hover_color="#d39e00", state="disabled")
        self.btn_edit.pack(side="left", padx=10)

        self.btn_delete = ctk.CTkButton(bottom_frame, text="Xóa dòng chọn", command=self.open_delete_window, fg_color="#dc3545", hover_color="#c82333", state="disabled")
        self.btn_delete.pack(side="left", padx=10)

        self.load_table_data()

    def on_table_change(self, choice):
        self.current_table = choice
        self.combo_search_cols.configure(values=DB_SCHEMA[self.current_table]["columns"])
        self.combo_search_cols.set(DB_SCHEMA[self.current_table]["columns"][0])
        self.load_table_data()
        self.entry_search.delete(0, 'end')

    def load_table_data(self, filter_col=None, filter_val=None):
        cols = DB_SCHEMA[self.current_table]["columns"]
        self.tree["columns"] = cols
        self.tree["show"] = "headings"
        for col in cols:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=120, anchor="center")

        for item in self.tree.get_children():
            self.tree.delete(item)

        # GỌI HÀM LẤY DỮ LIỆU THẬT TỪ MYSQL
        raw_data = get_all_from_table(self.current_table)
        
        if filter_col and filter_val:
            col_index = cols.index(filter_col)
            # Lọc dữ liệu bằng Python (so sánh chuỗi)
            data = [row for row in raw_data if filter_val.lower() in str(row[col_index]).lower()]
        else:
            data = raw_data

        for row in data:
            self.tree.insert("", "end", values=row)

        self.btn_edit.configure(state="disabled")
        self.btn_delete.configure(state="disabled")

    def handle_search(self):
        col = self.combo_search_cols.get()
        val = self.entry_search.get()
        if val.strip() != "":
            self.load_table_data(filter_col=col, filter_val=val)
        else:
            self.load_table_data()

    def on_row_select(self, event):
        if self.tree.focus():
            self.btn_edit.configure(state="normal")
            self.btn_delete.configure(state="normal")

    # ================= CÁC HÀM POPUP THÊM/SỬA/XÓA ĐỘNG =================
    def open_add_edit_window(self, mode):
        window = ctk.CTkToplevel(self)
        title = f"Thêm dòng mới - [{self.current_table}]" if mode == "ADD" else f"Chỉnh sửa dòng - [{self.current_table}]"
        window.title(title)
        window.geometry("500x600")
        window.grab_set()

        ctk.CTkLabel(window, text=title, font=("Arial", 18, "bold"), text_color="black").pack(pady=20)

        selected_values = []
        record_id = None
        if mode == "EDIT":
            selected_item = self.tree.focus()
            selected_values = self.tree.item(selected_item, 'values')
            record_id = selected_values[0] # Lấy ID của dòng đang chọn

        cols = DB_SCHEMA[self.current_table]["columns"]
        fks = DB_SCHEMA[self.current_table]["foreign_keys"]

        scroll_frame = ctk.CTkScrollableFrame(window, width=450, height=400, fg_color="white")
        scroll_frame.pack(pady=10)

        self.dynamic_inputs = {} # Lưu lại các ô nhập liệu để lấy dữ liệu sau

        for idx, col in enumerate(cols):
            if col == "id" and mode == "ADD":
                continue 
            
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(row_frame, text=col.upper() + ":", width=120, anchor="w", text_color="black").pack(side="left")

            if col in fks:
                ref_table = fks[col]
                # Lấy dữ liệu KHÓA NGOẠI THẬT từ MySQL
                fk_records = get_all_from_table(ref_table)
                fk_data = [f"{r[0]} - {r[1]}" for r in fk_records] # Ví dụ: "1 - Shopee"
                
                inp = ctk.CTkComboBox(row_frame, values=fk_data, width=250)
                if mode == "EDIT":
                    # Tìm và set giá trị cũ
                    old_val = selected_values[idx]
                    for fk in fk_data:
                        if fk.startswith(f"{old_val} -"):
                            inp.set(fk)
                            break
            else:
                inp = ctk.CTkEntry(row_frame, width=250)
                if mode == "EDIT":
                    inp.insert(0, selected_values[idx])
                if col == "id" and mode == "EDIT":
                    inp.configure(state="disabled") 

            inp.pack(side="left")
            self.dynamic_inputs[col] = inp # Lưu vào dict

        btn_text = "LƯU DỮ LIỆU" if mode == "ADD" else "CẬP NHẬT"
        ctk.CTkButton(window, text=btn_text, command=lambda: self.process_save(mode, window, record_id), fg_color="#007bff", hover_color="#0056b3").pack(pady=20)

    def process_save(self, mode, window, record_id):
        columns = []
        values = []
        
        for col, inp in self.dynamic_inputs.items():
            if col == "id": continue
            columns.append(col)
            val = inp.get()
            
            # Nếu là Khóa ngoại (vd: "1 - Shopee"), ta chỉ bóc lấy số 1
            if col in DB_SCHEMA[self.current_table]["foreign_keys"]:
                val = val.split(" - ")[0]
            values.append(val)

        if mode == "ADD":
            success = insert_record(self.current_table, columns, values)
        else:
            success = update_record(self.current_table, record_id, columns, values)

        if success:
            messagebox.showinfo("Thành công", "Lưu dữ liệu thành công!")
            window.destroy()
            self.load_table_data() # Nạp lại bảng
        else:
            messagebox.showerror("Thất bại", "Có lỗi xảy ra, vui lòng kiểm tra lại!")

    def open_delete_window(self):
        selected_item = self.tree.focus()
        row_id = self.tree.item(selected_item, 'values')[0]

        del_win = ctk.CTkToplevel(self)
        del_win.title("Xác nhận Xóa")
        del_win.geometry("450x250")
        del_win.grab_set()

        ctk.CTkLabel(del_win, text="CẢNH BÁO XÓA DỮ LIỆU", text_color="#dc3545", font=("Arial", 18, "bold")).pack(pady=15)
        ctk.CTkLabel(del_win, text=f"Bạn đang chuẩn bị xóa dòng có ID = {row_id} thuộc bảng '{self.current_table}'", text_color="black").pack(pady=5)

        is_referenced = True if self.current_table in ["brands", "categories", "sources"] else False 
        
        btn_confirm = ctk.CTkButton(del_win, text="XÁC NHẬN XÓA", fg_color="#dc3545", hover_color="#c82333")

        if is_referenced:
            warning_text = "⛔ RÀNG BUỘC DỮ LIỆU:\nBản ghi này đang được tham chiếu bởi sản phẩm.\nThao tác xóa đã bị khóa."
            ctk.CTkLabel(del_win, text=warning_text, text_color="#d39e00", font=("Arial", 12, "bold")).pack(pady=10)
            btn_confirm.configure(state="disabled", fg_color="#f5c6cb") 
        else:
            btn_confirm.configure(command=lambda: self.process_delete(row_id, del_win))

        btn_confirm.pack(pady=15)

    def process_delete(self, row_id, window):
        success = delete_record(self.current_table, row_id)
        if success:
            messagebox.showinfo("Thành công", "Đã xóa dữ liệu thành công!")
            window.destroy()
            self.load_table_data()
        else:
            messagebox.showerror("Thất bại", "Không thể xóa dữ liệu này!")

    # ================= 3. KHÔNG GIAN BÁO CÁO (MAPREDUCE CHARTS) =================
    def setup_mapreduce_frame(self):
        self.mapreduce_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        header_frame = ctk.CTkFrame(self.mapreduce_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header_frame, text="KẾT QUẢ PHÂN TÍCH MAPREDUCE", font=("Arial", 22, "bold"), text_color="black").pack(side="left")
        
        chart_frame = ctk.CTkFrame(self.mapreduce_frame, fg_color="white")
        # Đổi pady=(0, 20) thành pady=20 để đồ thị cách đều tiêu đề
        chart_frame.pack(fill="both", expand=True, padx=20, pady=20) 

        self.draw_charts(chart_frame)

    def draw_charts(self, parent_frame):
        # 1. Lấy dữ liệu THẬT từ HDFS thông qua file drill_api
        df_oos = get_oos_rate_data()
        df_elasticity = get_price_elasticity_data()

        # 2. Cấu hình khung chứa 2 biểu đồ (1 hàng, 2 cột)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor='#f8f9fa')

        # ================= ax1: BIỂU ĐỒ TỶ LỆ CHÁY HÀNG (BAR CHART) =================
        if not df_oos.empty:
            categories = df_oos['category_name'].tolist()
            rates = df_oos['oos_rate'].tolist()
            
            # Tô đỏ cột nếu tỷ lệ cháy hàng > 20%
            bar_colors = ['#dc3545' if r > 20 else '#17a2b8' for r in rates]
            
            ax1.bar(categories, rates, color=bar_colors)
            ax1.set_title('Cảnh báo: Tỷ lệ Cháy hàng (%)', color='black', pad=15, weight='bold')
            ax1.tick_params(colors='black')
            ax1.set_xticks(range(len(categories)))
            ax1.set_xticklabels(categories, rotation=15, ha='right', fontsize=9) 
        else:
            ax1.text(0.5, 0.5, 'Chưa kết nối được Drill\nHoặc dữ liệu rỗng', 
                     ha='center', va='center', color='red', weight='bold')
            ax1.set_title('Cảnh báo: Tỷ lệ Cháy hàng (%)', color='black')
            ax1.axis('off')

        # ================= ax2: ĐỘ CO GIÃN THEO GIÁ (AREA CHART) =================
        if not df_elasticity.empty:
            buckets = df_elasticity['price_bucket'].tolist()
            volumes = df_elasticity['total_sold_volume'].tolist()
            
            # Vẽ biểu đồ vùng (Area Chart)
            # alpha=0.3 tạo độ trong suốt cho vùng màu bên dưới đường line
            ax2.fill_between(buckets, volumes, color="#28a745", alpha=0.3) 
            ax2.plot(buckets, volumes, color="#28a745", marker='o', linewidth=2, markersize=6)
            
            ax2.set_title('Độ Co giãn Cầu theo Phân khúc Giá', color='black', pad=15, weight='bold')
            ax2.tick_params(colors='black')
            ax2.set_xticks(range(len(buckets)))
            ax2.set_xticklabels(buckets, rotation=15, ha='right', fontsize=9)
            
            # Hiển thị số liệu trực tiếp trên các điểm của biểu đồ
            for i, txt in enumerate(volumes):
                ax2.annotate(f"{txt:,}", (buckets[i], volumes[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
        else:
            ax2.text(0.5, 0.5, 'Chưa kết nối được Drill\nHoặc dữ liệu rỗng', 
                     ha='center', va='center', color='red', weight='bold')
            ax2.set_title('Độ Co giãn Cầu theo Phân khúc Giá', color='black')
            ax2.axis('off')

        # 3. Đưa biểu đồ lên giao diện CustomTkinter
        plt.tight_layout() 
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == "__main__":
    app = ECommerceDashboard()
    app.mainloop()