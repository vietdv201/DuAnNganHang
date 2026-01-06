import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os
import json

# --- CẤU HÌNH ---
# Đoạn này giúp Bot lấy chìa khóa từ đám mây
key_content = json.loads(os.environ['G_SHEET_CREDS'])

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, scope)
client = gspread.authorize(creds)
sheet = client.open("LaiSuatNganHang").sheet1 

def clean_interest_rate(val):
    match = re.search(r"(\d+\.?\d*)", str(val))
    return float(match.group(1)) if match else 0.0

print("Dang cao du lieu...")
url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    # Lấy dữ liệu
    dfs = pd.read_html(requests.get(url, headers=headers).text, match='Ngân hàng')
    df = dfs[1].copy() # Lấy bảng lãi suất online

    # Làm sạch
    for col in df.columns[1:]:
        df[col] = df[col].apply(clean_interest_rate)

    # Thêm ngày
    df['NgayCapNhat'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    cols = list(df.columns); cols = [cols[-1]] + cols[:-1]
    df = df[cols]

    # Ghi lên Sheet
    sheet.clear()
    sheet.append_row(df.columns.tolist())
    sheet.append_rows(df.values.tolist())
    print("Thanh cong!")

except Exception as e:
    print(f"Loi: {e}")
    # Nếu lỗi thì kết thúc chương trình bằng mã lỗi để GitHub biết
    exit(1)