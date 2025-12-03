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
gecko_path =r"C:\Users\Minh Thu\Desktop\MÃ NGUỒN MỞ\BT SELENIUM\BT FIREFOX\geckodriver.exe"

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
url = 'https://apps.lms.hutech.edu.vn/authn/login?next'

# Truy cập
driver.get(url)

# Tạm dừng khoảng 2 giây
time.sleep(2)

firstname_input = driver.find_element(By.XPATH, "//input[@name='emailOrUsername']")
lastname_input = driver.find_element(By.XPATH, "//input[@name='password']")

firstname_input.send_keys('huynhhuynh987@gmail.com')
time.sleep(1)
lastname_input.send_keys("PzKkZkod")

time.sleep(2)
buttton = driver.find_element(By.ID, "sign-in")
buttton.click()
time.sleep(5)

driver.quit()