# -*- coding: utf-8 -*-
"""AI tư vấn — trả lời tin nhắn tự do, hướng khách tới /mua. Trả None nếu chưa bật AI/lỗi."""
import os, pathlib
try:
    import requests
except ImportError:
    requests = None

BASE      = pathlib.Path(__file__).parent
LLM_KEY   = os.environ.get("LLM_API_KEY", "")
LLM_URL   = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
MAXH      = 10

def _brain():
    f = BASE / "advisor_brain.md"
    return f.read_text(encoding="utf-8") if f.exists() else \
        "Bạn là trợ lý tư vấn thân thiện. Hướng khách gõ /start để xem menu và /mua để mua."

BRAIN, HISTORY = _brain(), {}

def _remember(cid, role, content):
    h = HISTORY.setdefault(cid, []); h.append({"role": role, "content": content}); del h[:-MAXH]

def ai_reply(chat_id, user_text):
    if not LLM_KEY or requests is None or not (user_text or "").strip():
        return None
    _remember(chat_id, "user", user_text)
    msgs = [{"role": "system", "content": BRAIN}] + HISTORY.get(chat_id, [])
    try:
        r = requests.post(f"{LLM_URL}/chat/completions",
                          headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"},
                          json={"model": LLM_MODEL, "messages": msgs, "temperature": 0.5, "max_tokens": 500},
                          timeout=30)
        reply = r.json()["choices"][0]["message"]["content"].strip()
        _remember(chat_id, "assistant", reply)
        return reply or None
    except Exception as e:
        print("ai_advisor error:", e); return None

if __name__ == "__main__":
    assert len(BRAIN) > 20
    globals()["LLM_KEY"] = ""
    assert ai_reply(1, "tư vấn giúp em") is None
    print("ai_advisor selftest PASS ✓ (brain", len(BRAIN), "ký tự)")
