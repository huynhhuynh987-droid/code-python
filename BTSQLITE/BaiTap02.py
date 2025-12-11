import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re
import os # Thêm thư viện để kiểm tra/xóa file DB (tùy chọn)
############################################################################
# I. Cấu hình SQLite và Khởi tạo
############################################################################

DB_FILE = 'Painters_Data.db'
TABLE_NAME = 'painters_info'
all_links = []
LIMIT = 50 # <-- ĐÃ TĂNG GIỚI HẠN LÊN 50 HỌA SĨ

# Xóa DB cũ nếu muốn bắt đầu mới
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Đã xóa file DB cũ: {DB_FILE}")

# Mở kết nối SQLite và tạo bảng nếu chưa tồn tại
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    name TEXT PRIMARY KEY, --sử dụng tên làm khóa chính để tránh trùng lặp
    birth TEXT,
    death TEXT,
    nationality TEXT
);
"""
cursor.execute(create_table_sql) #gửi câu lệnh sql để tạo bảng sqlite
conn.commit() #lưu thay đổi vào database
print(f"Đã kết nối và chuẩn bị bảng '{TABLE_NAME}' trong '{DB_FILE}'.") #thông báo

# Khởi tạo driver
driver = webdriver.Chrome()

############################################################################
# II. Lấy Đường dẫn (Phase 1)
############################################################################

print("\n--- Đang lấy danh sách links ---")
try:
    url = "https://en.wikipedia.org/wiki/List_of_painters_by_name_beginning_with_%22F%22"
    driver.get(url) #mở url
    time.sleep(3)

    content_div = driver.find_element(By.CLASS_NAME, "mw-parser-output") # tìm và lưu trữ div chứa toàn bộ nd bài viết
    ul_tags = content_div.find_elements(By.TAG_NAME, "ul") #tìm all các thẻ ds k thứ tự bên trong bài viết

    for ul in ul_tags:
        li_tags = ul.find_elements(By.TAG_NAME, "li")
        if len(li_tags) > 5: #lọc các ul có trên 5 mục mới được xem là danh sách danh họa thật.
            for tag in li_tags:
                try:
                    link = tag.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    if ("/wiki/" in link) and \
                        ("List_of_painters" not in link) and \
                        ("cite_note" not in link) and \
                        ("Category:" not in link) and \
                        ("Special:" not in link) and \
                        ("Help:" not in link):
                        
                        all_links.append(link) 
                except:
                    pass
    
    all_links = list(set(all_links)) # loại bỏ trùng link
    print(f"Tìm thấy {len(all_links)} họa sĩ thực sự.")

except Exception as e:
    print("Error getting links:", e)

# Giới hạn link cào
links_to_scrape = all_links[:LIMIT]


############################################################################
# III. Duyệt qua từng link và LƯU VÀO SQLITE (Phase 2)
############################################################################

print("\n--- Bắt đầu Cào và Lưu vào SQLite ---")

insert_sql = f"""
INSERT OR IGNORE INTO {TABLE_NAME} (name, birth, death, nationality) 
VALUES (?, ?, ?, ?);
"""
count = 0
for link in links_to_scrape:
    count += 1

    print(f"({count}) Đang xử lý: {link}")
    
    # Khởi tạo giá trị cho mỗi lần cào
    name = birth = death = nationality = "" 
    
    try:
        driver.get(link)
        time.sleep(1) 

        # 1. Lấy tên họa sĩ
        try:
            name = driver.find_element(By.ID, "firstHeading").text
        except:
            name = ""

        # 2. Lấy ngày sinh (Born)
        try:
            birth_element = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
            birth = birth_element.text
            res = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', birth)
            birth = res[0] if res else birth 
        except:
            birth = ""

        # 3. Lấy ngày mất (Died)
        try:
            death_element = driver.find_element(By.XPATH, "//th[text()='Died']/following-sibling::td")
            death = death_element.text
            res = re.findall(r'[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}', death)
            death = res[0] if res else death
        except:
            death = ""

        # 4. Lấy Nationality
        try:
            nat_element = driver.find_element(By.XPATH, "//th[text()='Nationality']/following-sibling::td")
            nationality = nat_element.text.strip().split('\n')[0]
        except:
            # Fallback lấy từ Born (Chỉ lấy phần cuối cùng)
            try:
                birth_element = driver.find_element(By.XPATH, "//th[text()='Born']/following-sibling::td")
                #Dòng lệnh này yêu cầu Selenium tìm trong trang web một ô tiêu đề bảng 
                # <th> có nội dung là “Born”, sau đó lấy ô dữ liệu <td> nằm ngay bên cạnh nó trên cùng một hàng.
                birth_text = birth_element.text
                if "," in birth_text:
                    parts = birth_text.split(",")
                    nationality = parts[-1].strip().split('\n')[0] 
            except:
                nationality = ""
        
        # LƯU VÀO SQLITE
        cursor.execute(insert_sql, (name, birth, death, nationality))
        conn.commit()
        print(f"   -> Đã lưu thành công: {name}")

    except Exception as e:
        print(f"Lỗi tại link {link}: {e}")

print("\n--- Hoàn tất Cào và Lưu trữ ---")

############################################################################
# IV. Ket thuc (Truy vấn SQLite và Đóng kết nối)
driver.quit() #đóng toàn bộ cửa sổ

print("\n" + "="*70)
print("KIỂM TRA DỮ LIỆU SQLITE")

# 1. Truy vấn toàn bộ dữ liệu từ DB (Dùng Pandas để truy vấn và format)
query = f"SELECT * FROM {TABLE_NAME}"
final_data = pd.read_sql_query(query, conn) 

# 2. In kết quả
print("\n--- KẾT QUẢ TRUY VẤN (TỔNG HỢP) ---")
print(final_data.to_string(index=False))

# 3. Đếm tổng số lượng
total_painters = len(final_data)
print(f"\nTổng số họa sĩ đã được lưu trữ trong DB: {total_painters}")


#############################################
# A. THỐNG KÊ & TOÀN CỤC
#print ("1.dem tong so hoa si:")
#query=f"select count (*) from {table name}

#############################################

# 1. Đếm tổng số họa sĩ
print("1. Tổng số họa sĩ trong bảng:")
query = f"SELECT COUNT(*) FROM {TABLE_NAME}"
cursor.execute(query)
print(cursor.fetchone()[0], "\n")

# 2. Hiển thị 5 dòng đầu tiên
print("2. 5 dòng đầu tiên:")
query = f"SELECT * FROM {TABLE_NAME} LIMIT 5"
print(pd.read_sql_query(query, conn), "\n")

# 3. Danh sách quốc tịch duy nhất 
print("3. Các quốc tịch duy nhất:")
query = f"SELECT DISTINCT nationality FROM {TABLE_NAME} WHERE nationality IS NOT NULL AND nationality != ''"
rows = cursor.execute(query).fetchall()
for r in rows:
    print("-", r[0])
print("\n")

#############################################
# B. LỌC & TÌM KIẾM
#############################################

# 4. Tên bắt đầu bằng F
print("4. Các họa sĩ có tên bắt đầu bằng 'F':")
query = f"SELECT name FROM {TABLE_NAME} WHERE name LIKE 'F%'"
print(pd.read_sql_query(query, conn), "\n")

# 5. Quốc tịch chứa 'French'
print("5. Các họa sĩ có quốc tịch chứa 'French':")
query_5 = f"SELECT name, nationality FROM {TABLE_NAME} WHERE nationality LIKE '%French%'"
print(pd.read_sql_query(query_5, conn), "\n")


# 6. Không có quốc tịch
print("6. Các họa sĩ không có quốc tịch:")
query = f"SELECT name FROM {TABLE_NAME} WHERE nationality IS NULL OR nationality = ''"
print(pd.read_sql_query(query, conn), "\n")

# 7. Có đầy đủ birth và death
print("7. Họa sĩ có cả ngày sinh và ngày mất:")
query = f"""
SELECT name FROM {TABLE_NAME}
WHERE birth IS NOT NULL AND birth != ''
  AND death IS NOT NULL AND death != ''
"""
print(pd.read_sql_query(query, conn), "\n")

# 8. Tên chứa 'Fales'
print("8. Họa sĩ có tên chứa 'Fales':")
query = f"SELECT * FROM {TABLE_NAME} WHERE name LIKE '%Fales%'"
print(pd.read_sql_query(query, conn), "\n")


#############################################
# C. NHÓM & SẮP XẾP
#############################################

# 9. Sắp xếp theo tên A–Z
print("9. Danh sách họa sĩ (A → Z):")
query = f"SELECT name FROM {TABLE_NAME} ORDER BY name ASC"
print(pd.read_sql_query(query, conn), "\n")

# 10. Nhóm theo quốc tịch và đếm
print("10. Số lượng họa sĩ theo từng quốc tịch:")
query = f"""
SELECT nationality, COUNT(*) AS total
FROM {TABLE_NAME}
WHERE nationality IS NOT NULL AND nationality != ''
GROUP BY nationality
ORDER BY total DESC
"""
print(pd.read_sql_query(query, conn), "\n")
# 4. Đóng kết nối DB
conn.close()
print("Đã đóng kết nối cơ sở dữ liệu.")
print("\n" + "="*70)
print("THỰC HIỆN CÁC YÊU CẦU TRUY VẤN SQL\n")