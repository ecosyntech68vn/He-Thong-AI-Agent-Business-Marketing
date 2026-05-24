# -*- coding: utf-8 -*-
"""Cấu hình đọc từ biến môi trường (env). KHÔNG hardcode token."""
import os

def _env(k, d=""):
    return os.environ.get(k, d)

BOT_TOKEN               = _env("BOT_TOKEN")
ADMIN_CHAT_ID           = _env("ADMIN_CHAT_ID")
TELEGRAM_WEBHOOK_SECRET = _env("TELEGRAM_WEBHOOK_SECRET")
SEPAY_API_KEY           = _env("SEPAY_API_KEY")          # để trống = chế độ MANUAL (admin /confirm)
BASE_URL                = _env("BASE_URL")

# Ngân hàng nhận tiền (khuyến nghị MB Bank vì Sepay đẩy biến động realtime)
BANK_ACCOUNT = _env("BANK_ACCOUNT")
BANK_NAME    = _env("BANK_NAME", "MB Bank")
BANK_CODE    = _env("BANK_CODE", "MB")     # mã ngân hàng cho VietQR (MB, VCB, TCB, ACB...)
ACCOUNT_NAME = _env("ACCOUNT_NAME", "")

# Sản phẩm bán (thêm SKU mới chỉ cần thêm 1 dòng)
PRODUCTS = {
    "comay":    {"name": "Cỗ Máy Nội Dung (trọn bộ)", "price": 690000},
    "tripwire": {"name": "Bộ Tăng Tốc — Calendar + 50 prompt", "price": 199000},
}
DEFAULT_SKU = "comay"

# AI (tùy chọn). Để trống LLM_API_KEY -> bot vẫn chạy, chỉ chưa có AI tư vấn.
LLM_API_KEY  = _env("LLM_API_KEY")
LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL    = _env("LLM_MODEL", "gpt-4o-mini")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
