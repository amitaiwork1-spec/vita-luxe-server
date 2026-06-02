# -*- coding: utf-8 -*-
"""
Vita Luxe - 24/7 Server
Flask app that runs on Render.com:
  - Telegram webhook (bot always responds)
  - APScheduler (posts photos/reels/stories on schedule)
  - /ping endpoint (UptimeRobot keeps it alive)
"""
import os, json, time, logging, threading
from pathlib import Path
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BASE    = f"https://api.telegram.org/bot{TOKEN}"

# ─── Telegram helpers ───────────────────────────────────
import urllib.request

def tg(method, data):
    req = urllib.request.Request(
        f"{BASE}/{method}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        logging.error(f"TG error: {e}")
        return {}

def send(chat_id, text):
    tg("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

# ─── Bot logic ───────────────────────────────────────────
user_states = {}

GREETING = (
    "Hey gorgeous! I'm Vita Luxe - luxury fitness & travel creator!\n\n"
    "/photo - Custom photo just for you\n"
    "/shop  - My exclusive products\n"
    "/about - Learn more about me\n\n"
    "What can I do for you today?"
)

def handle(chat_id, text, user_name):
    state = user_states.get(chat_id, {})

    if text.startswith("/start"):
        user_states[chat_id] = {}
        send(chat_id, GREETING)

    elif text.startswith("/about"):
        send(chat_id,
            "I'm Vita Luxe - luxury wellness & travel influencer!\n"
            "Passionate about fitness, mindset, and living your best life.")

    elif text.startswith("/shop"):
        msg = (
            "My exclusive products:\n\n"
            "*Travel Fit 101 Guide* - $27\n"
            f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={os.environ.get('PAYPAL_EMAIL','')}&item_name=Travel+Fit+101&amount=27.00&currency_code=USD\n\n"
            "*30-Day Transformation* - $97\n"
            f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={os.environ.get('PAYPAL_EMAIL','')}&item_name=30-Day+Challenge&amount=97.00&currency_code=USD"
        )
        send(chat_id, msg)

    elif text.startswith("/photo"):
        user_states[chat_id] = {"state": "awaiting_request"}
        send(chat_id,
            "I'd love to create something special just for you!\n\n"
            "Tell me what you want - beach, gym, travel, sunset...\n"
            "I'll give you a custom price!")

    elif state.get("state") == "awaiting_request":
        price = _price(text)
        paypal_url = (
            f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick"
            f"&business={os.environ.get('PAYPAL_EMAIL','')}"
            f"&item_name=Custom+Photo&amount={price:.2f}&currency_code=USD"
        )
        send(chat_id,
            f"I'll create that beautiful photo just for you!\n\n"
            f"Price: *${price:.0f}*\n\n"
            f"Pay here:\n{paypal_url}\n\n"
            f"Send 'paid' after payment and I'll send your photo!")
        user_states[chat_id] = {"state": "awaiting_payment", "request": text, "price": price}

    elif state.get("state") == "awaiting_payment":
        if any(w in text.lower() for w in ["paid", "done", "payment", "sent"]):
            send(chat_id, "Generating your exclusive photo... one moment!")
            threading.Thread(target=_gen_and_send, args=(chat_id, state.get("request",""))).start()
            user_states[chat_id] = {}
        else:
            send(chat_id, "Complete payment first, then send 'paid'! Or /photo to start over.")

    else:
        replies = [
            "Love hearing from you! Follow me on Instagram for daily inspiration!",
            "Hey! You're amazing - keep shining every day!",
            "Thanks for reaching out! Check my Instagram for exclusive content!",
        ]
        import random
        send(chat_id, random.choice(replies))


def _price(text):
    t = text.lower()
    if any(w in t for w in ["series","pack","5 photo","collection"]): return 35.0
    if any(w in t for w in ["exclusive","private","only for me"]):     return 50.0
    if any(w in t for w in ["personalized","my name","dedicated"]):    return 25.0
    if any(w in t for w in ["luxury","vip","premium"]):                return 20.0
    if any(w in t for w in ["travel","resort","hotel"]):               return 15.0
    if any(w in t for w in ["gym","workout","fitness"]):               return 10.0
    if any(w in t for w in ["beach","sunset","outdoor"]):              return 10.0
    return 5.0


def _gen_and_send(chat_id, request_text):
    """Generate image and send via Telegram."""
    try:
        import urllib.parse, tempfile, os
        prompt = (
            f"beautiful mixed ethnicity female influencer age 25, "
            f"long wavy dark brown hair, {request_text}, "
            f"professional photography, cinematic lighting, 4K, Instagram style"
        )
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&seed=42&nologo=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as res:
            img_bytes = res.read()

        # Send photo via Telegram multipart
        boundary = "----Boundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="caption"\r\n\r\n'
            f"Your exclusive photo is ready! Stay gorgeous!\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="photo"; filename="photo.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()

        req2 = urllib.request.Request(
            f"{BASE}/sendPhoto", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        urllib.request.urlopen(req2, timeout=30)
        logging.info(f"Photo sent to {chat_id}")
    except Exception as e:
        logging.error(f"Photo gen error: {e}")
        send(chat_id, "Your exclusive photo will be delivered shortly!")


# ─── Webhook endpoint ────────────────────────────────────
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    msg = update.get("message", {})
    if msg:
        chat_id   = msg["chat"]["id"]
        text      = msg.get("text", "")
        user_name = msg.get("from", {}).get("first_name", "")
        if text:
            threading.Thread(target=handle, args=(chat_id, text, user_name)).start()
    return jsonify({"ok": True})

@app.route("/ping")
def ping():
    return jsonify({"status": "alive", "bot": "Vita Luxe"})

@app.route("/")
def index():
    return jsonify({"name": "Vita Luxe Bot", "status": "running"})


# ─── Scheduler jobs ──────────────────────────────────────
def post_daily_photo():
    logging.info("[Scheduler] Daily photo job")
    try:
        from instagram_auto import post_photo_job
        post_photo_job()
    except Exception as e:
        logging.error(f"Photo job error: {e}")

def post_story_job(story_index):
    logging.info(f"[Scheduler] Story {story_index+1}/12")
    try:
        from instagram_auto import post_story_job as do_story
        do_story(story_index)
    except Exception as e:
        logging.error(f"Story job error: {e}")

def start_scheduler():
    sched = BackgroundScheduler(timezone="Asia/Jerusalem")

    # Daily photo at 09:00 Israel time
    sched.add_job(post_daily_photo, "cron", hour=9, minute=0)

    # 12 stories throughout the day
    story_times = [
        (8,0),(8,55),(9,50),(10,45),(11,40),
        (12,35),(13,30),(14,25),(15,20),(16,15),(17,10),(18,5)
    ]
    for i, (h, m) in enumerate(story_times):
        sched.add_job(post_story_job, "cron", hour=h, minute=m,
                      kwargs={"story_index": i})

    sched.start()
    logging.info(f"Scheduler started with {len(sched.get_jobs())} jobs")


# ─── Startup ─────────────────────────────────────────────
def setup_webhook():
    """Register webhook with Telegram."""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if render_url:
        webhook_url = f"{render_url}/webhook/{TOKEN}"
        result = tg("setWebhook", {"url": webhook_url, "drop_pending_updates": True})
        logging.info(f"Webhook set: {webhook_url} → {result.get('ok')}")

if __name__ == "__main__":
    setup_webhook()
    start_scheduler()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
