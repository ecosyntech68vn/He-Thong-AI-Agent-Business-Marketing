# -*- coding: utf-8 -*-
"""Zalo OA — dùng CHUNG bộ não AI với Telegram (ai_advisor). Đăng ký blueprint trong app.py."""
import os, hashlib
try:
    import requests
except ImportError:
    requests = None
from flask import Blueprint, request, jsonify
from ai_advisor import ai_reply

ZALO_TOKEN  = os.environ.get("ZALO_OA_ACCESS_TOKEN", "")
ZALO_SECRET = os.environ.get("ZALO_APP_SECRET", "")
ZALO_STRICT = os.environ.get("ZALO_STRICT", "0") == "1"
SEND_URL    = "https://openapi.zalo.me/v3.0/oa/message"

zalo_bp = Blueprint("zalo", __name__)

def zalo_send(user_id, text):
    if not ZALO_TOKEN or requests is None:
        print("zalo_send: thiếu ZALO_OA_ACCESS_TOKEN"); return
    try:
        requests.post(SEND_URL, headers={"access_token": ZALO_TOKEN, "Content-Type": "application/json"},
                      json={"recipient": {"user_id": user_id}, "message": {"text": text[:2000]}}, timeout=20)
    except Exception as e:
        print("zalo_send error:", e)

def _verify(req):
    if not ZALO_SECRET:
        return True
    sig = req.headers.get("X-ZEvent-Signature", "")
    body = req.get_data(as_text=True) or ""
    ts = ""
    try: ts = (req.get_json(silent=True) or {}).get("timestamp", "")
    except Exception: pass
    mac = "mac=" + hashlib.sha256((os.environ.get("ZALO_APP_ID", "") + body + str(ts) + ZALO_SECRET).encode()).hexdigest()
    ok = sig == mac
    if not ok:
        print("zalo: sai chữ ký", "-> CHẶN" if ZALO_STRICT else "-> vẫn nhận")
    return ok or (not ZALO_STRICT)

@zalo_bp.route("/zalo-webhook", methods=["GET"])
def zalo_verify():
    return jsonify({"status": "ok", "service": "Zalo OA + Co May Noi Dung"}), 200

@zalo_bp.route("/zalo-webhook", methods=["POST"])
def zalo_webhook():
    if not _verify(request):
        return jsonify({"ok": True}), 200
    d = request.get_json(silent=True) or {}
    sender = (d.get("sender") or {}).get("id")
    if d.get("event_name") in ("user_send_text", "user_submit_info") and sender:
        text = ((d.get("message") or {}).get("text") or "").strip()
        if text:
            reply = ai_reply("zalo_" + str(sender), text) or \
                ("Dạ em là trợ lý Cỗ Máy Nội Dung 👋 Anh/chị bán khóa học/dịch vụ gì ạ? Em tư vấn nhanh nhé!")
            zalo_send(sender, reply)
    return jsonify({"ok": True}), 200
