from pygments.formatters.html import webify
from selenium import webdriver
from selenium.webdriver.common.by import By 
import time
#khoi tap webdriver
driver = webdriver.Chrome()
#mo trang 
url = "https://en.wikipedia.org/wiki/List_of_painters_by_name"
driver.get(url)
#doi khoang 2s
time.sleep(2)
#lay all cac the <a>
tags = driver.find_elements(By.XPATH, "//a[contains(@tittle,'List of painters')]")
#tao ra danh sach cac lien ket
links = (tag.get_attribute("href")for tag in tags)
#xuat thong tin
for link in links:
    print(link)
#dong webdriver
driver.quit()