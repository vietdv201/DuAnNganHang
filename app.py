import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Lãi Suất Ngân Hàng", layout="wide")

# [QUAN TRỌNG] Đổi tiêu đề để xác nhận code mới đã chạy
st.title("✅ ĐÃ SỬA LỖI (V3): LÃI SUẤT NGÂN HÀNG") 

# --- KẾT NỐI GOOGLE SHEET ---
def load_data():
    # 1. Kết nối
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    
    # 2. Lấy dữ liệu
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # 3. BỘ LỌC XỬ LÝ SỐ (VÒNG LẶP CHIA 10)
    def fix_loi_so_vn(val):
        s = str(val)
        if not s: return 0.0
        
        # Thay dấu phẩy thành dấu chấm ngay lập tức
        s = s.replace(',', '.')
        
        try:
            match = re.search(r"(\d+\.?\d*)", s)
            if match:
                num = float(match.group(1))
                
                # NẾU SỐ LỚN HƠN 25 -> CHIA 10 LIÊN TỤC
                # Ví dụ: 585 -> 58.5 -> 5.85
                while num > 25:
                    num = num / 10
                return num
            return 0.0
        except: return 0.0

    # Áp dụng bộ lọc cho tất cả các cột
    for col in df.columns:
        if col not in ["Ngân hàng", "NgayCapNhat"]:
            df[col] = df[col].apply(fix_loi_so_vn)
            
    return df

try:
    # Bỏ st.spinner cũ để tránh cache, gọi hàm trực tiếp
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
            
            fig = px.bar(
                df_sort, 
                x='Ngân hàng', 
                y=ky_han,
                text_auto='.2f', 
                color=ky_han,
                color_continuous_scale='Greens'
            )
            
            fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
            # Set cứng trục Y tối đa là 15 để ép biểu đồ hiển thị đúng
            fig.update_layout(height=500, yaxis_range=[0, 15], yaxis_title="Lãi suất (%)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Kiểm tra bảng số liệu (Đã xử lý)"):
                st.dataframe(df)

except Exception as e:
    st.error(f"Lỗi: {e}")
