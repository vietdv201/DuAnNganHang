import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Lãi Suất", layout="wide")

# [QUAN TRỌNG] Đổi tiêu đề để ông biết chắc chắn code mới đã chạy
st.title("✅ BẢN SỬA LỖI VĨNH VIỄN (V4)") 

# --- HÀM XỬ LÝ SỐ "CỤC SÚC" ---
def fix_so_lieu(val):
    s = str(val)
    if not s: return 0.0
    
    # Thay dấu phẩy thành dấu chấm ngay lập tức
    s = s.replace(',', '.')
    
    try:
        # Lấy số ra
        match = re.search(r"(\d+\.?\d*)", s)
        if match:
            num = float(match.group(1))
            
            # VÒNG LẶP CHIA 10
            # Nếu số lớn hơn 25 (VD: 585), chia cho 10 đến khi nào nhỏ hơn 25 thì thôi
            while num > 25:
                num = num / 10
            return num
        return 0.0
    except: return 0.0

# --- KẾT NỐI VÀ LẤY DATA ---
def load_data():
    # Kết nối Google Sheet
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        # Lấy key từ Secrets trên Cloud
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # --- ÉP SỐ LIỆU NGAY TẠI ĐÂY ---
    # Chạy vòng lặp sửa lỗi cho tất cả các cột lãi suất
    for col in df.columns:
        if col not in ["Ngân hàng", "NgayCapNhat"]:
            df[col] = df[col].apply(fix_so_lieu)
            
    return df

try:
    # Gọi hàm lấy dữ liệu (Không dùng cache để bắt buộc lấy mới)
    df = load_data()

    # Hiển thị ngày cập nhật
    if 'NgayCapNhat' in df.columns:
        st.caption(f"Cập nhật lúc: {df['NgayCapNhat'].iloc[0]}")

    # Vẽ biểu đồ
    cols = [c for c in df.columns if 'tháng' in c]
    if cols:
        ky_han = st.selectbox("Chọn kỳ hạn:", cols, index=3)
        
        if ky_han:
            df_sort = df.sort_values(by=ky_han, ascending=False)
            
            # Vẽ lại biểu đồ
            fig = px.bar(
                df_sort, 
                x='Ngân hàng', 
                y=ky_han,
                text_auto='.2f', 
                color=ky_han,
                color_continuous_scale='Greens'
            )
            
            fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
            # Khóa cứng chiều cao trục Y là 15% để cột 585 không phá vỡ biểu đồ
            fig.update_layout(height=500, yaxis_range=[0, 15], yaxis_title="Lãi suất (%)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Hiện bảng check
            with st.expander("Bảng số liệu đã xử lý"):
                st.dataframe(df)

except Exception as e:
    st.error(f"Lỗi rồi: {e}")
