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
@st.cache_data(ttl=300) # Reset cache mỗi 5 phút
def load_data():
    # 1. Xác thực (Ưu tiên file key.json nếu chạy local)
    if os.path.exists('key.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    else:
        # Dùng cho khi deploy lên mạng (Streamlit Cloud)
        key_content = json.loads(os.environ['G_SHEET_CREDS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_content, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        
    client = gspread.authorize(creds)
    sheet = client.open("LaiSuatNganHang").sheet1
    
    # 2. Lấy dữ liệu thô về
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # 3. HÀM XỬ LÝ SỐ "CỤC SÚC" (BẤT CHẤP DẤU PHẨY HAY CHẤM)
    def clean_number(val):
        # Biến mọi thứ thành chuỗi để xử lý
        s = str(val)
        
        # Nếu là chuỗi rỗng hoặc None -> về 0
        if not s or s.lower() == 'nan': return 0.0
        
        # Thay dấu phẩy thành dấu chấm (Chuẩn hóa về kiểu Mỹ)
        s = s.replace(',', '.')
        
        # Dùng Regex để chỉ lấy số (vứt hết chữ %, chữ cái đi)
        match = re.search(r"(\d+\.?\d*)", s)
        if match:
            num = float(match.group(1))
            
            # --- THUẬT TOÁN "VÒNG LẶP CHIA 10" ---
            # Nguyên tắc: Lãi suất VN hiện tại không bao giờ quá 25%.
            # Nếu thấy số to hơn 25 (ví dụ 585, 485, 61), cứ chia 10 cho đến khi nó nhỏ lại.
            # 585 -> 58.5 -> 5.85 (OK dừng)
            # 61 -> 6.1 (OK dừng)
            while num > 25:
                num = num / 10
            return num
            
        return 0.0

    # 4. Áp dụng hàm xử lý cho tất cả các cột (trừ cột Ngân hàng & Ngày)
    for col in df.columns:
        if col not in ["Ngân hàng", "NgayCapNhat"]:
            df[col] = df[col].apply(clean_number)
            
    return df

# --- GIAO DIỆN CHÍNH ---
try:
    with st.spinner('Đang tải dữ liệu và sửa lỗi số học...'):
        df = load_data()

    # Hiển thị ngày cập nhật
    if 'NgayCapNhat' in df.columns:
        st.caption(f"Dữ liệu cập nhật lúc: {df['NgayCapNhat'].iloc[0]}")

    # Chọn kỳ hạn
    cols_lai_suat = [c for c in df.columns if 'tháng' in c]
    if not cols_lai_suat:
        st.error("Không tìm thấy cột lãi suất nào (kiểm tra lại tên cột trong Sheet!)")
    else:
        ky_han = st.selectbox("Chọn kỳ hạn:", cols_lai_suat, index=3) # Mặc định chọn cái thứ 4 (thường là 12 tháng)

        # Vẽ biểu đồ
        if ky_han:
            df_sort = df.sort_values(by=ky_han, ascending=False)
            
            # Tạo biểu đồ
            fig = px.bar(
                df_sort, 
                x='Ngân hàng', 
                y=ky_han,
                text_auto='.2f', # Format hiển thị 2 số lẻ
                color=ky_han,
                color_continuous_scale='Greens'
            )
            
            # Tinh chỉnh hiển thị
            fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
            fig.update_layout(height=500, xaxis_title=None, yaxis_title="Lãi suất (%)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Hiện bảng số liệu bên dưới để đối chiếu
            with st.expander("Bảng số liệu gốc (Đã xử lý)"):
                st.dataframe(df)

except Exception as e:
    st.error(f"Toang rồi ông giáo ạ! Lỗi nè: {e}")
    st.info("Thử bấm dấu 3 chấm góc phải trên -> Clear Cache xem sao.")