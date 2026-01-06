import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os

print("⏳ Đang kết nối Google Sheet...")

# 1. KẾT NỐI
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

# 2. CÀO DỮ LIỆU (Đoạn này đã nâng cấp)
print("⏳ Đang đọc dữ liệu từ Web...")
url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}

# [QUAN TRỌNG] Thêm decimal=',' để máy hiểu 1,5 là 1.5 chứ không phải 15
dfs = pd.read_html(
    requests.get(url, headers=headers).text, 
    match='Ngân hàng', 
    decimal=',',    # Dấu phẩy là số lẻ
    thousands='.'   # Dấu chấm là hàng nghìn
)
df = dfs[1].copy()

# 3. ÉP TÊN CỘT
cols_new = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
# Chỉ lấy đúng số cột mình cần
if len(df.columns) >= len(cols_new):
    df = df.iloc[:, :len(cols_new)]
    df.columns = cols_new

# Xóa dòng tiêu đề thừa nếu có
if df.iloc[0,0] == "Ngân hàng":
    df = df.iloc[1:]

# 4. LÀM SẠCH DỮ LIỆU (Đoạn này bạn hỏi sửa thế nào đây)
def clean_so(val):
    # Chuyển về chuỗi, xóa % nếu có
    val = str(val).replace('%', '')
    
    # Đề phòng trường hợp pandas chưa xử lý hết dấu phẩy
    val = val.replace(',', '.') 
    
    try:
        # Lấy số ra khỏi chuỗi
        match = re.search(r"(\d+\.?\d*)", val)
        if match:
            num = float(match.group(1))
            
            # [QUAN TRỌNG] Logic chống sai số:
            # Lãi suất ngân hàng không bao giờ quá 20%.
            # Nếu máy đọc ra số > 20 (ví dụ 415), nghĩa là nó sai -> Chia 100
            # Nếu máy đọc ra 1.5 -> Nhỏ hơn 20 -> Giữ nguyên.
            if num > 20: 
                return num / 100
            
            return num
        return 0.0
    except: return 0.0

# Áp dụng hàm làm sạch cho tất cả các cột (trừ cột Ngân hàng)
for col in df.columns:
    if col != "Ngân hàng":
        df[col] = df[col].apply(clean_so)

# Thêm ngày cập nhật
df.insert(0, 'NgayCapNhat', datetime.now().strftime("%Y-%m-%d %H:%M"))

print("🚀 Đang đẩy dữ liệu chuẩn lên Sheet...")
sheet.clear()
sheet.append_row(df.columns.tolist())
sheet.append_rows(df.values.tolist())

print("🎉 XONG! Dữ liệu giờ chuẩn đét rồi nhé (1,5% vẫn là 1.5%).")