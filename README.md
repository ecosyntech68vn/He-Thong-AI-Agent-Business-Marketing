# Cỗ Máy Nội Dung — Bot Bán Hàng Tự Động (Telegram + Sepay + Zalo + AI)

Bán bộ **Founder Solo** (ladder 3 tầng) tự động: **FounderToolkit ~~199k~~ 139k** · **Cỗ Máy Nội Dung ~~890k~~ 599k** · **Combo ~~999k~~ 699k ⭐**. Khách đặt → bot tạo VietQR → khách chuyển khoản → Sepay báo về → **bot tự gửi link sản phẩm**. Tin nhắn tự do được **AI tư vấn**; kết nối cả **Zalo OA** dùng chung AI.

Kiến trúc kế thừa nền tảng `bot-aithucchien` (Flask webhook + Sepay auto-giao + SQLite).

## Cấu trúc
```
comay-bot/
├── app.py            # Flask: /telegram-webhook, /sepay-webhook, /zalo-webhook, /
├── config.py         # đọc env + danh mục sản phẩm
├── db.py             # SQLite: đơn, link giao, GD lệch
├── ai_advisor.py     # AI tư vấn (LLM)
├── advisor_brain.md  # "bộ não" AI — sửa nội dung/giá ở đây
├── zalo.py           # Zalo OA (dùng chung AI)
├── requirements.txt · Procfile · .env.example · .gitignore
```

## A. Tạo repo GitHub MỚI & push
```bash
cd comay-bot
git init
git add .
git commit -m "Co May Noi Dung bot - Telegram + Sepay + Zalo + AI"
# Tạo repo PRIVATE tên "comay-bot" trên https://github.com/new (KHÔNG để public vì có code thanh toán)
git remote add origin https://github.com/<USERNAME>/comay-bot.git
git branch -M main
git push -u origin main
```
> File `.env` đã nằm trong `.gitignore` — token sẽ KHÔNG bị đẩy lên. Tuyệt đối không commit token.

## B. Chuẩn bị tài khoản
1. **Telegram bot:** @BotFather → `/newbot` → lấy `BOT_TOKEN`. (Đã lộ token cũ thì `/revoke`.)
2. **Chat ID admin:** chat với @userinfobot → lấy số → `ADMIN_CHAT_ID`.
3. **MB Bank + Sepay** (khuyến nghị MB vì biến động realtime): mở MB Bank → đăng ký Sepay → link bank → lấy `SEPAY_API_KEY`, trỏ webhook `{BASE_URL}/sepay-webhook` (Authentication: Apikey).
4. **Link sản phẩm:** tạo thư mục Google Drive chứa trọn bộ Cỗ Máy → "Anyone with link → Viewer" → lấy URL (set ở bước E).
5. **AI (tùy chọn):** OpenAI hoặc Groq (free) → `LLM_API_KEY` (+ base url/model).
6. **Zalo OA (tùy chọn):** tạo OA + app ở developers.zalo.me → `ZALO_OA_ACCESS_TOKEN` (token ~25h, cần refresh).

## C. Deploy Railway
1. railway.app → New Project → Deploy from GitHub → chọn `comay-bot` (tự nhận Python qua requirements.txt + Procfile).
2. Tab **Variables**: điền theo `.env.example` (BOT_TOKEN, ADMIN_CHAT_ID, SEPAY_API_KEY, BANK_*, LLM_*, ZALO_* …).
3. Settings → Domains → Generate Domain → copy vào `BASE_URL`.
4. Mở `{BASE_URL}/` phải thấy `{"status":"ok","service":"Co May Noi Dung Bot"}`.

## D. Nối webhook
- **Telegram:** mở `https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=<BASE_URL>/telegram-webhook&secret_token=<TELEGRAM_WEBHOOK_SECRET>`
- **Sepay:** dashboard → Webhook URL = `<BASE_URL>/sepay-webhook`, method POST, Apikey.
- **Zalo:** Zalo app → Webhook = `<BASE_URL>/zalo-webhook`.

## E. Set link giao hàng (chat admin với bot)
```
/set_link founder https://drive.google.com/drive/folders/<ID_FOUNDERTOOLKIT_199>
/set_link comay   https://drive.google.com/drive/folders/<ID_CO_MAY_TRON_BO>
/set_link combo   https://drive.google.com/drive/folders/<ID_COMBO_FOUNDER_SOLO>
```

## F. Lệnh
- Khách: `/start` · `/mua` (=`/mua_combo` 699k ⭐) · `/mua_comay` (599k) · `/mua_founder` (139k) · `/trang_thai` · `/lien_he` · nhắn tự do → AI tư vấn.
- Admin: `/set_link <sku> <url>` · `/confirm <TXN>` (giao thủ công) · `/unmatched` · `/stats` · `/admin_help`.

## G. Checklist Go-live
- ☐ `/start` trả menu · `/mua` ra QR + mã TXN
- ☐ Set link cả 2 SKU
- ☐ Test 1 CK thật nhỏ → bot báo underpaid (đúng) → rồi CK đủ → tự giao
- ☐ Nhận noti admin khi có đơn/giao
- ☐ Tắt `LLM_API_KEY` thử → bot vẫn chạy (offline-safe)

## Test logic không cần token
```
python app.py --selftest
```

## An toàn
- Token/key chỉ để trong env (Railway), KHÔNG commit. Repo **private**.
- AI không bịa số TK/giá; gặp khó → mời khách `/lien_he`.
- Sepay xác thực bằng Apikey; Telegram bằng secret_token; Zalo bằng chữ ký (bật `ZALO_STRICT=1`).
- `bot.db` chứa chat_id khách → coi như dữ liệu cá nhân.
