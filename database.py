import sqlite3

def get_db_connection():
    conn = sqlite3.connect('immunisation.db')
    conn.row_factory = sqlite3.Row   # Trả về dạng dict để dễ dùng
    return conn

# Kiểm tra các bảng trong database
def get_tables():
    conn = get_db_connection()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    conn.close()
    return [table[0] for table in tables]

# Test database
if __name__ == "__main__":
    print("Tables in database:", get_tables())