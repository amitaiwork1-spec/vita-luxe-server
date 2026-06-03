# -*- coding: utf-8 -*-
"""
Instagram automation for Vita Luxe.
Uses SDXL Lightning (free HuggingFace Space) to generate consistent character images.
"""
import os, json, logging, urllib.request, urllib.parse, random, sys, tempfile, time
from pathlib import Path

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

# ── Vita Luxe character base prompt ─────────────────────────────────────────
VITA_BASE = (
    "beautiful mixed ethnicity woman 25 years old, long dark wavy hair, "
    "tan skin, fit athletic body, luxury lifestyle, "
    "professional photography, 4K, realistic, instagram influencer"
)

PHOTO_THEMES = [
    f"{VITA_BASE}, gym workout, athletic outfit, mirror selfie, natural lighting",
    f"{VITA_BASE}, yoga on beach, golden hour, peaceful expression",
    f"{VITA_BASE}, luxury resort pool, swimwear, vacation lifestyle",
    f"{VITA_BASE}, morning coffee, luxury apartment, cozy morning routine",
    f"{VITA_BASE}, outdoor run, athletic wear, sunrise, motion",
    f"{VITA_BASE}, healthy meal prep, kitchen, colorful vegetables, clean eating",
    f"{VITA_BASE}, luxury hotel room, morning stretching, white sheets",
    f"{VITA_BASE}, outdoor cafe, sunglasses, relaxed fashion, city",
]

STORY_THEMES = [
    f"{VITA_BASE}, selfie, gym mirror, athletic wear, vertical portrait",
    f"{VITA_BASE}, smoothie bowl, healthy breakfast, close up, lifestyle",
    f"{VITA_BASE}, beach sunset, relaxed, vertical shot, travel",
    f"{VITA_BASE}, spa day, skincare routine, natural look, bathroom",
    f"{VITA_BASE}, night workout, gym lights, determined, vertical",
    f"{VITA_BASE}, casual outfit, city street, fashion, vertical portrait",
    f"{VITA_BASE}, meditation, rooftop, morning light, peaceful, vertical",
    f"{VITA_BASE}, luxury shopping, fashion bags, lifestyle, vertical",
]

CAPTIONS = [
    "Rise and shine. Make today count. 🌅",
    "Your body is your temple. Treat it like one. 💪",
    "Travel. Train. Thrive. Repeat. ✈️",
    "Living proof that consistency changes everything. 🔥",
    "Luxury is a mindset, not a price tag. 💎",
    "Strong women build each other up. Tag yours below. 👇",
    "This view though. Never taking it for granted. 🌍",
    "Wellness is not a destination. It's a daily choice. 🧘",
    "Every rep, every mile, every choice matters. ⚡",
    "She believed she could, so she did. 🌟",
]

HASHTAGS = (
    "#LuxuryFitness #WellnessLifestyle #FitTravel #HealthyLiving "
    "#MotivationMonday #GymLife #TravelGoals #WellnessInspo "
    "#ActiveLifestyle #FitnessJourney #LuxuryTravel #GlowUp "
    "#VitaLuxe #FitnessGirls #HealthyGirl"
)

SDXL_BASE = "https://ap123-sdxl-lightning.hf.space"


def _generate_vita_image(prompt: str) -> bytes:
    """Generate image via SDXL Lightning HuggingFace Space (free)."""
    session = "vita" + str(random.randint(100000, 999999))
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    # Step 1: Join the generation queue
    payload = json.dumps({
        "data": [prompt, "4-Step"],
        "event_data": None,
        "fn_index": 0,
        "trigger_id": 1,
        "session_hash": session,
    }).encode()

    req = urllib.request.Request(SDXL_BASE + "/queue/join",
                                 data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        join_resp = json.loads(r.read())
    logging.info(f"  Queue joined: {join_resp.get('event_id', '?')[:16]}...")

    # Step 2: Poll for result via SSE stream
    req2 = urllib.request.Request(
        SDXL_BASE + f"/queue/data?session_hash={session}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "text/event-stream"},
    )
    img_url = None
    with urllib.request.urlopen(req2, timeout=90) as r:
        buffer = b""
        while True:
            chunk = r.read(8192)
            if not chunk:
                break
            buffer += chunk
            # Parse SSE events
            for line in buffer.split(b"\n"):
                if line.startswith(b"data:"):
                    raw = line[5:].strip()
                    if raw and raw != b"[DONE]":
                        try:
                            event = json.loads(raw)
                            if event.get("msg") == "process_completed":
                                output = event.get("output", {}).get("data", [])
                                if output and isinstance(output[0], dict):
                                    img_url = output[0].get("url")
                        except Exception:
                            pass
            if img_url:
                break
            if len(buffer) > 500000:
                break

    if not img_url:
        raise RuntimeError("No image URL returned from SDXL Lightning")

    logging.info(f"  Image generated: {img_url[-40:]}")

    # Step 3: Download the image
    req3 = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req3, timeout=30) as r:
        img_bytes = r.read()

    if len(img_bytes) < 50000:
        raise RuntimeError(f"Image too small: {len(img_bytes)} bytes")

    return img_bytes


def _ig_login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]
    session_file = Path("ig_session.json")
    if session_file.exists():
        logging.info("Loading saved Instagram session...")
        cl.load_settings(session_file)
    else:
        logging.info("No session file, doing fresh login...")
    cl.login(IG_USERNAME, IG_PASSWORD)
    return cl


def _save_tmp(data: bytes, suffix=".jpg") -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


def post_photo_job():
    """Post a daily Vita Luxe photo to Instagram."""
    theme = random.choice(PHOTO_THEMES)
    logging.info(f"Generating Vita Luxe photo: {theme[:60]}...")
    img  = _generate_vita_image(theme)
    path = _save_tmp(img, suffix=".png")
    caption = random.choice(CAPTIONS) + "\n\n" + HASHTAGS
    logging.info(f"Image ready: {len(img)//1024}KB | Posting to Instagram...")
    cl    = _ig_login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted! ID: {media.pk}")
    os.unlink(path)


def post_story_job():
    """Post a Vita Luxe story to Instagram."""
    theme = random.choice(STORY_THEMES)
    logging.info(f"Generating Vita Luxe story: {theme[:60]}...")
    img  = _generate_vita_image(theme)
    path = _save_tmp(img, suffix=".png")
    logging.info(f"Story ready: {len(img)//1024}KB | Posting to Instagram...")
    cl    = _ig_login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted! ID: {media.pk}")
    os.unlink(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not IG_USERNAME or not IG_PASSWORD:
        logging.error("IG_USERNAME or IG_PASSWORD not set!")
        sys.exit(1)

    mode = sys.argv[1] if len(sys.argv) > 1 else "photo"
    logging.info(f"Mode: {mode} | IG: {IG_USERNAME[:5]}***")

    if mode == "photo":
        post_photo_job()
    elif mode == "story":
        post_story_job()
    else:
        logging.error(f"Unknown mode: {mode}")
        sys.exit(1)
