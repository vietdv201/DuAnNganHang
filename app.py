import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Phân Tích Lãi Suất", layout="wide")

# --- KẾT NỐI DỮ LIỆU ---
@st.cache_data(ttl=300)
def load_data():
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Chuyển cột NgayCapNhat sang dạng datetime để tính toán
    df['NgayCapNhat'] = pd.to_datetime(df['NgayCapNhat'])
    return df

try:
    df = load_data()
    
    # Tiêu đề
    st.title("💰 TRUNG TÂM DỮ LIỆU LÃI SUẤT")
    
    # TẠO 2 TAB CHỨC NĂNG
    tab1, tab2 = st.tabs(["📊 Bảng Xếp Hạng (Mới nhất)", "📈 Phân Tích Xu Hướng (Lịch sử)"])

    # --- TAB 1: DỮ LIỆU HÔM NAY (Code cũ nhưng tối ưu hơn) ---
    with tab1:
        # Lấy ngày mới nhất trong dữ liệu
        latest_date = df['NgayCapNhat'].max()
        st.caption(f"Dữ liệu cập nhật mới nhất: {latest_date.strftime('%d-%m-%Y')}")
        
        # Lọc ra dữ liệu của ngày mới nhất
        df_latest = df[df['NgayCapNhat'] == latest_date]
        
        cols_ky_han = [c for c in df.columns if 'tháng' in c]
        ky_han = st.selectbox("Chọn kỳ hạn so sánh:", cols_ky_han, index=3, key="s1")
        
        if ky_han:
            df_sort = df_latest.sort_values(by=ky_han, ascending=False)
            fig_bar = px.bar(
                df_sort, x='Ngân hàng', y=ky_han,
                text_auto='.2f', color=ky_han, color_continuous_scale='Greens',
                title=f"Lãi suất {ky_han} ngày {latest_date.strftime('%d/%m')}"
            )
            fig_bar.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
            fig_bar.update_layout(height=500, yaxis_range=[0, 15])
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 2: BIỂU ĐỒ ĐƯỜNG (TÍNH NĂNG MỚI) ---
    with tab2:
        st.header("Biểu đồ biến động lãi suất trung bình thị trường")
        
        # 1. Bộ lọc thời gian
        col_filter1, col_filter2 = st.columns([1, 3])
        with col_filter1:
            time_range = st.radio(
                "Chọn khoảng thời gian:",
                ["1 tháng qua", "3 tháng qua", "6 tháng qua", "1 năm qua", "Tất cả"],
                index=1
            )
        
        # Xử lý lọc ngày
        end_date = df['NgayCapNhat'].max()
        if time_range == "1 tháng qua":
            start_date = end_date - timedelta(days=30)
        elif time_range == "3 tháng qua":
            start_date = end_date - timedelta(days=90)
        elif time_range == "6 tháng qua":
            start_date = end_date - timedelta(days=180)
        elif time_range == "1 năm qua":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = df['NgayCapNhat'].min()
            
        # Lọc dữ liệu theo thời gian đã chọn
        df_filtered = df[(df['NgayCapNhat'] >= start_date) & (df['NgayCapNhat'] <= end_date)]

        # 2. Tính toán trung bình (Gom nhóm theo ngày)
        # Chỉ lấy các cột kỳ hạn quan trọng mà bạn yêu cầu
        target_cols = ['3 tháng', '6 tháng', '12 tháng', '24 tháng']
        # Đảm bảo cột tồn tại trong data
        valid_cols = [c for c in target_cols if c in df.columns]
        
        if not df_filtered.empty and valid_cols:
            # Tính trung bình cộng của tất cả ngân hàng theo từng ngày
            df_trend = df_filtered.groupby('NgayCapNhat')[valid_cols].mean().reset_index()
            
            # 3. Vẽ biểu đồ đường (Line Chart)
            fig_line = px.line(
                df_trend, 
                x='NgayCapNhat', 
                y=valid_cols,
                markers=True,
                title="Xu hướng Lãi suất Trung bình các kỳ hạn",
                labels={"value": "Lãi suất trung bình (%)", "NgayCapNhat": "Thời gian", "variable": "Kỳ hạn"}
            )
            fig_line.update_layout(hovermode="x unified", height=500, yaxis_range=[0, 10])
            st.plotly_chart(fig_line, use_container_width=True)
            
            with st.expander("Xem bảng số liệu trung bình"):
                st.dataframe(df_trend.sort_values(by='NgayCapNhat', ascending=False))
        else:
            st.warning("Chưa đủ dữ liệu lịch sử để vẽ biểu đồ này (Cần ít nhất 2 ngày dữ liệu).")

except Exception as e:
    st.error(f"Đang chờ dữ liệu tích lũy... ({e})")
