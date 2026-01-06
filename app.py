import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Lãi Suất Ngân Hàng", layout="wide")
st.title("💰 LÃI SUẤT NGÂN HÀNG HÔM NAY")

# --- 1. KẾT NỐI VÀ LẤY DỮ LIỆU ---
@st.cache_data(ttl=300)
def load_data():
    # Kết nối Google Sheet
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Xử lý cột ngày tháng
    if 'NgayCapNhat' in df.columns:
        df['NgayCapNhat'] = pd.to_datetime(df['NgayCapNhat'])
    
    # HÀM SỬA LỖI SỐ (Giữ nguyên logic cũ của ông)
    def fix_so_lieu(val):
        s = str(val)
        if not s: return 0.0
        s = s.replace(',', '.')
        try:
            match = re.search(r"(\d+\.?\d*)", s)
            if match:
                num = float(match.group(1))
                while num > 13: # Logic chia 10
                    num = num / 10
                return num
            return 0.0
        except: return 0.0

    # Áp dụng sửa lỗi cho các cột số
    for col in df.columns:
        if col not in ["Ngân hàng", "NgayCapNhat"]:
            df[col] = df[col].apply(fix_so_lieu)
            
    return df

try:
    df = load_data()

    # --- PHẦN 1: GIAO DIỆN CŨ (GIỮ NGUYÊN) ---
    # Lấy ngày mới nhất để hiển thị
    latest_date = df['NgayCapNhat'].max()
    st.caption(f"Cập nhật lúc: {latest_date}")

    # Lọc dữ liệu chỉ lấy ngày mới nhất để vẽ biểu đồ cột
    df_today = df[df['NgayCapNhat'] == latest_date].copy()

    # Chọn kỳ hạn
    cols_lai_suat = [c for c in df.columns if 'tháng' in c]
    ky_han = st.selectbox("Chọn kỳ hạn:", cols_lai_suat, index=3) # Mặc định 12 tháng

    # Vẽ biểu đồ cột (Bar Chart)
    if ky_han:
        df_sort = df_today.sort_values(by=ky_han, ascending=False)
        
        fig = px.bar(
            df_sort, 
            x='Ngân hàng', 
            y=ky_han,
            text_auto='.2f', 
            color=ky_han,
            color_continuous_scale='Greens',
            title=f"Bảng xếp hạng lãi suất {ky_han} (Mới nhất)"
        )
        
        fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        fig.update_layout(height=500, yaxis_range=[0, 15], yaxis_title="Lãi suất (%)")
        
        st.plotly_chart(fig, use_container_width=True)

    # Hiển thị bảng chi tiết (Full Table)
    with st.expander("Xem bảng số liệu chi tiết", expanded=True):
        st.dataframe(df_today)

    # --- PHẦN 2: TÍNH NĂNG MỚI (PHÂN TÍCH XU HƯỚNG) ---
    st.markdown("---") # Kẻ một đường ngang ngăn cách
    st.header("📈 Xu hướng thị trường (Tính năng mới)")
    
    # Bộ lọc thời gian
    col1, col2 = st.columns([1, 4])
    with col1:
        time_option = st.selectbox(
            "Thời gian:",
            ["1 tháng qua", "3 tháng qua", "6 tháng qua", "1 năm qua", "Tất cả"],
            index=1
        )

    # Xử lý lọc ngày
    end_date = df['NgayCapNhat'].max()
    if time_option == "1 tháng qua": start_date = end_date - timedelta(days=30)
    elif time_option == "3 tháng qua": start_date = end_date - timedelta(days=90)
    elif time_option == "6 tháng qua": start_date = end_date - timedelta(days=180)
    elif time_option == "1 năm qua": start_date = end_date - timedelta(days=365)
    else: start_date = df['NgayCapNhat'].min()

    # Lọc dữ liệu lịch sử
    df_history = df[(df['NgayCapNhat'] >= start_date) & (df['NgayCapNhat'] <= end_date)]

    # Tính trung bình lãi suất các kỳ hạn theo ngày
    target_cols = ['3 tháng', '6 tháng', '12 tháng', '24 tháng']
    valid_cols = [c for c in target_cols if c in df.columns]

    if not df_history.empty and valid_cols:
        # Gom nhóm theo ngày và tính trung bình
        df_trend = df_history.groupby('NgayCapNhat')[valid_cols].mean().reset_index()
        
        # Vẽ biểu đồ đường (Line Chart)
        fig_line = px.line(
            df_trend, 
            x='NgayCapNhat', 
            y=valid_cols,
            markers=True,
            title="Biến động lãi suất trung bình theo thời gian",
            labels={"value": "Lãi suất trung bình (%)", "NgayCapNhat": "Ngày", "variable": "Kỳ hạn"}
        )
        fig_line.update_layout(hovermode="x unified", height=450, yaxis_range=[0, 10])
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Chưa có đủ dữ liệu lịch sử để vẽ biểu đồ xu hướng.")

except Exception as e:
    st.error(f"Có lỗi xảy ra: {e}")
