import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os

# --- 1. KẾT NỐI ---
print("⏳ 1. Đang kết nối Google Sheet...")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

# --- 2. CÀO DỮ LIỆU ---
print("⏳ 2. Đang lấy dữ liệu từ Web...")
url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}
# Đọc thô, không cho pandas tự đoán format
dfs = pd.read_html(requests.get(url, headers=headers).text, match='Ngân hàng')
df = dfs[1].copy()

# ÉP TÊN CỘT
cols_new = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
if len(df.columns) >= len(cols_new):
    df = df.iloc[:, :len(cols_new)]
    df.columns = cols_new
if df.iloc[0,0] == "Ngân hàng":
    df = df.iloc[1:]

# --- 3. HÀM SỬA LỖI (CÓ IN RA MÀN HÌNH ĐỂ KIỂM TRA) ---
def clean_so_debug(val):
    val_str = str(val).strip()
    # Ưu tiên đổi phẩy thành chấm (VN -> US)
    val_str = val_str.replace(',', '.')
    
    try:
        match = re.search(r"(\d+\.?\d*)", val_str)
        if match:
            num = float(match.group(1))
            original = num # Lưu số gốc để so sánh
            
            # --- LOGIC CHIA 10 (SỬA LỖI 585 -> 5.85) ---
            # Miễn là số > 20, chia 10 liên tục
            while num > 20:
                num = num / 10
            
            # Nếu số bị thay đổi, in ra cho người dùng biết
            if num != original:
                print(f"   🔧 Đã sửa: {original}  --->  {num}")
                
            return num
        return 0.0
    except: return 0.0

print("⏳ 3. Đang làm sạch dữ liệu...")
# Áp dụng hàm sửa lỗi cho TẤT CẢ các cột trừ cột tên Ngân hàng
for col in df.columns:
    if col != "Ngân hàng":
        df[col] = df[col].apply(clean_so_debug)

# Thêm ngày giờ
df.insert(0, 'NgayCapNhat', datetime.now().strftime("%Y-%m-%d %H:%M"))

# --- 4. GHI VÀO SHEET ---
print("🚀 4. Đang ghi đè dữ liệu mới vào Sheet...")
sheet.clear()
sheet.append_row(df.columns.tolist())
sheet.append_rows(df.values.tolist())

print("🎉 XONG! Dữ liệu trên Sheet đã chuẩn 100%.")
print("👉 Hãy mở Web App và Clear Cache ngay!")
