import sqlite3
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH

DEFAULT_PRODUCTS = [
    ("Сырники", "Сырники со шпинатом", "450 г", 640, 1),
    ("Сырники", "Сырники с вишней", "450 г", 610, 1),
    ("Сырники", "Сырники с маком", "450 г", 590, 1),
    ("Сырники", "Сырники классические", "450 г", 520, 1),
    ("Сырники", "Сырники с вялеными томатами", "450 г", 680, 1),
    ("Сырники", "Сырники банановые", "450 г", 520, 1),
    ("Сырники", "Сырники клубничные", "450 г", 520, 1),
    ("Сырники", "Сырники с халвой", "450 г", 520, 1),
    ("Сырники", "Сырники из тофу", "450 г", 720, 1),
    ("Сырники", "Сырники с шоколадной крошкой", "450 г", 530, 1),
    ("Сырники", "Сырники с беконом", "450 г", 600, 1),

    ("Выпечка и запеканки", "Бейглы творожные, 3 шт", "330 г", 430, 1),
    ("Выпечка и запеканки", "Галета с сезонными фруктами и ягодами", "420 г", 460, 1),
    ("Выпечка и запеканки", "Лепешка сырно-творожная", "200 г", 290, 1),
    ("Выпечка и запеканки", "Лепешка морковно-творожная", "200 г", 290, 1),
    ("Выпечка и запеканки", "Запеканка классическая", "400 г", 480, 1),
    ("Выпечка и запеканки", "Запеканка зебра", "350 г", 470, 1),
    ("Выпечка и запеканки", "Запеканка с маком", "370 г", 470, 1),
    ("Выпечка и запеканки", "Запеканка с вишней", "370 г", 610, 1),
    ("Выпечка и запеканки", "Запеканка с малиновым джемом", "370 г", 490, 1),
    ("Выпечка и запеканки", "Запеканка с клубникой", "400 г", 860, 1),
    ("Выпечка и запеканки", "Ленивые вареники", "500 г", 500, 1),
    ("Выпечка и запеканки", "Ватрушки творожные", "350 г", 450, 1),
    ("Выпечка и запеканки", "Ленивые пирожки", "350 г", 400, 1),

    ("Пельмени и вареники", "Пельмени мясные", "500 г", 590, 1),
    ("Пельмени и вареники", "Вареники капуста-мясо", "500 г", 350, 1),
    ("Пельмени и вареники", "Вареники картошка", "500 г", 350, 1),
    ("Пельмени и вареники", "Вареники капуста", "500 г", 350, 1),
    ("Пельмени и вареники", "Вареники с творогом", "500 г", 350, 1),
    ("Пельмени и вареники", "Вареники с вишней", "500 г", 650, 1),

    ("Блины", "Блины курица-сыр", "500 г", 440, 1),
    ("Блины", "Блины мясо-рис", "500 г", 340, 1),
    ("Блины", "Блинчики с творогом", "500 г", 480, 1),
    ("Блины", "Блины Рафаэлло", "500 г", 360, 1),
    ("Блины", "Блинчики с припеком из зелени и ветчины", "600 г", 475, 1),
    ("Блины", "Блинчики с Нутеллой", "500 г", 480, 1),

    ("Прочее", "Фрикадельки куриные", "500 г", 500, 1),
    ("Прочее", "Фрикадельки свинина/говядина", "500 г", 800, 1),
    ("Прочее", "Котлета по-домашнему", "500 г", 550, 1),
    ("Прочее", "Куриная котлета", "500 г", 550, 1),

    ("Вафли", "Вафли классические", "160 г", 250, 1),
    ("Вафли", "Вафли сырные", "160 г", 250, 1),
    ("Вафли", "Вафли шпинатные", "160 г", 250, 1),

    ("Дополнительно", "Курица сувид", "220 г", 300, 1),
    ("Дополнительно", "Масло клубничное", "170 г", 280, 1),
    ("Дополнительно", "Масло с вялеными томатами", "160 г", 280, 1),
    ("Дополнительно", "Чесночно-зеленое масло", "140 г", 280, 1),
    ("Дополнительно", "Блинное масло классическое", "1 л", 280, 1),
    ("Дополнительно", "Блинное масло шоколадное", "1 л", 280, 1),
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
                """INSERT INTO products(category,name,package_label,price,active)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET
                       category=excluded.category,
                       package_label=excluded.package_label,
                       price=excluded.price,
                       active=1""",
                (category, name, package_label, price, 1),
            )

        # Все позиции в каталоге открыты.
        conn.execute("UPDATE products SET active=1")


def list_categories():
    with _conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT category FROM products
               WHERE active=1
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
        sql += " AND active=1"
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
