import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os
import json

# --- CẤU HÌNH KẾT NỐI (Giữ nguyên cho Bot trên GitHub) ---
key_content = json.loads(os.environ['G_SHEET_CREDS'])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

# --- CÀO DỮ LIỆU ---
print("Bot bắt đầu cào dữ liệu...")
url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    # 1. ĐỌC DỮ LIỆU (Đã thêm cấu hình xử lý dấu phẩy VN)
    dfs = pd.read_html(
        requests.get(url, headers=headers).text, 
        match='Ngân hàng', 
        decimal=',',    # Dấu phẩy là số lẻ
        thousands='.'   # Dấu chấm là hàng nghìn
    )
    df = dfs[1].copy()

    # 2. ÉP TÊN CỘT CHO CHUẨN
    cols_new = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
    # Chỉ lấy đúng số cột cần thiết
    if len(df.columns) >= len(cols_new):
        df = df.iloc[:, :len(cols_new)]
        df.columns = cols_new
    
    # Xóa dòng tiêu đề bị lặp (nếu có)
    if df.iloc[0,0] == "Ngân hàng":
        df = df.iloc[1:]

    # 3. HÀM LÀM SẠCH SỐ LIỆU (Logic thông minh giống fix.py)
    def clean_so(val):
        val = str(val).replace('%', '') # Bỏ dấu %
        val = val.replace(',', '.')     # Đổi phẩy thành chấm (đề phòng)
        
        try:
            match = re.search(r"(\d+\.?\d*)", val)
            if match:
                num = float(match.group(1))
                
                # CHỐT CHẶN AN TOÀN:
                # Nếu > 20 (VD: 415) -> Chia 100 thành 4.15
                # Nếu <= 20 (VD: 1.5) -> Giữ nguyên
                if num > 20: 
                    return num / 100
                return num
            return 0.0
        except: return 0.0

    # Áp dụng làm sạch cho các cột số
    for col in df.columns:
        if col != "Ngân hàng":
            df[col] = df[col].apply(clean_so)

    # 4. THÊM NGÀY GIỜ VÀ GHI VÀO SHEET
    df.insert(0, 'NgayCapNhat', datetime.now().strftime("%Y-%m-%d %H:%M"))

    sheet.clear()
    sheet.append_row(df.columns.tolist())
    sheet.append_rows(df.values.tolist())
    
    print("Thanh cong! Da cap nhat Sheet.")

except Exception as e:
    print(f"Loi nghiem trong: {e}")
    exit(1) # Báo lỗi cho GitHub biết để gửi mail báo ông