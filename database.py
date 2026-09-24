import sqlite3

BD_NAME = "shop_database.db"

def init_db():
    conn = sqlite3.connect(BD_NAME)
    cursor = conn.cursor()

    cursor.execute(
            '''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pubg_id TEXT NOT NULL,
            product TEXT NOT NULL,
            amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'NEW',
            worker_id INTEGER DEFAULT NULL
        )
            '''
        )
    
    conn.commit()
    conn.close()

def create_order(pubg_id: str, product: str, amount: int, category: str) -> int:
    conn = sqlite3.connect(BD_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO orders (pubg_id,product,amount,category) VALUES (?,?,?,?,?)", (pubg_id,product,amount,category))

    order_id = cursor.lastrowid or 0

    conn.commit()
    conn.close()

    return int(order_id)

def update_order_status(order_id, status: str, worker_id: int | None = None) -> bool:
    # Обновление статуса заказа и айди рабочего
    conn = sqlite3.connect(BD_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ?, worker_id = ? WHERE id = ?",(status, worker_id, order_id))

    conn.commit()
    conn.close()
    return True

def get_order_by_id(order_id: int):

    conn = sqlite3.connect(BD_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT pubg_id, product, amount,category, status, worker_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()

    conn.close()
    return order