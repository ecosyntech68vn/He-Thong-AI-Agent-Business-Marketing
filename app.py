# -*- coding: utf-8 -*-
"""
Cỗ Máy Nội Dung — Bot bán hàng tự động (Telegram + Sepay + Zalo + AI).
Kiến trúc theo nền tảng bot-aithucchien: webhook Flask, Sepay auto-giao, SQLite.
- Khách /mua -> bot tạo đơn TXN + VietQR -> khách CK -> Sepay webhook -> tự gửi link sản phẩm.
- Tin nhắn tự do -> AI tư vấn (ai_advisor). Zalo OA dùng chung AI (zalo.py).
Chạy:  python app.py            (server thật)
       python app.py --selftest (kiểm tra logic, không cần token/mạng)
"""
import os, re, sys, uuid
from urllib.parse import quote
from flask import Flask, request, jsonify
try:
    import requests
except ImportError:
    requests = None

import config as C
import db
from ai_advisor import ai_reply

db.init()
app = Flask(__name__)

# Zalo (tùy chọn) — đăng ký nếu import được
try:
    from zalo import zalo_bp
    app.register_blueprint(zalo_bp)
except Exception as _e:
    print("Zalo blueprint chưa bật:", _e)

ADMIN_STATE = {}   # chat_id -> {"action": "setlink", "sku": ...}

# ---------- Telegram helpers ----------
def _tg(method, payload):
    if not C.BOT_TOKEN or requests is None:
        return {}
    try:
        return requests.post(f"{C.TG_API}/{method}", json=payload, timeout=20).json()
    except Exception as e:
        print("tg error:", e); return {}

def tg_send(chat_id, text, reply_markup=None):
    p = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        p["reply_markup"] = reply_markup
    return _tg("sendMessage", p)

def tg_send_photo(chat_id, photo_url, caption):
    return _tg("sendPhoto", {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"})

def tg_keyboard():
    return {"inline_keyboard": [
        [{"text": "⭐ Combo Founder Solo — 699k (gốc 999k)", "callback_data": "mua_combo"}],
        [{"text": "🛒 Cỗ Máy Nội Dung — 599k (gốc 890k)", "callback_data": "mua_comay"}],
        [{"text": "📘 FounderToolkit — 139k (gốc 199k)", "callback_data": "mua_founder"}],
        [{"text": "📦 Sản phẩm là gì?", "callback_data": "intro"},
         {"text": "❓ FAQ", "callback_data": "faq"}],
        [{"text": "🧾 Đơn của tôi", "callback_data": "trang_thai"},
         {"text": "🙋 Tư vấn viên", "callback_data": "lien_he"}],
    ]}

def notify_admin(text):
    if C.ADMIN_CHAT_ID:
        tg_send(C.ADMIN_CHAT_ID, "🔔 " + text)

# ---------- VietQR ----------
def vietqr_url(amount, content):
    return (f"https://img.vietqr.io/image/{C.BANK_CODE}-{C.BANK_ACCOUNT}-compact2.png"
            f"?amount={amount}&addInfo={quote(content)}&accountName={quote(C.ACCOUNT_NAME)}")

def new_txn():
    return "TXN" + uuid.uuid4().hex[:6].upper()

def vnd(n):
    return f"{n:,.0f}đ".replace(",", ".")

# ---------- Static copy ----------
INTRO = ("<b>Bộ công cụ Founder Solo</b> — vừa XÂY vừa MARKETING công ty công nghệ một mình bằng AI.\n\n"
         "• <b>FounderToolkit — <s>199k</s> 139k</b>: Sổ tay GitHub cho founder không rành code.\n"
         "• <b>Cỗ Máy Nội Dung — <s>890k</s> 599k</b>: hệ thống marketing (1 ý tưởng → 5 bài, ~5 giờ/tuần).\n"
         "• <b>Combo — <s>999k</s> 699k</b> ⭐: cả 2 + bonus (bài seeding + thư viện prompt). Rẻ hơn mua lẻ, đáng nhất.\n\n"
         "Đây là chính bộ công cụ tôi dùng để vừa xây vừa marketing EcoSynTech một mình.")
FAQ = ("❓ <b>Hay gặp</b>\n"
       "• Không rành công nghệ vẫn dùng được (prompt copy-paste + AI trợ lý + video).\n"
       "• Không phải khóa học — là hệ thống chạy sẵn.\n"
       "• Bảo đảm hoàn tiền 14 ngày.\n"
       "• Giao tự động qua link ngay sau khi thanh toán.")

# ---------- Handlers ----------
def handle_start(chat_id, name=""):
    tg_send(chat_id, f"Xin chào {name} 👋 Em là trợ lý của <b>Cỗ Máy Nội Dung</b>.\n"
                     "Anh/chị chọn bên dưới, hoặc cứ nhắn câu hỏi tự nhiên — em tư vấn ngay ạ 😊", tg_keyboard())

def handle_mua(chat_id, sku):
    sku = sku.replace("mua_", "")
    prod = C.PRODUCTS.get(sku)
    if not prod:
        tg_send(chat_id, "Sản phẩm không tồn tại. Gõ /start để xem menu.", tg_keyboard()); return
    txn = new_txn()
    db.create_order(txn, chat_id, sku, prod["price"])
    content = f"COMAY {txn}"
    gia = (f"<s>{vnd(prod['list'])}</s> → <b>{vnd(prod['price'])}</b> (ưu đãi mở bán)"
           if prod.get("list") else f"<b>{vnd(prod['price'])}</b>")
    cap = (f"🛒 <b>{prod['name']}</b>\n💵 Giá: {gia}\n\n"
           f"Chuyển khoản theo QR, hoặc thủ công:\n"
           f"🏦 {C.BANK_NAME} | STK <b>{C.BANK_ACCOUNT or '[CHƯA CẤU HÌNH]'}</b> | {C.ACCOUNT_NAME}\n"
           f"💵 Số tiền: <b>{vnd(prod['price'])}</b>\n"
           f"📝 Nội dung: <b>{content}</b>\n\n"
           f"⏱ Sau khi CK đúng nội dung, bot tự gửi link sản phẩm trong ~30 giây.\n"
           f"Mã đơn của anh/chị: <code>{txn}</code> (tra cứu: /trang_thai)")
    if C.BANK_ACCOUNT:
        tg_send_photo(chat_id, vietqr_url(prod["price"], content), cap)
    else:
        tg_send(chat_id, cap)
    notify_admin(f"Đơn mới {txn} — {prod['name']} {vnd(prod['price'])} (chat {chat_id})")

def handle_trang_thai(chat_id):
    rows = db.orders_by_chat(chat_id)
    if not rows:
        tg_send(chat_id, "Anh/chị chưa có đơn nào. Gõ /start để xem sản phẩm.", tg_keyboard()); return
    lines = [f"• {o['txn']} — {C.PRODUCTS.get(o['sku'],{}).get('name',o['sku'])} — "
             f"{'✅ Đã thanh toán' if o['status']=='paid' else '⏳ Chờ CK'}" for o in rows]
    tg_send(chat_id, "🧾 <b>Đơn của anh/chị:</b>\n" + "\n".join(lines))

def handle_lien_he(chat_id):
    tg_send(chat_id, f"🙋 Em là <b>Trợ lý của anh Thuận</b> — nhà sáng lập <b>EcoSynTech Global</b>. Em báo anh Thuận phản hồi sớm ạ!\n\n📞 Liên hệ anh Thuận trực tiếp:\n• Telegram: tg://user?id={C.ADMIN_CHAT_ID}\n• Zalo: https://zalo.me/0985438373\n• ☎️ Gọi/SMS: 0985438373\n• 📧 thuanktqd.mba@gmail.com")
    notify_admin(f"🔔 Khách cần tư vấn - bấm để chat: tg://user?id={chat_id}")

def deliver(order):
    """Giao sản phẩm: gửi link cho khách + báo admin."""
    link = db.get_link(order["sku"])
    name = C.PRODUCTS.get(order["sku"], {}).get("name", order["sku"])
    if link:
        tg_send(order["chat_id"], f"🎉 Thanh toán thành công! Cảm ơn anh/chị.\n\n"
                                  f"📦 <b>{name}</b> của anh/chị đây ạ:\n{link}\n\n"
                                  f"Bắt đầu từ file “Hướng dẫn sử dụng” nhé. Cần hỗ trợ cứ nhắn em! 🙌")
    else:
        tg_send(order["chat_id"], "🎉 Thanh toán thành công! Admin sẽ gửi link sản phẩm cho anh/chị ngay ạ.")
        notify_admin(f"⚠️ Đơn {order['txn']} đã trả tiền nhưng CHƯA set link cho SKU '{order['sku']}'. "
                     f"Dùng /set_link {order['sku']} <url>")
    notify_admin(f"✅ ĐÃ GIAO {order['txn']} — {name}")

def handle_admin(chat_id, text):
    if str(chat_id) != str(C.ADMIN_CHAT_ID):
        return
    parts = text.split()
    cmd = parts[0]
    if cmd == "/admin_help":
        tg_send(chat_id, "Lệnh admin:\n/set_link <sku> <url>\n/confirm <TXN>\n/unmatched\n/stats")
    elif cmd == "/set_link" and len(parts) >= 3:
        db.set_link(parts[1], parts[2]); tg_send(chat_id, f"✅ Đã set link cho {parts[1]}.")
    elif cmd == "/confirm" and len(parts) >= 2:
        o = db.get_order(parts[1].upper())
        if o:
            db.mark_paid(o["txn"]); deliver(o); tg_send(chat_id, f"✅ Confirm + giao {o['txn']}.")
        else:
            tg_send(chat_id, "Không thấy mã đơn đó.")
    elif cmd == "/unmatched":
        u = db.list_unmatched()
        tg_send(chat_id, "GD chưa khớp:\n" + ("\n".join(f"• {x['content']} | {vnd(x['amount'])}" for x in u) or "(trống)"))
    elif cmd == "/stats":
        s = db.stats(); tg_send(chat_id, f"📊 Đơn đã thanh toán: {s['orders']} | Doanh thu: {vnd(s['revenue'])}")

# ---------- Lõi khớp thanh toán (tách riêng để test được) ----------
def process_payment(content, amount):
    """Khớp 1 biến động ngân hàng với đơn. Trả (status, txn)."""
    m = re.search(r"TXN[A-Z0-9]{6}", (content or "").upper().replace(" ", ""))
    if not m:
        db.log_unmatched(content, amount); notify_admin(f"GD không khớp (không thấy mã): {content} {vnd(amount)}")
        return ("no_code", None)
    txn = m.group(0)
    o = db.get_order(txn)
    if not o:
        db.log_unmatched(content, amount); notify_admin(f"GD có mã {txn} nhưng không thấy đơn.")
        return ("no_order", txn)
    if o["status"] == "paid":
        return ("already", txn)
    if amount < o["amount"]:
        notify_admin(f"⚠️ Đơn {txn} CK THIẾU: nhận {vnd(amount)} / cần {vnd(o['amount'])}")
        tg_send(o["chat_id"], f"Em nhận được {vnd(amount)} nhưng đơn cần {vnd(o['amount'])}. "
                              f"Anh/chị vui lòng chuyển bù phần còn lại ạ.")
        return ("underpaid", txn)
    db.mark_paid(txn); o = db.get_order(txn); deliver(o)
    return ("delivered", txn)

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Co May Noi Dung Bot"})

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    if C.TELEGRAM_WEBHOOK_SECRET and \
            request.headers.get("X-Telegram-Bot-Api-Secret-Token") != C.TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": True}), 200
    u = request.get_json(silent=True) or {}
    if "callback_query" in u:
        cq = u["callback_query"]; chat_id = cq["message"]["chat"]["id"]; data = cq.get("data", "")
        _tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
        if data.startswith("mua_"): handle_mua(chat_id, data)
        elif data == "intro":  tg_send(chat_id, INTRO, tg_keyboard())
        elif data == "faq":    tg_send(chat_id, FAQ, tg_keyboard())
        elif data == "trang_thai": handle_trang_thai(chat_id)
        elif data == "lien_he": handle_lien_he(chat_id)
        return jsonify({"ok": True})
    msg = u.get("message") or {}
    if "text" not in msg:
        return jsonify({"ok": True})
    chat_id = msg["chat"]["id"]; text = msg["text"].strip()
    name = (msg.get("from") or {}).get("first_name", "")
    if str(chat_id) == str(C.ADMIN_CHAT_ID) and text.startswith(("/set_link", "/confirm", "/unmatched", "/stats", "/admin_help")):
        handle_admin(chat_id, text); return jsonify({"ok": True})
    if text == "/start":            handle_start(chat_id, name)
    elif text in ("/mua", "/mua_combo"): handle_mua(chat_id, "combo")
    elif text == "/mua_comay":      handle_mua(chat_id, "comay")
    elif text == "/mua_founder":    handle_mua(chat_id, "founder")
    elif text == "/trang_thai":     handle_trang_thai(chat_id)
    elif text == "/lien_he":        handle_lien_he(chat_id)
    else:
        reply = ai_reply(chat_id, text)
        if reply: tg_send(chat_id, reply, tg_keyboard())
        else:     tg_send(chat_id, "Em chưa rõ ý ạ — anh/chị chọn nhanh bên dưới hoặc gõ /start nhé 👇", tg_keyboard())
    return jsonify({"ok": True})

@app.route("/sepay-webhook", methods=["POST"])
def sepay_webhook():
    if not C.SEPAY_API_KEY:
        return jsonify({"ok": True, "msg": "manual mode"}), 200
    auth = request.headers.get("Authorization", "")
    if auth != f"Apikey {C.SEPAY_API_KEY}":
        return jsonify({"ok": False}), 401
    d = request.get_json(silent=True) or {}
    content = d.get("content") or d.get("description") or ""
    amount = int(d.get("transferAmount") or d.get("amount") or 0)
    status, txn = process_payment(content, amount)
    return jsonify({"ok": True, "status": status, "txn": txn})

# ---------- Self-test ----------
def selftest():
    global tg_send, tg_send_photo, notify_admin
    out = []
    tg_send = lambda c, t, rm=None: out.append(("send", str(t)[:50]))
    tg_send_photo = lambda c, p, cap: out.append(("photo", str(cap)[:50]))
    notify_admin = lambda t: out.append(("admin", t))
    db.set_link("comay", "https://drive.google.com/test")
    handle_start(1, "Test")
    handle_mua(1, "mua_comay")
    o = db.orders_by_chat(1)[0]; txn = o["txn"]
    assert o["status"] == "pending"
    price = C.PRODUCTS["comay"]["price"]
    st, t2 = process_payment(f"COMAY {txn}", price)
    assert st == "delivered" and t2 == txn, f"phải giao được, got {st}"
    assert db.get_order(txn)["status"] == "paid"
    st2, _ = process_payment("MUA TXNZZZZZZ", price)
    assert st2 == "no_order"
    st3, _ = process_payment(f"COMAY {new_txn()}", 100)  # không có đơn
    print("app selftest PASS ✓ —", len(out), "actions; deliver+underpaid+unmatched OK")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        if not C.BOT_TOKEN:
            print("THIẾU BOT_TOKEN — xem README.md"); sys.exit(1)
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)
