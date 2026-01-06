import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os
import json

# --- CẤU HÌNH ---
key_content = json.loads(os.environ['G_SHEET_CREDS'])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

def clean_interest_rate(val):
    # Chỉ lấy số, nếu lỗi thì trả về 0
    try:
        match = re.search(r"(\d+\.?\d*)", str(val))
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0

print("Dang cao du lieu...")
url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    dfs = pd.read_html(requests.get(url, headers=headers).text, match='Ngân hàng')
    df = dfs[1].copy()
    
    # === [QUAN TRỌNG] ĐẶT LẠI TÊN CỘT THỦ CÔNG ===
    # Vì web trả về tiêu đề lung tung, ta ép cứng tên cột luôn cho chuẩn
    # (Dựa trên thứ tự cột trong ảnh Sheet bạn gửi)
    df.columns = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
    
    # Xóa hàng đầu tiên nếu nó chứa chữ "Ngân hàng" (do lỗi đọc bảng)
    if df.iloc[0,0] == "Ngân hàng":
        df = df.iloc[1:]
    
    # Làm sạch số liệu (trừ cột Ngân hàng ra)
    for col in df.columns:
        if col != "Ngân hàng":
            df[col] = df[col].apply(clean_interest_rate)
    
    # Thêm ngày cập nhật vào cột đầu tiên
    df.insert(0, 'NgayCapNhat', datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Ghi đè lên Sheet
    sheet.clear() # Xóa sạch sheet cũ
    sheet.append_row(df.columns.tolist()) # Ghi tiêu đề mới
    sheet.append_rows(df.values.tolist()) # Ghi dữ liệu
    print("Thanh cong!")

except Exception as e:
    print(f"Loi: {e}")
    exit(1)