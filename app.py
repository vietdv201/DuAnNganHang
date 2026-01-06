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
st.title("💰 LÃI SUẤT NGÂN HÀNG HÔM NAY")

# --- KẾT NỐI GOOGLE SHEET ---
@st.cache_data(ttl=600)
def load_data():
    # Kết nối
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    
    # Lấy dữ liệu thô
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # --- [QUAN TRỌNG] BỘ LỌC DỮ LIỆU TẠI CHỖ ---
    # Nhiệm vụ: Dù Sheet ghi là "5,85" hay "585", Web cũng sẽ đưa về 5.85
    def xu_ly_so_hien_thi(val):
        val = str(val) # Chuyển thành chữ trước
        val = val.replace(',', '.') # Thay phẩy thành chấm
        try:
            # Lấy số ra
            match = re.search(r"(\d+\.?\d*)", val)
            if match:
                num = float(match.group(1))
                
                # THUẬT TOÁN ÉP SỐ:
                # Nếu số > 20 (Vô lý), tự động chia 10 dần dần cho đến khi về đúng
                # Ví dụ: 585 -> 58.5 -> 5.85 (Dừng)
                while num > 20:
                    num = num / 10
                
                return num
            return 0.0
        except: return 0.0

    # Áp dụng bộ lọc này cho tất cả các cột lãi suất
    for col in df.columns:
        if col != "Ngân hàng" and col != "NgayCapNhat":
            df[col] = df[col].apply(xu_ly_so_hien_thi)
            
    return df

try:
    with st.spinner('Đang tải dữ liệu...'):
        df = load_data()

    # Hiển thị thời gian cập nhật
    if 'NgayCapNhat' in df.columns:
        last_update = df['NgayCapNhat'].iloc[0]
        st.caption(f"Cập nhật lúc: {last_update}")

    # --- BỘ LỌC KỲ HẠN ---
    ds_ky_han = [col for col in df.columns if 'tháng' in col]
    ky_han = st.selectbox("Chọn kỳ hạn:", ds_ky_han, index=3)

    # --- VẼ BIỂU ĐỒ ---
    if ky_han:
        # Sắp xếp
        df_sort = df.sort_values(by=ky_han, ascending=False)

        # Tiêu đề biểu đồ
        st.subheader(f"Lãi suất {ky_han} (%)")

        # Vẽ biểu đồ
        fig = px.bar(
            df_sort, 
            x='Ngân hàng', 
            y=ky_han,
            text_auto='.2f',
            color=ky_han,
            color_continuous_scale='Greens'
        )

        fig.update_layout(
            xaxis_title="Ngân hàng",
            yaxis_title=None, # Ẩn chữ trục dọc cho gọn
            height=500
        )
        
        # Thêm dấu %
        fig.update_traces(
            texttemplate='%{y:.2f}%', 
            textposition='outside'
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- BẢNG DỮ LIỆU ---
    with st.expander("Xem bảng số liệu chi tiết"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Lỗi: {e}")