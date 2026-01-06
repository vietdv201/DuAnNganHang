import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Lãi Suất Ngân Hàng", layout="wide")

st.title("💰 LÃI SUẤT NGÂN HÀNG HÔM NAY")

# --- KẾT NỐI GOOGLE SHEET ---
@st.cache_data(ttl=600) # Tự động làm mới sau 10 phút
def load_data():
    # Kiểm tra xem đang chạy trên máy hay trên GitHub
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

try:
    with st.spinner('Đang tải dữ liệu mới nhất...'):
        df = load_data()

    # Hiển thị thời gian cập nhật
    if 'NgayCapNhat' in df.columns:
        last_update = df['NgayCapNhat'].iloc[0]
        st.caption(f"Cập nhật lúc: {last_update}")

    # --- BỘ LỌC KỲ HẠN ---
    ds_ky_han = [col for col in df.columns if 'tháng' in col]
    ky_han = st.selectbox("Chọn kỳ hạn bạn muốn xem:", ds_ky_han, index=3) # Mặc định chọn 12 tháng

    # --- VẼ BIỂU ĐỒ ---
    if ky_han:
        # Sắp xếp dữ liệu từ cao xuống thấp để biểu đồ đẹp
        # Lưu ý: Data giờ là số chuẩn rồi, không cần convert nữa
        df_sort = df.sort_values(by=ky_han, ascending=False)

        # Vẽ biểu đồ cột
        fig = px.bar(
            df_sort, 
            x='Ngân hàng', 
            y=ky_han,
            title=f"Bảng xếp hạng lãi suất {ky_han}",
            text_auto='.2f', # Hiển thị 2 số sau dấu phẩy trên cột
            color=ky_han,    # Tô màu theo độ cao thấp
            color_continuous_scale='Greens' # Màu xanh lá cây (màu tiền)
        )

        # Tinh chỉnh biểu đồ cho đẹp
        fig.update_layout(
            xaxis_title="Ngân hàng",
            yaxis_title="Lãi suất (%/năm)",
            height=500
        )
        
        # Thêm dấu % vào con số hiển thị
        fig.update_traces(
            texttemplate='%{y:.2f}%', 
            textposition='outside'
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- HIỂN THỊ BẢNG DỮ LIỆU ---
    with st.expander("Xem bảng chi tiết"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Có lỗi xảy ra: {e}")
    st.info("Mẹo: Thử bấm menu 3 chấm góc phải -> Clear Cache rồi tải lại trang nhé!")