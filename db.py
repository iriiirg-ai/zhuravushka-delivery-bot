import sqlite3
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH

DEFAULT_PRODUCTS = [
    ("Сырники", "Сырники шпинатные", "450 г", 0, 0),
    ("Сырники", "Сырники с вишней", "450 г", 0, 0),
    ("Сырники", "Сырники с маком", "450 г", 0, 0),
    ("Сырники", "Сырники классические", "450 г", 0, 0),
    ("Сырники", "Сырники с вялеными томатами", "450 г", 0, 0),
    ("Сырники", "Сырники банановые", "450 г", 0, 0),
    ("Сырники", "Сырники клубничные", "450 г", 0, 0),
    ("Сырники", "Сырники с халвой", "450 г", 0, 0),
    ("Сырники", "Сырники из тофу", "450 г", 0, 0),
    ("Сырники", "Сырники с шоколадной крошкой", "450 г", 0, 0),
    ("Сырники", "Сырники с беконом", "450 г", 0, 0),

    ("Выпечка", "Бейглы творожные", "3 шт., 330 г", 0, 0),
    ("Выпечка", "Галета", "420 г", 0, 0),
    ("Выпечка", "Лепёшки сырно-творожные", "200 г", 0, 0),
    ("Выпечка", "Лепёшка морковно-сырная", "200 г", 0, 0),
    ("Выпечка", "Ватрушка творожная", "3 шт., 350 г", 450, 1),
    ("Выпечка", "Пирожки ленивые", "4 шт., 350 г", 400, 1),

    ("Запеканки", "Запеканка классическая", "400 г", 0, 0),
    ("Запеканки", "Запеканка зебра", "350 г", 0, 0),
    ("Запеканки", "Запеканка с маком", "370 г", 0, 0),
    ("Запеканки", "Запеканка с вишней", "370 г", 0, 0),
    ("Запеканки", "Запеканка с малиновым джемом", "370 г", 0, 0),
    ("Запеканки", "Запеканка с клубникой", "370 г", 0, 0),

    ("Полуфабрикаты", "Пельмени классические", "500 г", 0, 0),
    ("Полуфабрикаты", "Вареники капуста-мясо", "500 г", 0, 0),
    ("Полуфабрикаты", "Вареники с картошкой", "500 г", 0, 0),
    ("Полуфабрикаты", "Вареники с капустой", "500 г", 0, 0),
    ("Полуфабрикаты", "Вареники с творогом", "500 г", 0, 0),
    ("Полуфабрикаты", "Вареники с вишней", "500 г", 0, 0),
    ("Полуфабрикаты", "Ленивые вареники", "500 г", 0, 0),
    ("Полуфабрикаты", "Фрикадельки с курицей", "500 г", 0, 0),
    ("Полуфабрикаты", "Фрикадельки свинина/говядина", "500 г", 0, 0),
    ("Полуфабрикаты", "Котлета по-домашнему", "500 г", 0, 0),
    ("Полуфабрикаты", "Котлета куриная", "500 г", 0, 0),
    ("Полуфабрикаты", "Тефтели мясные", "500 г", 0, 0),
    ("Полуфабрикаты", "Котлеты куриные со шпинатом", "500 г", 0, 0),

    ("Блины и тесто", "Блины курица-сыр", "500 г", 0, 0),
    ("Блины и тесто", "Блины мясо-рис", "500 г", 0, 0),
    ("Блины и тесто", "Блины с творогом", "500 г", 0, 0),
    ("Блины и тесто", "Блины Рафаэлло", "500 г", 0, 0),
    ("Блины и тесто", "Блинчики ветчина-сыр", "600 г", 0, 0),
    ("Блины и тесто", "Блинное тесто классическое", "1 л", 280, 1),
    ("Блины и тесто", "Блинное тесто шоколадное", "1 л", 280, 1),

    ("Вафли", "Вафли классические", "160 г", 0, 0),
    ("Вафли", "Вафли сырные", "160 г", 0, 0),
    ("Вафли", "Вафли шпинатные", "160 г", 0, 0),

    ("Дополнительно", "Курица сувид", "220 г", 0, 0),
    ("Дополнительно", "Масло клубничное", "170 г", 0, 0),
    ("Дополнительно", "Масло с вялеными томатами", "160 г", 0, 0),
    ("Дополнительно", "Чесночно-зелёное масло", "140 г", 0, 0),
    ("Дополнительно", "Сёмга слабосолёная", "200 г", 0, 0),
    ("Дополнительно", "Говяжий язык", "100 г", 0, 0),
]


def _conn():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            package_label TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_tg_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            fulfillment TEXT NOT NULL,
            cafe TEXT NOT NULL,
            address TEXT,
            total INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            staff_name TEXT,
            work_chat_message_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            package_label TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        );
        """)
        for category, name, package_label, price, active in DEFAULT_PRODUCTS:
            conn.execute(
                """INSERT OR IGNORE INTO products(category,name,package_label,price,active)
                   VALUES(?,?,?,?,?)""",
                (category, name, package_label, price, active),
            )


def list_categories():
    with _conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT category FROM products
               WHERE active=1 AND price>0
               ORDER BY category COLLATE NOCASE"""
        ).fetchall()
        return [r["category"] for r in rows]


def list_products(category: Optional[str] = None, active_only: bool = True):
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if category is not None:
        sql += " AND category=?"
        args.append(category)
    if active_only:
        sql += " AND active=1 AND price>0"
    sql += " ORDER BY category COLLATE NOCASE, name COLLATE NOCASE"
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def get_product(product_id: int):
    with _conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        return dict(row) if row else None


def add_product(category, name, package_label, price, active=1):
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO products(category,name,package_label,price,active)
               VALUES(?,?,?,?,?)""",
            (category.strip(), name.strip(), package_label.strip(), int(price), int(active)),
        )
        return cur.lastrowid


def update_product(product_id, **fields):
    allowed = {"category", "name", "package_label", "price", "active"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    args = list(fields.values()) + [product_id]
    with _conn() as conn:
        conn.execute(f"UPDATE products SET {sets} WHERE id=?", args)


def set_setting(key, value):
    with _conn() as conn:
        conn.execute(
            """INSERT INTO settings(key,value) VALUES(?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (key, str(value)),
        )


def get_setting(key):
    with _conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def create_order(guest_tg_id, guest_name, phone, fulfillment, cafe, address, cart):
    total = sum(int(i["price"]) * int(i["quantity"]) for i in cart)
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO orders
               (guest_tg_id,guest_name,phone,fulfillment,cafe,address,total)
               VALUES(?,?,?,?,?,?,?)""",
            (guest_tg_id, guest_name, phone, fulfillment, cafe, address, total),
        )
        order_id = cur.lastrowid
        for i in cart:
            conn.execute(
                """INSERT INTO order_items
                   (order_id,product_id,product_name,package_label,price,quantity)
                   VALUES(?,?,?,?,?,?)""",
                (
                    order_id,
                    i.get("product_id"),
                    i["name"],
                    i["package_label"],
                    int(i["price"]),
                    int(i["quantity"]),
                ),
            )
        return order_id


def get_order(order_id):
    with _conn() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
        ).fetchall()
        return (dict(order) if order else None, [dict(i) for i in items])


def update_order(order_id, **fields):
    allowed = {"status", "staff_name", "work_chat_message_id"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    args = list(fields.values()) + [order_id]
    with _conn() as conn:
        conn.execute(f"UPDATE orders SET {sets} WHERE id=?", args)
