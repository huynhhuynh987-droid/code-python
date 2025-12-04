from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time
import pandas as pd
import os
import re 

# --- 1. KHỞI TẠO VÀ TRUY CẬP ---
driver = webdriver.Chrome() 
URL = "https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_tr%C6%B0%E1%BB%9Dng_%C4%91%E1%BA%A1i_h%E1%BB%8Dc,_h%E1%BB%8Dc_vi%E1%BB%87n_v%C3%a0_cao_%C4%91%E1%BA%B3ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam"
driver.get(URL)
time.sleep(3) 

all_institutions_data = []

# --- 2. TÌM VÀ CHUẨN BỊ DUYỆT BẢNG ---
tables_initial = driver.find_elements(By.CSS_SELECTOR, "table.wikitable")
num_tables = len(tables_initial)
print(f"Đã tìm thấy tổng cộng {num_tables} bảng dữ liệu. Bắt đầu thu thập...")

# --- CẤU HÌNH INDEX THỬ NGHIỆM TỐI ƯU ---
NAME_INDICES = [1, 2] # Tên Trường
# Thử nghiệm phạm vi cột rộng hơn: từ index 3 đến index 7 (Cột 4 đến Cột 8)
RECTOR_INDICES = [5, 4, 6, 7, 3] 

# Hàm kiểm tra xem chuỗi có phải là tên người hợp lệ không (Đã nới lỏng bộ lọc)
def is_valid_rector(text):
    text = text.strip().replace('[1]', '').replace('[2]', '').replace('[3]', '').replace('[4]', '')
    # Kiểm tra: Phải có ít nhất 2 từ (first name, last name), không phải là số/ngày tháng
    if not text or len(text) < 5 or text.isdigit() or len(text.split()) < 2:
        return False
    # Loại bỏ nếu nó giống định dạng địa chỉ/ngày tháng: (VD: Hà Nội, 1/1/2020)
    if any(char in text for char in ['/', '-', ',', '...']):
        return False
    return True

# --- 3. DUYỆT VÀ KHẮC PHỤC LỖI ---
for table_index in range(num_tables):
    try:
        # Khắc phục lỗi StaleElementReferenceException
        current_tables = driver.find_elements(By.CSS_SELECTOR, "table.wikitable")
        table = current_tables[table_index] 
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        for row in rows[1:]: 
            cols = row.find_elements(By.XPATH, "./td | ./th") 
            
            ten_truong = "null"
            hieu_truong = "null"
            
            # 1. Tìm Tên Trường
            for idx in NAME_INDICES:
                if len(cols) > idx and cols[idx].text.strip():
                    ten_truong = cols[idx].text.strip()
                    break
            
            # 2. Tìm Hiệu trưởng (Sử dụng vòng lặp thử index rộng hơn)
            for idx in RECTOR_INDICES:
                if len(cols) > idx:
                    text_rector = cols[idx].text.strip()
                    # Chỉ chấp nhận nếu chuỗi vượt qua bộ lọc nới lỏng
                    if is_valid_rector(text_rector):
                        hieu_truong = text_rector
                        break 
            
            # --- LƯU DỮ LIỆU ---
            final_ten_truong = ten_truong if ten_truong != "null" and len(ten_truong) > 5 and not ten_truong.isdigit() else "null"
            final_hieu_truong = hieu_truong if hieu_truong != "null" else "null"
            
            if final_ten_truong != "null":
                all_institutions_data.append({
                    "Tên Trường": final_ten_truong,
                    "Hiệu Trưởng/Giám đốc": final_hieu_truong
                })
                    
    except StaleElementReferenceException:
        print(f"⚠️ Lỗi Stale Element Reference ở bảng {table_index}. Đang tự động tìm lại và bỏ qua.")
        continue 
    except Exception as e:
        print(f"❌ Lỗi khác ở bảng {table_index}: {e}")
        continue

# --- 4. ĐÓNG VÀ XUẤT EXCEL ---
driver.quit()

df = pd.DataFrame(all_institutions_data)
df = df.drop_duplicates(subset=['Tên Trường']) 

output_file = "DanhSach_Truong_Wiki_Final_RectorFixed_v2.xlsx"
df.to_excel(output_file, index=False)

print(f"\n=======================================================")
print(f"✅ HOÀN TẤT THU THẬP. Đã lưu {len(df)} trường vào file:")
print(f"   {output_file}")
print("=======================================================")
os.startfile(output_file)