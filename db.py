import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from catalog import CATALOG
from config import DATABASE_PATH, TIMEZONE


def now_iso() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec='seconds')


def ensure_parent() -> None:
    parent = os.path.dirname(DATABASE_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)


@contextmanager
def connect():
    ensure_parent()
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            package_label TEXT NOT NULL,
            price INTEGER,
            active INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
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
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            package_label TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        );
        ''')
        for category, name, package_label, price in CATALOG:
            active = 1 if price is not None and price > 0 else 0
            db.execute('''
                INSERT OR IGNORE INTO products(category, name, package_label, price, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (category, name, package_label, price, active, now_iso()))


def set_setting(key: str, value: str) -> None:
    with connect() as db:
        db.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))


def get_setting(key: str):
    with connect() as db:
        row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row['value'] if row else None


def list_categories(active_only=True):
    q = 'SELECT DISTINCT category FROM products'
    args = []
    if active_only:
        q += ' WHERE active=1 AND price IS NOT NULL AND price>0'
    q += ' ORDER BY category'
    with connect() as db:
        return [r['category'] for r in db.execute(q, args).fetchall()]


def list_products(category=None, active_only=True):
    clauses, args = [], []
    if category:
        clauses.append('category=?'); args.append(category)
    if active_only:
        clauses.append('active=1 AND price IS NOT NULL AND price>0')
    q = 'SELECT * FROM products'
    if clauses:
        q += ' WHERE ' + ' AND '.join(clauses)
    q += ' ORDER BY category, name'
    with connect() as db:
        return db.execute(q, args).fetchall()


def get_product(product_id: int):
    with connect() as db:
        return db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()


def add_product(category, name, package_label, price, active=1):
    with connect() as db:
        cur = db.execute('INSERT INTO products(category,name,package_label,price,active,created_at) VALUES(?,?,?,?,?,?)',
                         (category, name, package_label, price, active, now_iso()))
        return cur.lastrowid


def update_product(product_id, **fields):
    allowed = {'category','name','package_label','price','active'}
    values = {k:v for k,v in fields.items() if k in allowed}
    if not values:
        return
    sets = ','.join(f'{k}=?' for k in values)
    with connect() as db:
        db.execute(f'UPDATE products SET {sets} WHERE id=?', (*values.values(), product_id))


def create_order(guest_tg_id, guest_name, phone, fulfillment, cafe, address, cart):
    total = sum(item['price'] * item['quantity'] for item in cart)
    stamp = now_iso()
    with connect() as db:
        cur = db.execute('''INSERT INTO orders(guest_tg_id,guest_name,phone,fulfillment,cafe,address,total,status,created_at,updated_at)
                            VALUES(?,?,?,?,?,?,?,'new',?,?)''',
                         (guest_tg_id, guest_name, phone, fulfillment, cafe, address, total, stamp, stamp))
        oid = cur.lastrowid
        for item in cart:
            db.execute('''INSERT INTO order_items(order_id,product_id,product_name,package_label,price,quantity)
                          VALUES(?,?,?,?,?,?)''', (oid, item['product_id'], item['name'], item['package_label'], item['price'], item['quantity']))
        return oid


def get_order(order_id):
    with connect() as db:
        order = db.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
        items = db.execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id', (order_id,)).fetchall()
        return order, items


def update_order(order_id, **fields):
    allowed = {'status','staff_name','work_chat_message_id'}
    values = {k:v for k,v in fields.items() if k in allowed}
    values['updated_at'] = now_iso()
    sets = ','.join(f'{k}=?' for k in values)
    with connect() as db:
        db.execute(f'UPDATE orders SET {sets} WHERE id=?', (*values.values(), order_id))
