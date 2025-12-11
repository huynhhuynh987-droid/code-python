import sqlite3
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
import pandas as pd


# --- 1. CẤU HÌNH ---
DB_FILE = 'longchau_db.sqlite'
TABLE_NAME = 'products'  # Đặt tên bảng thống nhất là 'products'

# --- 2. KHỞI TẠO DATABASE ---
if os.path.exists(DB_FILE):
    os.remove(DB_FILE) # Xóa làm mới để test cho sạch
    print(f"[*] Đã xóa file DB cũ: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Tạo bảng 
sql_create = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id TEXT,
        product_name TEXT,
        price REAL,
        original_price REAL,
        unit TEXT,
        product_url TEXT PRIMARY KEY,
        image_url TEXT,
        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""

cursor.execute(sql_create)
conn.commit()
print(f"[*] Đã tạo bảng '{TABLE_NAME}' thành công.")

# --- 3. KHỞI TẠO SELENIUM (Sử dụng Chrome/Edge) ---
chrome_options = ChromeOptions()
# Bật chế độ headless (ẩn giao diện) để chạy nhanh và nhẹ hơn
# Thay đổi thành False nếu muốn thấy cửa sổ trình duyệt hiện ra
chrome_options.headless = True 

# Khởi tạo WebDriver. Selenium sẽ tự động tìm kiếm Chromedriver.
driver = webdriver.Chrome(options=chrome_options) 
url = 'https://nhathuoclongchau.com.vn/duoc-my-pham/cham-soc-da-mat'
try:
    print(f"[*] Đang truy cập: {url}")
    driver.get(url)
    time.sleep(3)

    # --- 4. CUỘN TRANG & CLICK XEM THÊM ---
    body = driver.find_element(By.TAG_NAME, "body")
    
    # Click xem thêm (chỉ click 2 lần để đảm bảo có đủ khoảng 50 sản phẩm)
    for k in range(10): 
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "Xem thêm" in btn.text and "sản phẩm" in btn.text:
                    driver.execute_script("arguments[0].click();", btn) #được dùng để đảm bảo cú click hoạt động ngay cả khi nút không hoàn toàn trong tầm nhìn
                    time.sleep(2)
                    print(f" -> Đã click 'Xem thêm' lần {k+1}")
                    break
        except: pass
    
    # Cuộn trang
    print("[*] Đang cuộn trang...")
    for i in range(20): 
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.1)
    time.sleep(3)

    # --- 5. TÌM NÚT CHỌN MUA ĐỂ XÁC ĐỊNH VỊ TRÍ SP ---
    buttons = driver.find_elements(By.XPATH, "//button[text()='Chọn mua']")
    print(f"[*] Tìm thấy {len(buttons)} sản phẩm. Bắt đầu lưu...")

    # --- 6. VÒNG LẶP XỬ LÝ TỪNG SẢN PHẨM ---
    max_products = 50
    for i, bt in enumerate(buttons, 1):
        if i > max_products:
            print(f"[*] Đã đạt giới hạn {max_products} sản phẩm. Dừng cào.")
            break

        try:
            # Tìm thẻ cha chứa thông tin
            parent_div = bt
            for _ in range(3):
                parent_div = parent_div.find_element(By.XPATH, "./..")
            sp = parent_div
            
            # --- [QUAN TRỌNG] Lấy toàn bộ text để xử lý ---
            full_text = sp.text 

            # A. Lấy Tên SP
            try:tsp = sp.find_element(By.TAG_NAME, 'h3').text
            except:
                tsp = "No Name"

            # B. Lấy URL & ID
            try:
                p_url = sp.find_element(By.TAG_NAME, 'a').get_attribute('href')
                # Tách ID từ URL (VD: ...-30144.html -> 30144)
                p_id = p_url.split('-')[-1].replace('.html', '')
            except:
                p_url = f"unknown_{i}"
                p_id = str(i)

            # D. XỬ LÝ GIÁ & UNIT (Logic Regex)
            price_number = 0
            original_price = 0
            unit = "Không xác định"

            lines = full_text.split('\n')
            for line in lines:
                if 'đ' in line: #chỉ quan tâm các dòng có ký hiệu tiền Việt
                    clean_line = line.replace('.', '').replace(',', '') #loại bỏ dấu chấm và dấu phẩy
                    # Tìm số trong dòng
                    numbers = re.findall(r'\d+', clean_line) #tìm tất cả chuỗi số liên tiếp trong dòng.
                    if numbers:
                        found_price = float(numbers[0]) #lấy số đầu tiên xuất hiện trong dòng làm giá tạm.
                        
                        # Nếu có dấu /, đây là giá chính kèm đơn vị
                        if '/' in line:
                            price_number = found_price #lưu giá
                            unit = line.split('/')[-1].strip().replace('đ', '') #lấy phần sau dấu / và xóa khoảng trắng
                            # Nếu chưa có giá, lấy tạm số đầu tiên tìm thấy
                        elif price_number == 0:
                            price_number = found_price

            # E. Xử lý Giá Gốc (Class gạch ngang)
            try:
                org_elem = sp.find_element(By.CSS_SELECTOR, ".line-through") #tìm thẻ HTML có class line-through, thường là giá gạch ngang (giá cũ trước khi giảm).
                org_text = org_elem.text.replace('.', '').replace('đ', '').strip()
                original_price = float(re.findall(r'\d+', org_text)[0]) #lấy số đầu tiên làm giá gốc.
            except:
                original_price = 0 #nếu k tìm thấy thẻ => giá gốc =0

            # --- 7. LƯU TỨC THỜI VÀO DB ---
            if tsp:
                sql = f'''
                    INSERT OR IGNORE INTO {TABLE_NAME}
                    (id, product_name, price, original_price, unit, product_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(sql, (p_id, tsp, price_number, original_price, unit, p_url))
                conn.commit() # Commit ngay lập tức
                print(f"[{i}] Đã lưu: {tsp[:30]}... | {price_number}")

        except Exception as e:
            # print(f"Lỗi sp {i}: {e}") 
            continue

except Exception as e:
    print(f"Lỗi chương trình: {e}")

# finally:
#     # Đảm bảo đóng trình duyệt và kết nối DB
#     if 'driver' in locals() and driver:
#         driver.quit()
#     if 'conn' in locals() and conn:
#         conn.close()
#     print("\nHoàn tất quá trình cào và lưu dữ liệu tức thời.")
    # --- 3. KẾT NỐI VÀ THỰC THI CHÍNH ---
# conn = None
# try:
#     conn = sqlite3.connect(DB_FILE)
# except Exception as e:
#     print(f"\nLỖI CHUNG XẢY RA: {e}")

# finally:
#     # Đóng kết nối
#     if conn:
#         conn.close()
#         print("\n--- ĐÃ ĐÓNG KẾT NỐI DATABASE. KẾT THÚC CHƯƠNG TRÌNH ---")
# --- TRUY VẤN ĐÃ CHỈNH SỬA ---
# --- 3. KẾT NỐI VÀ THỰC THI CHÍNH ---
# conn = None
# try:
#     conn = sqlite3.connect(DB_FILE)
# except Exception as e:
#     print(f"\nLỖI CHUNG XẢY RA: {e}")

# finally:
#     # Đóng kết nối
#     if conn:
#         conn.close()
#   
 ##Yêu Cầu Phân Tích Dữ Liệu
print("\n===== NHÓM 1: KIỂM TRA CHẤT LƯỢNG DỮ LIỆU =====\n")

# 1. Kiểm tra TRÙNG LẶP theo product_url hoặc product_name
cursor.execute(f"""
SELECT product_name, product_url, COUNT(*) AS so_lan
FROM {TABLE_NAME}
GROUP BY product_name, product_url
HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
print("1. Các bản ghi trùng lặp (theo product_url hoặc product_name):")
print(duplicates, "\n")

# 2. Kiểm tra dữ liệu thiếu giá (price NULL hoặc = 0)
cursor.execute(f"""
SELECT COUNT(*)
FROM {TABLE_NAME}
WHERE price IS NULL OR price = 0
""")
missing_price = cursor.fetchone()[0]
print(f"2. Số sản phẩm thiếu giá bán (price NULL hoặc 0): {missing_price}\n")

# 3. Kiểm tra giá bất thường (price > original_price)
cursor.execute(f"""
SELECT product_name, price, original_price
FROM {TABLE_NAME}
WHERE price IS NOT NULL AND original_price IS NOT NULL
  AND price > original_price
""")
wrong_price = cursor.fetchall()
print("3. Sản phẩm có giá bất thường (price > original_price):")
print(wrong_price, "\n")

# 4. Kiểm tra định dạng – danh sách unit duy nhất
cursor.execute(f"SELECT DISTINCT unit FROM {TABLE_NAME}")
units = cursor.fetchall()
print("4. Các đơn vị tính (unit) duy nhất:")
print(units, "\n")


# 5. Tổng số lượng bản ghi trong bảng
cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
total = cursor.fetchone()[0]
print(f"5. Tổng số sản phẩm đã được cào: {total}\n")

print("\n===== NHÓM 2: KHẢO SÁT & PHÂN TÍCH =====\n")
# 1. 10 sản phẩm có mức giảm giá lớn nhất
cursor.execute(f"""
SELECT product_name, price, original_price,
       (original_price - price) AS giam_gia
FROM {TABLE_NAME}
WHERE price IS NOT NULL AND original_price IS NOT NULL
ORDER BY giam_gia DESC
LIMIT 10
""")
top_discount = cursor.fetchall()
print("1. Top 10 sản phẩm giảm giá nhiều nhất:")
print(top_discount, "\n")

# 2. Sản phẩm đắt nhất
cursor.execute(f"""
SELECT *
FROM {TABLE_NAME}
WHERE price IS NOT NULL
ORDER BY price DESC
LIMIT 1
""")
highest_price = cursor.fetchone()
print("2. Sản phẩm có giá bán cao nhất:")
print(highest_price, "\n")

# 3. Thống kê số lượng sản phẩm theo đơn vị tính (unit)
cursor.execute(f"""
SELECT unit, COUNT(*) AS so_luong
FROM {TABLE_NAME}
GROUP BY unit
ORDER BY so_luong DESC
""")
unit_stat = cursor.fetchall()
print("3. Số lượng sản phẩm theo từng đơn vị (unit):")
print(unit_stat, "\n")

# 4. Tìm sản phẩm chứa từ khóa 'Vitamin C'
cursor.execute(f"""
SELECT *
FROM {TABLE_NAME}
WHERE product_name LIKE '%Vitamin C%'
""")
vitamin_c_products = cursor.fetchall()
print("4. Sản phẩm có tên chứa 'Vitamin C':")
print(vitamin_c_products, "\n")

# 5. Lọc sản phẩm có giá từ 100k đến 200k
cursor.execute(f"""
SELECT *
FROM {TABLE_NAME}
WHERE price BETWEEN 100000 AND 200000
""")
filtered_price = cursor.fetchall()
print("5. Sản phẩm có giá trong khoảng 100.000 – 200.000 VNĐ:")
print(filtered_price, "\n")

print("\n===== NHÓM 3: CÁC TRUY VẤN NÂNG CAO =====\n")

# 1. Sắp xếp tất cả sản phẩm theo giá bán từ thấp đến cao
cursor.execute(f"""
SELECT product_name, price
FROM {TABLE_NAME}
WHERE price IS NOT NULL
ORDER BY price ASC 
""")
sorted_price = cursor.fetchall()
print("1. Danh sách sản phẩm (sắp xếp theo giá tăng dần):")
print(sorted_price[:20], "... (hiển thị 20 dòng đầu)\n")

# 2. Top 5 sản phẩm có phần trăm giảm giá cao nhất
cursor.execute(f"""
SELECT product_name, price, original_price,
       ROUND((original_price - price) * 100.0 / original_price, 2) AS percent_discount
FROM {TABLE_NAME}
WHERE price IS NOT NULL 
  AND original_price IS NOT NULL 
  AND original_price > 0
ORDER BY percent_discount DESC
LIMIT 5
""")
discount_percent = cursor.fetchall()
print("2. Top 5 sản phẩm có phần trăm giảm giá cao nhất:")
print(discount_percent, "\n")

# 3. Xóa bản ghi trùng lặp (chỉ giữ 1 bản ghi cho mỗi product_name)
# --- Bước 1: xem trùng lặp (không bắt buộc nhưng hữu ích)
cursor.execute(f"""
SELECT product_name, COUNT(*)
FROM {TABLE_NAME}
GROUP BY product_name
HAVING COUNT(*) > 1
""")
dups_check = cursor.fetchall()
print("3.1. Các product_name bị trùng trước khi xóa:")
print(dups_check, "\n")

# --- Bước 2: xóa trùng bằng CTE (chỉ giữ bản ghi có product_url nhỏ nhất)
cursor.execute(f"""
WITH ranked AS (
    SELECT rowid AS rid, 
           product_name,
           ROW_NUMBER() OVER (PARTITION BY product_name ORDER BY product_url) AS rn
    FROM {TABLE_NAME}
)
DELETE FROM {TABLE_NAME}
WHERE rowid IN (SELECT rid FROM ranked WHERE rn > 1);
""")
conn.commit()

print("3.2. Đã xóa các bản ghi trùng lặp (giữ lại 1 bản ghi mỗi product_name).\n")

# 4. Phân tích nhóm giá
cursor.execute(f"""
SELECT
    CASE
        WHEN price < 50000 THEN 'Dưới 50k'
        WHEN price BETWEEN 50000 AND 100000 THEN '50k - 100k'
        WHEN price BETWEEN 100000 AND 200000 THEN '100k - 200k'
        ELSE 'Trên 200k'
    END AS nhom_gia,
    COUNT(*) AS so_luong
FROM {TABLE_NAME}
GROUP BY nhom_gia
ORDER BY so_luong DESC
""")
price_group = cursor.fetchall()
print("4. Phân tích số lượng sản phẩm theo nhóm giá:")
print(price_group, "\n")

# 5. Liệt kê các bản ghi có product_url NULL hoặc rỗng
cursor.execute(f"""
SELECT *
FROM {TABLE_NAME}
WHERE product_url IS NULL OR product_url = ''
""")
bad_urls = cursor.fetchall()
print("5. Các bản ghi có URL không hợp lệ:")
print(bad_urls, "\n")
conn = None
try:
    conn = sqlite3.connect(DB_FILE)
except Exception as e:
    print(f"\nLỖI CHUNG XẢY RA: {e}")

finally:
    # Đóng kết nối
    if conn:
        conn.close()
        print("\n--- ĐÃ ĐÓNG KẾT NỐI DATABASE. KẾT THÚC CHƯƠNG TRÌNH ---")

