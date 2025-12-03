from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import time

# Đường dẫn đến file geckodriver (đặt cùng thư mục)
gecko_path = r"C:\Users\Minh Thu\Desktop\MÃ NGUỒN MỞ\BT SELENIUM\BT FIREFOX\geckodriver.exe"
# Khởi tạo đối tượng dịch vụ
ser = Service(gecko_path)

# Tạo tùy chọn
options = webdriver.FirefoxOptions() # Cách viết ngắn gọn và hiện đại hơn
# SỬA LỖI ĐƯỜNG DẪN: Sửa đường dẫn binary_location
# TÌM LẠI đường dẫn đến file firefox.exe của bạn
options.binary_location = r"C:\Users\Minh Thu\AppData\Local\Mozilla Firefox\firefox.exe"
# thiết lập firefox chỉ hiên thị giao diện
options.headless = False

# khởi tạo driver
driver = webdriver.Firefox(options=options, service=ser)

# tạo url (Đã dùng AJAX Demo)
url = "http://pythonscraping.com/pages/javascript/ajaxDemo.html"
# truy cập 
driver.get(url)

# in ra một nội dung của trang web
print("Before:===============\n")
print(driver.page_source)

# tạm dừng khoảng 3s (Đợi AJAX tải xong)
time.sleep(3)

# in lại
print("\n\n\n\nAfter: =============\n")
print(driver.page_source)

# đóng browser
driver.quit()