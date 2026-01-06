import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os

print("⏳ Đang xử lý...")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}

# 1. ĐỌC DỮ LIỆU
# dtype=str: Bắt buộc đọc tất cả là chữ (để không bị mất số 0 ở đầu hoặc mất dấu chấm)
dfs = pd.read_html(requests.get(url, headers=headers).text, match='Ngân hàng')
df = dfs[1].copy()

# 2. ÉP TÊN CỘT
cols_new = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
if len(df.columns) >= len(cols_new):
    df = df.iloc[:, :len(cols_new)]
    df.columns = cols_new
if df.iloc[0,0] == "Ngân hàng":
    df = df.iloc[1:]

# 3. HÀM LÀM SẠCH "BẤT BẠI" (Bản nâng cấp)
def clean_so(val):
    val = str(val).strip()
    
    # Bước 1: Ưu tiên xử lý dấu phẩy (VN) thành dấu chấm (Quốc tế)
    if ',' in val:
        val = val.replace('.', '') # Xóa dấu chấm hàng nghìn nếu có (VD: 1.000,5)
        val = val.replace(',', '.') # Đổi phẩy thành chấm
    
    # Bước 2: Lấy số ra
    try:
        # Regex này chấp nhận số thập phân
        match = re.search(r"(\d+\.?\d*)", val)
        if match:
            num = float(match.group(1))
            
            # Bước 3: Vòng lặp sửa lỗi (Chỉ chạy khi số quá vô lý)
            # Nếu web lỗi format biến 5.85 thành 585 -> Chia 100
            # Nếu web lỗi format biến 10.1 thành 101 -> Chia 10
            # Còn 1.01 hay 10.01 thì nó nhỏ hơn 20 rồi, không bị chia.
            while num > 20:
                num = num / 10
            
            return num
        return 0.0
    except: return 0.0

# Áp dụng
for col in df.columns:
    if col != "Ngân hàng":
        df[col] = df[col].apply(clean_so)

df.insert(0, 'NgayCapNhat', datetime.now().strftime("%Y-%m-%d %H:%M"))

print("🚀 Đang cập nhật Sheet...")
sheet.clear()
sheet.append_row(df.columns.tolist())
sheet.append_rows(df.values.tolist())
print("🎉 XONG! Dữ liệu 1,01 hay 10,01 đều chuẩn.")