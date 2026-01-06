import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os

# --- 1. KẾT NỐI GOOGLE SHEET ---
# Dùng Secret từ biến môi trường (nếu chạy trên GitHub) hoặc file key.json (nếu chạy máy)
try:
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        import json
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
except Exception as e:
    print(f"Lỗi kết nối: {e}")
    exit()

# --- 2. CÀO DỮ LIỆU TỪ WEB ---
try:
    url = 'https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem'
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = pd.read_html(requests.get(url, headers=headers).text, match='Ngân hàng')
    df = dfs[1].copy()

    # Đổi tên cột cho chuẩn
    cols_new = ["Ngân hàng", "1 tháng", "3 tháng", "6 tháng", "12 tháng", "18 tháng", "24 tháng", "36 tháng"]
    if len(df.columns) >= len(cols_new):
        df = df.iloc[:, :len(cols_new)]
        df.columns = cols_new
    if df.iloc[0,0] == "Ngân hàng":
        df = df.iloc[1:]

    # --- 3. LÀM SẠCH SỐ LIỆU (QUAN TRỌNG) ---
    def clean_so(val):
        s = str(val).replace(',', '.')
        try:
            match = re.search(r"(\d+\.?\d*)", s)
            if match:
                num = float(match.group(1))
                # Logic chia 10 nếu số > 25 (chống lỗi 585 -> 5.85)
                while num > 25:
                    num = num / 10
                return num
            return 0.0
        except: return 0.0

    for col in df.columns:
        if col != "Ngân hàng":
            df[col] = df[col].apply(clean_so)

    # Thêm cột ngày tháng (chỉ lấy ngày, bỏ giờ phút để dễ gom nhóm)
    today_str = datetime.now().strftime("%Y-%m-%d")
    df.insert(0, 'NgayCapNhat', today_str)

    # --- 4. GHI VÀO SHEET (CHẾ ĐỘ GHI NỐI TIẾP) ---
    # Kiểm tra xem hôm nay đã cào chưa? Nếu cào rồi thì thôi không ghi đè nữa tránh trùng lặp
    existing_data = sheet.get_all_values()
    
    # Nếu Sheet trống trơn -> Ghi cả tiêu đề + dữ liệu
    if not existing_data:
        sheet.append_row(df.columns.tolist())
        sheet.append_rows(df.values.tolist())
        print(f"✅ Đã tạo mới và ghi dữ liệu ngày {today_str}")
    else:
        # Nếu Sheet đã có dữ liệu -> Kiểm tra xem dòng cuối cùng có phải hôm nay không
        last_date = existing_data[-1][0] if existing_data else ""
        
        if last_date == today_str:
            print(f"⚠️ Dữ liệu ngày {today_str} đã tồn tại! Không ghi thêm.")
        else:
            # Nếu chưa có -> Ghi nối tiếp vào dưới cùng
            sheet.append_rows(df.values.tolist())
            print(f"✅ Đã cập nhật thêm dữ liệu ngày {today_str}")

except Exception as e:
    print(f"❌ Lỗi khi chạy Bot: {e}")
