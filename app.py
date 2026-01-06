import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import json
import os

st.set_page_config(page_title="So Sánh Lãi Suất", layout="wide")

@st.cache_data(ttl=600)
def load_data():
    # Lấy chìa khóa từ cấu hình bảo mật của Streamlit
    key_content = json.loads(st.secrets["G_SHEET_CREDS"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, scope)
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    return pd.DataFrame(sheet.get_all_records())

st.title("💰 LÃI SUẤT NGÂN HÀNG HÔM NAY")

try:
    # 1. Tải dữ liệu về
    df = load_data()
    
    # --- ĐOẠN DEBUG (KIỂM TRA LỖI) ---
    st.error("👇 ĐÂY LÀ TÊN CỘT THỰC TẾ (CHỤP MÀN HÌNH CHỖ NÀY GỬI TÔI NHÉ) 👇")
    st.write(list(df.columns)) # In ra danh sách tên cột
    st.write("👇 Dữ liệu mẫu:")
    st.dataframe(df.head())    # In thử 5 dòng đầu
    # ---------------------------------

    if not df.empty:
        # Lấy cột ngày cập nhật (Cột cuối cùng)
        col_date = df.columns[0] # Cột đầu tiên là NgayCapNhat do code bot đẩy lên
        st.write(f"Cập nhật lúc: {df[col_date].iloc[0]}")
        
        # Chọn kỳ hạn
        # Lưu ý: Python phân biệt chữ hoa thường, nên ta phải lấy đúng tên trong list ở trên
        ky_han = st.selectbox("Kỳ hạn:", ["1 tháng", "6 tháng", "12 tháng", "24 tháng"], index=2)
        
        # Kiểm tra xem kỳ hạn bạn chọn có nằm trong dữ liệu không
        if ky_han in df.columns:
            # Sắp xếp và vẽ
            df_sort = df.sort_values(by=ky_han, ascending=False)
            
            fig = px.bar(df_sort, x='Ngân hàng', y=ky_han, 
                         title=f"Lãi suất {ky_han} (%)", 
                         text_auto=True, 
                         color=ky_han,
                         color_continuous_scale='Greens')
            
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_sort)
        else:
            st.warning(f"Không tìm thấy cột tên là '{ky_han}' trong dữ liệu!")
            
    else:
        st.warning("Đang chờ dữ liệu cập nhật...")

except Exception as e:
    st.error(f"Lỗi: {e}")