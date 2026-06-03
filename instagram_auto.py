# -*- coding: utf-8 -*-
"""
Instagram automation for Vita Luxe.
Consistent character: dark wavy hair, mixed ethnicity, 25yo, luxury fitness.
"""
import os, json, logging, urllib.request, random, sys, tempfile, time, subprocess
from pathlib import Path

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

# ── Vita Luxe - ultra realistic photography prompts ──────────────────────────
VITA_BASE = (
    "RAW photograph, DSLR, 25 year old woman, long wavy dark brown hair, "
    "natural olive skin with pores, athletic toned body, "
    "Sony A7 85mm f/1.4, shallow depth of field, film grain, "
    "candid natural expression, hyperrealistic, no filter"
)

PHOTO_THEMES = [
    f"{VITA_BASE}, beach golden hour, beige sports bra, looking over shoulder, warm backlight",
    f"{VITA_BASE}, gym mirror selfie, black athletic outfit, natural gym lighting, candid",
    f"{VITA_BASE}, luxury rooftop pool sunset, relaxed pose, summer lifestyle, cinematic",
    f"{VITA_BASE}, morning outdoor yoga, white sports set, soft sunrise light, peaceful",
    f"{VITA_BASE}, luxury hotel balcony, white linen, morning coffee, natural window light",
    f"{VITA_BASE}, outdoor run in park, ponytail, athletic wear, motion blur background",
    f"{VITA_BASE}, beach at sunset, sitting on sand, casual look, golden warm tones",
]

STORY_THEMES = [
    f"{VITA_BASE}, close face selfie, gym background, natural light, vertical portrait",
    f"{VITA_BASE}, beach candid shot, golden hour, vertical, slight smile, hair in wind",
    f"{VITA_BASE}, mirror gym selfie, sports bra leggings, vertical, phone in frame",
    f"{VITA_BASE}, poolside luxury resort, sunglasses, summer, vertical lifestyle",
    f"{VITA_BASE}, morning coffee window, natural beauty, cozy, vertical portrait",
    f"{VITA_BASE}, outdoor city walk, casual fashion, vertical, candid street photo",
    f"{VITA_BASE}, spa day, face mask, bathroom mirror, natural no makeup look, vertical",
]

REEL_THEMES = [
    f"{VITA_BASE}, dynamic fitness pose, gym, dramatic natural light",
    f"{VITA_BASE}, beach sunrise walk, athletic wear, natural movement",
    f"{VITA_BASE}, luxury rooftop, fashion editorial, confident look",
    f"{VITA_BASE}, outdoor workout park, energetic, motion",
    f"{VITA_BASE}, poolside summer, relaxed glamour, lifestyle",
]

CAPTIONS = [
    "Rise and grind. 💪 Every rep counts.\n\n" ,
    "Golden hour energy only. ✨\n\n",
    "Luxury is a lifestyle, not a price tag. 💎\n\n",
    "She trained. She glowed. She conquered. 🔥\n\n",
    "Your body. Your rules. Your results. 👑\n\n",
]

HASHTAGS = (
    "#VitaLuxe #LuxuryFitness #FitnessGirl #WellnessLifestyle "
    "#FitBody #GymLife #HealthyLiving #FitnessMotivation "
    "#BodyGoals #FitnessCommunity #ActiveLifestyle #GlowUp"
)

SDXL_BASE = "https://ap123-sdxl-lightning.hf.space"


def _generate_vita_image(prompt: str) -> bytes:
    """Generate Vita Luxe image via SDXL Lightning (free, no API key)."""
    session = "vita" + str(random.randint(100000, 999999))
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

    payload = json.dumps({
        "data": [prompt, "8-Step"],
        "event_data": None,
        "fn_index": 0,
        "trigger_id": 1,
        "session_hash": session,
    }).encode()

    req = urllib.request.Request(SDXL_BASE + "/queue/join",
                                 data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        json.loads(r.read())

    req2 = urllib.request.Request(
        SDXL_BASE + f"/queue/data?session_hash={session}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "text/event-stream"},
    )
    img_url = None
    with urllib.request.urlopen(req2, timeout=90) as r:
        buffer = b""
        while True:
            chunk = r.read(8192)
            if not chunk: break
            buffer += chunk
            for line in buffer.split(b"\n"):
                if line.startswith(b"data:"):
                    raw = line[5:].strip()
                    if raw and raw != b"[DONE]":
                        try:
                            event = json.loads(raw)
                            if event.get("msg") == "process_completed":
                                out = event.get("output", {}).get("data", [])
                                if out and isinstance(out[0], dict):
                                    img_url = out[0].get("url")
                        except Exception:
                            pass
            if img_url or len(buffer) > 500000:
                break

    if not img_url:
        raise RuntimeError("No image URL from SDXL Lightning")

    req3 = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req3, timeout=30) as r:
        img_bytes = r.read()

    if len(img_bytes) < 50000:
        raise RuntimeError(f"Image too small: {len(img_bytes)} bytes")

    logging.info(f"  Image generated: {len(img_bytes)//1024}KB")
    return img_bytes


def _make_reel_video(img_bytes: bytes) -> str:
    """Create a 15-second reel video from image with Ken Burns zoom effect."""
    try:
        from moviepy.editor import ImageClip, CompositeVideoClip
        import numpy as np
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.resize((1080, 1920), Image.LANCZOS)

        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(tmp_img.name, "JPEG", quality=95)
        tmp_img.close()

        clip = ImageClip(tmp_img.name, duration=15)

        def zoom(t):
            scale = 1 + 0.05 * (t / 15)
            return scale

        zoomed = clip.resize(zoom)
        zoomed = zoomed.set_position("center")

        final = CompositeVideoClip([zoomed], size=(1080, 1920))
        final = final.set_duration(15)

        out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        final.write_videofile(out.name, fps=30, codec="libx264",
                               audio=False, logger=None, preset="ultrafast")
        os.unlink(tmp_img.name)
        return out.name

    except ImportError:
        # Fallback: ffmpeg direct approach
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.resize((1080, 1920), Image.LANCZOS)
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(tmp_img.name, "JPEG", quality=95)
        tmp_img.close()
        out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        subprocess.run([
            "ffmpeg", "-loop", "1", "-i", tmp_img.name,
            "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=450:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
            "-t", "15", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-y", out.name
        ], capture_output=True)
        os.unlink(tmp_img.name)
        return out.name


def _ig_login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]
    session_file = Path("ig_session.json")
    if session_file.exists():
        logging.info("Loading saved Instagram session...")
        cl.load_settings(session_file)
    cl.login(IG_USERNAME, IG_PASSWORD)
    return cl


def _save_tmp(data: bytes, suffix=".png") -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


def delete_recent_stories():
    """Delete all current stories."""
    cl = _ig_login()
    try:
        user_id = cl.user_id_from_username(IG_USERNAME.split("@")[0]) if "@" in IG_USERNAME else cl.user_id
        stories = cl.user_stories(user_id)
        logging.info(f"Found {len(stories)} stories to delete")
        for story in stories:
            cl.story_delete(story.pk)
            logging.info(f"  Deleted story {story.pk}")
            time.sleep(1)
    except Exception as e:
        logging.warning(f"Could not delete stories: {e}")


def post_photo_job():
    theme = random.choice(PHOTO_THEMES)
    logging.info(f"Generating Vita Luxe photo...")
    img  = _generate_vita_image(theme)
    path = _save_tmp(img)
    caption = random.choice(CAPTIONS) + HASHTAGS
    cl    = _ig_login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted! ID: {media.pk}")
    os.unlink(path)


def post_story_job():
    theme = random.choice(STORY_THEMES)
    logging.info(f"Generating Vita Luxe story...")
    img  = _generate_vita_image(theme)
    path = _save_tmp(img)
    cl    = _ig_login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted! ID: {media.pk}")
    os.unlink(path)


def post_reel_job():
    theme = random.choice(REEL_THEMES)
    logging.info(f"Generating Vita Luxe reel...")
    img  = _generate_vita_image(theme)
    logging.info("Creating video...")
    video_path = _make_reel_video(img)
    caption = random.choice(CAPTIONS) + HASHTAGS
    cl    = _ig_login()
    media = cl.clip_upload(video_path, caption)
    logging.info(f"Reel posted! ID: {media.pk}")
    os.unlink(video_path)


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
    elif mode == "reel":
        post_reel_job()
    elif mode == "delete_stories":
        delete_recent_stories()
    else:
        logging.error(f"Unknown mode: {mode}")
        sys.exit(1)
