# -*- coding: utf-8 -*-
"""SQLite: đơn hàng + link giao + log giao dịch không khớp."""
import sqlite3, time, pathlib

DB = pathlib.Path(__file__).parent / "bot.db"

def _c():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    with _c() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS orders(
            txn TEXT PRIMARY KEY, chat_id TEXT, sku TEXT, amount INTEGER,
            status TEXT, created TEXT, channel TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS links(sku TEXT PRIMARY KEY, url TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS unmatched(
            id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, amount INTEGER, created TEXT)""")

def create_order(txn, chat_id, sku, amount, channel="telegram"):
    with _c() as c:
        c.execute("INSERT OR REPLACE INTO orders VALUES(?,?,?,?,?,?,?)",
                  (txn, str(chat_id), sku, amount, "pending", time.strftime("%Y-%m-%d %H:%M"), channel))

def get_order(txn):
    with _c() as c:
        r = c.execute("SELECT * FROM orders WHERE txn=?", (txn,)).fetchone()
        return dict(r) if r else None

def mark_paid(txn):
    with _c() as c:
        c.execute("UPDATE orders SET status='paid' WHERE txn=?", (txn,))

def orders_by_chat(chat_id):
    with _c() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM orders WHERE chat_id=? ORDER BY created DESC LIMIT 10", (str(chat_id),)).fetchall()]

def set_link(sku, url):
    with _c() as c:
        c.execute("INSERT OR REPLACE INTO links VALUES(?,?)", (sku, url))

def get_link(sku):
    with _c() as c:
        r = c.execute("SELECT url FROM links WHERE sku=?", (sku,)).fetchone()
        return r["url"] if r else None

def log_unmatched(content, amount):
    with _c() as c:
        c.execute("INSERT INTO unmatched(content,amount,created) VALUES(?,?,?)",
                  (content, amount, time.strftime("%Y-%m-%d %H:%M")))

def list_unmatched(n=10):
    with _c() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM unmatched ORDER BY id DESC LIMIT ?", (n,)).fetchall()]

def stats():
    with _c() as c:
        r = c.execute("SELECT COUNT(*) n, COALESCE(SUM(amount),0) rev FROM orders WHERE status='paid'").fetchone()
        return {"orders": r["n"], "revenue": r["rev"]}
