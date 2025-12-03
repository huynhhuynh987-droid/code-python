from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
import time
import pandas as pd

# Đường dẫn đến file thực thi geckodriver
gecko_path = r"C:\\Users\\Minh Thu\Desktop\\MÃ NGUỒN MỞ\BT SELENIUM\\geckodriver.exe"

# Khởi tởi đối tượng dịch vụ với đường geckodriver
ser = Service(gecko_path)

# Tạo tùy chọn
options = webdriver.FirefoxOptions();
options.binary_location =r"C:\Users\Minh Thu\AppData\Local\Mozilla Firefox\firefox.exe"
# Thiết lập firefox chỉ hiện thị giao diện
options.headless = False

# Khởi tạo driver
driver = webdriver.Firefox(options = options)

# Tạo url
url = 'https://gochek.vn/collections/all'

# Truy cập
driver.get(url)

# Tạm dừng khoảng 2 giây
time.sleep(1)
# Tao cac list
stt = []
ten_san_pham = []
gia_ban = []
hinh_anh = []
url_san_pham = []
mo_ta_san_pham = []
#lấy link hình ảnh của tất cả sản phẩm
products_img = driver.find_elements(By.CLASS_NAME, "product-img")
for img in products_img:
    img_link = img.find_element(By.TAG_NAME, "img").get_attribute("src")
    hinh_anh.append(img_link)
    stt.append(len(stt)+1)  
products = driver.find_elements(By.CLASS_NAME, "box-pro-detail")
#lay thong tin san pham
for product in products:
    name_pro = product.find_element(By.TAG_NAME, "a").text 
    price_pro = product.find_element(By.TAG_NAME, "p").text
    ten_san_pham.append(name_pro)
    gia_ban.append(price_pro)
    link_pro = product.find_element(By.TAG_NAME, "a").get_attribute("href")
    url_san_pham.append(link_pro)
# Truy cập trang chi tiết sản phẩm
for i in url_san_pham:
    url_detail = i
    driver.get(url_detail)
    time.sleep(1)
    #lấy thông tin mô tả sản phẩm
    try:
        mo_ta = driver.find_element(By.CLASS_NAME, "description-productdetail").text
        print(f"Mô tả sản phẩm tại {url_detail}:\n{mo_ta}\n")
        mo_ta_san_pham.append(mo_ta)
    except NoSuchElementException:
        print(f"Không tìm thấy mô tả sản phẩm tại {url_detail}\n")
    # ====== XUẤT EXCEL ======

df = pd.DataFrame({
    "STT": stt,
    "Tên sản phẩm": ten_san_pham,
    "Giá bán": gia_ban,
    "Hình ảnh": hinh_anh,
    "Link sản phẩm": url_san_pham,
    "Mô tả sản phẩm": mo_ta_san_pham
})

output_file = "gochek_all_products.xlsx"
df.to_excel(output_file, index=False)

print("Đã xuất file:", output_file)

# Tự mở file sau khi xuất xong
import os
os.startfile(output_file)



