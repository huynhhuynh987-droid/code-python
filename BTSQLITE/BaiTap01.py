import sqlite3

#1. kết nối tới CSDL
conn = sqlite3.connect("inventory.db")
#tạo đối tượng "cursor" để thực thi các lệnh SQL
cursor = conn.cursor()


#2.thao tác với Database và Table
# lệnh SQ; để tạo bảng products
sql1= """
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    quantity INTEGER
)
"""
#thực thi câu lệnh tạo bảng
cursor.execute(sql1)
conn.commit() #lưu thay đổi vào DB
#3. CRUD
#3.1. Thêm (INSERT)
products_data =[
    ("Laptop A100", 999.99,15),
    ("Mouse Wỉreless X", 25.50, 50),
    ("Monitor 27-inch",249.00, 10)
     
]
#lệnh SQL để chèn dữ liệu. Dùng "?" để tráng lỗi SQL Injection
sql2 = """
INSERT INTO products(name, price, quantity)
VALUES
(?,?,?)
"""

#thêm nhiều bản ghi cùng lúc 
cursor.executemany(sql2,products_data)
conn.commit() #lưu thay đổi

#3.2. READ(SELECT)
sql3 = "SELECT*FROM products"
#thực thi truy vấn
cursor.execute(sql3)
#lấy all kết quả
all_products= cursor.fetchall()
# In tiêu đề
print(f"{'ID':<4} | {'Tên Sản Phẩm':<20} | {'Giá':<10} | {'Số Lượng':<10}")
# Lặp và in ra
for p in all_products:
    print(f"{p[0]:<4} | {p[1]:<20} | {p[2]:<10} | {p[3]:<10}")
# # 3.3 UPDATE
sql4= "UPDATE products SET price =50 WHERE name = 'Mouse Wireless'"
#thưc thi truy vấn
cursor.execute(sql4)
conn.commit()
# 3.4. DELETE
sql5= "DELETE FROM products WHERE name = 'Laptop A100'"
cursor.execute(sql5)
conn.commit()
# 4. Đóng kết nối
print("\n" + "="*50)
conn.close()
print("Đã đóng kết nối CSDL.")
