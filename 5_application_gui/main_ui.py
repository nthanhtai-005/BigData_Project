import customtkinter as ctk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# IMPORT TOÀN BỘ 8 HÀM TỪ DRILL API
from drill_api import (get_oos_rate_data, get_price_elasticity_data, 
                       get_category_count_data, get_category_price_data, get_brand_price_compare_data,
                       get_raw_mapreduce_data, MAPREDUCE_JOBS_CONFIG)

# IMPORT CÁC HÀM XỬ LÝ DATABASE
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
        self.title("Data Warehouse Dashboard - Group 6")
        self.after(0, lambda: self.state('zoomed'))
        self.current_table = "products"

        self.setup_sidebar()
        self.setup_crud_frame()
        self.setup_mapreduce_frame()
        self.setup_raw_data_frame()

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
        
        self.btn_menu_raw = ctk.CTkButton(self.sidebar_frame, text="📑 Dữ liệu MapReduce", command=lambda: self.select_frame("RAW"), fg_color="transparent", text_color="black", hover_color="#dee2e6", anchor="w")
        self.btn_menu_raw.pack(pady=10, padx=20, fill="x")

    def select_frame(self, frame_name):
        self.btn_menu_crud.configure(fg_color=("#ced4da" if frame_name == "CRUD" else "transparent"))
        self.btn_menu_chart.configure(fg_color=("#ced4da" if frame_name == "CHART" else "transparent"))
        self.btn_menu_raw.configure(fg_color=("#ced4da" if frame_name == "RAW" else "transparent")) 

        self.crud_frame.pack_forget()
        self.mapreduce_frame.pack_forget()
        self.raw_data_frame.pack_forget()
        if frame_name == "CRUD":
            self.crud_frame.pack(side="right", fill="both", expand=True)
        elif frame_name == "CHART":
            self.mapreduce_frame.pack(side="right", fill="both", expand=True)
        elif frame_name == "RAW":
            self.raw_data_frame.pack(side="right", fill="both", expand=True)

    # ================= 2. CRUD =================
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

        raw_data = get_all_from_table(self.current_table)
        
        if filter_col and filter_val:
            col_index = cols.index(filter_col)
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
            record_id = selected_values[0]

        cols = DB_SCHEMA[self.current_table]["columns"]
        fks = DB_SCHEMA[self.current_table]["foreign_keys"]

        scroll_frame = ctk.CTkScrollableFrame(window, width=450, height=400, fg_color="white")
        scroll_frame.pack(pady=10)

        self.dynamic_inputs = {} 

        for idx, col in enumerate(cols):
            if col == "id" and mode == "ADD":
                continue 
            
            row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(row_frame, text=col.upper() + ":", width=120, anchor="w", text_color="black").pack(side="left")

            if col in fks:
                ref_table = fks[col]
                fk_records = get_all_from_table(ref_table)
                fk_data = [f"{r[0]} - {r[1]}" for r in fk_records] 
                
                inp = ctk.CTkComboBox(row_frame, values=fk_data, width=250)
                if mode == "EDIT":
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
            self.dynamic_inputs[col] = inp 

        btn_text = "LƯU DỮ LIỆU" if mode == "ADD" else "CẬP NHẬT"
        ctk.CTkButton(window, text=btn_text, command=lambda: self.process_save(mode, window, record_id), fg_color="#007bff", hover_color="#0056b3").pack(pady=20)

    def process_save(self, mode, window, record_id):
        columns = []
        values = []
        
        for col, inp in self.dynamic_inputs.items():
            if col == "id": continue
            columns.append(col)
            val = inp.get()
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
            self.load_table_data() 
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

    # ================= 3.MAPREDUCE CHARTS =================
    def setup_mapreduce_frame(self):
        self.mapreduce_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        header_frame = ctk.CTkFrame(self.mapreduce_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header_frame, text="KẾT QUẢ PHÂN TÍCH MAPREDUCE (8 BÀI TOÁN)", font=("Arial", 22, "bold"), text_color="black").pack(side="left")
        
        # SỬ DỤNG CTKSCROLLABLEFRAME ĐỂ CUỘN LÊN XUỐNG
        chart_frame = ctk.CTkScrollableFrame(self.mapreduce_frame, fg_color="white")
        chart_frame.pack(fill="both", expand=True, padx=20, pady=20) 

        self.draw_charts(chart_frame)

    def draw_charts(self, parent_frame):
        # Đổi cấu trúc thành 5 hàng, 1 cột. Tăng chiều cao (figsize) lên 35 để các biểu đồ rộng rãi
        fig, axs = plt.subplots(5, 1, figsize=(14, 35), facecolor='#f8f9fa')
        fig.subplots_adjust(hspace=0.5, top=0.98, bottom=0.02)

        def show_empty_state(ax, title):
            ax.text(0.5, 0.5, 'ĐANG CHỜ KẾT QUẢ MAPREDUCE\n(Chưa có dữ liệu trên HDFS)', 
                    ha='center', va='center', color='#6c757d', weight='bold')
            ax.set_title(title, weight='bold', pad=15)
            ax.axis('off')

        # === BIỂU ĐỒ 1: TỶ LỆ CHÁY HÀNG ===
        df_oos = get_oos_rate_data()
        if not df_oos.empty:
            categories = df_oos['category_name'].tolist()
            rates = df_oos['oos_rate'].tolist()
            bar_colors = ['#dc3545' if r > 20 else '#17a2b8' for r in rates]
            axs[0].bar(categories, rates, color=bar_colors)
            axs[0].set_title('1. Cảnh báo: Tỷ lệ Cháy hàng (%)', color='black', weight='bold', pad=15)
            axs[0].set_xticks(range(len(categories)))
            axs[0].set_xticklabels(categories, rotation=15, ha='right', fontsize=10) 
        else:
            show_empty_state(axs[0], '1. Cảnh báo: Tỷ lệ Cháy hàng (%)')

        # === BIỂU ĐỒ 2: ĐỘ CO GIÃN GIÁ ===
        df_elasticity = get_price_elasticity_data()
        if not df_elasticity.empty:
            buckets = df_elasticity['price_bucket'].tolist()
            volumes = df_elasticity['total_sold_volume'].tolist()
            axs[1].fill_between(buckets, volumes, color="#28a745", alpha=0.3) 
            axs[1].plot(buckets, volumes, color="#28a745", marker='o', linewidth=2, markersize=6)
            axs[1].set_title('2. Nhu cầu của khách hàng theo Phân khúc giá', color='black', weight='bold', pad=15)
            axs[1].set_xticks(range(len(buckets)))
            axs[1].set_xticklabels(buckets, rotation=15, ha='right', fontsize=10)
        else:
            show_empty_state(axs[1], '2. Nhu cầu của khách hàng theo Phân khúc giá')

        # === BIỂU ĐỒ 3 (MỚI): PHÂN BỐ DANH MỤC (PIE CHART) ===
        df_cat = get_category_count_data()
        if not df_cat.empty:
            labels = df_cat['category_name'].tolist()
            sizes = df_cat['total_products'].tolist()
            
            # XÓA tham số labels=labels để không in chữ lên hình tròn
            # pctdistance=0.8 để đẩy các con số % ra gần viền ngoài cho thoáng
            wedges, texts, autotexts = axs[2].pie(
                sizes, 
                autopct='%1.1f%%', 
                startangle=140, 
                colors=plt.cm.tab20.colors, # Dùng tab20 để có nhiều màu phân biệt tốt hơn cho 10 danh mục
                pctdistance=0.8
            )
            
            axs[2].set_title('3. Phân bố Số lượng Sản phẩm theo Danh mục', color='black', weight='bold', pad=15)
            
            # ĐƯA CHÚ THÍCH RA NGOÀI (BÊN PHẢI)
            # bbox_to_anchor=(1, 0.5) ghim chú thích vào mép phải của khung biểu đồ
            axs[2].legend(wedges, labels,
                          title="Danh mục sản phẩm",
                          loc="center left",
                          bbox_to_anchor=(1, 0.5),
                          fontsize=10,
                          title_fontsize=11)
        else:
            show_empty_state(axs[2], '3. Phân bố Số lượng Sản phẩm theo Danh mục')

        # === BIỂU ĐỒ 4 (MỚI): SO SÁNH GIÁ BÁN & GIÁ GỐC (CỘT ĐÔI) ===
        df_price = get_category_price_data()
        if not df_price.empty:
            labels = df_price['category_name'].tolist()
            avg_price = df_price['avg_price'].tolist()
            avg_market = df_price['avg_market_price'].tolist()
            
            x = np.arange(len(labels))
            width = 0.35  # Độ rộng của 1 cột
            
            axs[3].bar(x - width/2, avg_price, width, label='Giá Thực Bán', color='#007bff')
            axs[3].bar(x + width/2, avg_market, width, label='Giá Niêm Yết', color='#6c757d')
            axs[3].set_title('4. So sánh Giá bán trung bình và Giá gốc theo Danh mục', color='black', weight='bold', pad=15)
            axs[3].set_xticks(x)
            axs[3].set_xticklabels(labels, rotation=15, ha='right', fontsize=10)
            axs[3].legend()
        else:
            show_empty_state(axs[3], '4. So sánh Giá bán trung bình và Giá gốc theo Danh mục')

        # === BIỂU ĐỒ 5 (MỚI): CẠNH TRANH GIÁ THƯƠNG HIỆU HASAKI VS LAM THẢO ===
        df_brand = get_brand_price_compare_data()
        if not df_brand.empty:
            # Sắp xếp theo Lượt bán và chỉ lấy Top 15 để biểu đồ không bị rối mắt
            df_brand = df_brand.sort_values(by='total_sold', ascending=False).head(15)
            
            labels = df_brand['brand_name'].tolist()
            hasaki_price = df_brand['avg_price_hasaki'].tolist()
            lamthao_price = df_brand['avg_price_lamthao'].tolist()
            
            x = np.arange(len(labels))
            width = 0.35
            
            axs[4].bar(x - width/2, hasaki_price, width, label='Shop: Hasaki', color='#198754')
            axs[4].bar(x + width/2, lamthao_price, width, label='Shop: Lam Thảo', color='#fd7e14')
            axs[4].set_title('5. Cạnh tranh Giá bán các Thương hiệu Nổi tiếng (Top 15)', color='black', weight='bold', pad=15)
            axs[4].set_xticks(x)
            axs[4].set_xticklabels(labels, rotation=25, ha='right', fontsize=10)
            axs[4].legend()
        else:
            show_empty_state(axs[4], '5. Cạnh tranh Giá bán các Thương hiệu Nổi tiếng')

        # Vẽ lên Giao diện
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", expand=False, padx=10, pady=10)
        
    # ================= 4. RAW MAPREDUCE DATA =================
    def setup_raw_data_frame(self):
        self.raw_data_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Phần Header chứa Combobox
        top_frame = ctk.CTkFrame(self.raw_data_frame, fg_color="#f8f9fa")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(top_frame, text="Chọn Bài toán MapReduce:", font=("Arial", 14, "bold"), text_color="black").pack(side="left", padx=15, pady=15)
        
        # Combobox chọn bài toán
        job_titles = list(MAPREDUCE_JOBS_CONFIG.keys())
        self.combo_jobs = ctk.CTkComboBox(top_frame, values=job_titles, command=self.load_raw_job_data, width=500)
        self.combo_jobs.set(job_titles[0])
        self.combo_jobs.pack(side="left", padx=10)
        
        ctk.CTkButton(top_frame, text="Tải dữ liệu", command=lambda: self.load_raw_job_data(self.combo_jobs.get()), width=100, fg_color="#17a2b8", hover_color="#138496").pack(side="left", padx=10)
        
        # Hiển thị tổng số dòng
        self.lbl_row_count = ctk.CTkLabel(top_frame, text="Tổng số dòng: 0", font=("Arial", 12, "italic"), text_color="gray")
        self.lbl_row_count.pack(side="right", padx=20)

        # Phần Bảng (Treeview)
        mid_frame = ctk.CTkFrame(self.raw_data_frame, fg_color="transparent")
        mid_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # Scrollbars cho Bảng
        tree_scroll_y = ttk.Scrollbar(mid_frame)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x = ttk.Scrollbar(mid_frame, orient='horizontal')
        tree_scroll_x.pack(side="bottom", fill="x")

        # Khởi tạo Treeview
        self.raw_tree = ttk.Treeview(mid_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.raw_tree.pack(fill="both", expand=True)
        
        tree_scroll_y.config(command=self.raw_tree.yview)
        tree_scroll_x.config(command=self.raw_tree.xview)
        
        # Tải dữ liệu bài đầu tiên khi khởi động
        self.load_raw_job_data(self.combo_jobs.get())

    def load_raw_job_data(self, job_title):
        # 1. Gọi API lấy DataFrame
        df = get_raw_mapreduce_data(job_title)
        
        # 2. Xóa dữ liệu cũ trong bảng
        self.raw_tree.delete(*self.raw_tree.get_children())
        
        if df.empty:
            self.raw_tree["columns"] = ("Message",)
            self.raw_tree["show"] = "headings"
            self.raw_tree.heading("Message", text="THÔNG BÁO")
            self.raw_tree.column("Message", width=800, anchor="center")
            self.raw_tree.insert("", "end", values=("Chưa có dữ liệu cho bài toán này trên HDFS.",))
            self.lbl_row_count.configure(text="Tổng số dòng: 0")
            return
            
        # 3. Thiết lập cột mới theo DataFrame
        columns = list(df.columns)
        self.raw_tree["columns"] = columns
        self.raw_tree["show"] = "headings"
        
        for col in columns:
            self.raw_tree.heading(col, text=col.upper())
            self.raw_tree.column(col, width=200, anchor="center")
            
        # 4. Chèn dữ liệu mới
        for _, row in df.iterrows():
            self.raw_tree.insert("", "end", values=list(row))
            
        self.lbl_row_count.configure(text=f"Tổng số dòng: {len(df)}")

if __name__ == "__main__":
    app = ECommerceDashboard()
    app.mainloop()