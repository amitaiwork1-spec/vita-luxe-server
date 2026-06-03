# -*- coding: utf-8 -*-
"""
Instagram automation for Vita Luxe.
Uses pre-generated images from GitHub repo (images/photos/ and images/stories/).
"""
import os, json, logging, urllib.request, random, sys, tempfile
from pathlib import Path

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

REPO = "amitaiwork1-spec/vita-luxe-server"

CAPTIONS = [
    "Rise and grind. Every rep counts. 💪\n\n",
    "Golden hour energy only. ✨\n\n",
    "Luxury is a lifestyle, not a price tag. 💎\n\n",
    "She trained. She glowed. She conquered. 🔥\n\n",
    "Your body. Your rules. Your results. 👑\n\n",
    "Travel. Train. Thrive. Repeat. ✈️\n\n",
    "Living proof that consistency changes everything. 🌟\n\n",
    "Wellness is not a destination. It is a daily choice. 🧘\n\n",
]

HASHTAGS = (
    "#VitaLuxe #LuxuryFitness #FitnessGirl #WellnessLifestyle "
    "#FitBody #GymLife #HealthyLiving #FitnessMotivation "
    "#BodyGoals #FitnessCommunity #ActiveLifestyle #GlowUp"
)


def _get_random_image(folder):
    """Download random pre-generated image from GitHub repo."""
    url = f"https://api.github.com/repos/{REPO}/contents/images/{folder}"
    req = urllib.request.Request(url, headers={"User-Agent": "vita-luxe"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            files = json.loads(r.read())
        if not files:
            raise RuntimeError(f"No images in images/{folder}/")
        chosen = random.choice(files)
        dl_url = chosen["download_url"]
        req2 = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=30) as r:
            return r.read()
    except Exception as e:
        raise RuntimeError(f"Failed to get image from repo: {e}")


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


def _save_tmp(data: bytes, suffix=".jpg") -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


def post_photo_job():
    logging.info("Getting Vita Luxe photo from library...")
    img  = _get_random_image("photos")
    path = _save_tmp(img)
    caption = random.choice(CAPTIONS) + HASHTAGS
    logging.info(f"Photo: {len(img)//1024}KB | Logging in...")
    cl    = _ig_login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted! {media.pk}")
    os.unlink(path)


def post_story_job():
    logging.info("Getting Vita Luxe story from library...")
    img  = _get_random_image("stories")
    path = _save_tmp(img)
    logging.info(f"Story: {len(img)//1024}KB | Logging in...")
    cl    = _ig_login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted! {media.pk}")
    os.unlink(path)


def post_reel_job():
    """Create reel from photo using ffmpeg zoom effect."""
    import subprocess
    logging.info("Getting Vita Luxe image for reel...")
    img  = _get_random_image("photos")
    img_path = _save_tmp(img, suffix=".jpg")

    out_path = tempfile.mktemp(suffix=".mp4")
    logging.info("Creating reel video with ffmpeg...")
    result = subprocess.run([
        "ffmpeg", "-loop", "1", "-i", img_path,
        "-vf", "scale=1080:1080,zoompan=z='min(zoom+0.001,1.3)':d=450:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1080",
        "-t", "15", "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-y", out_path
    ], capture_output=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()[-200:]}")

    caption = random.choice(CAPTIONS) + HASHTAGS
    logging.info(f"Reel video ready | Logging in...")
    cl    = _ig_login()
    media = cl.clip_upload(out_path, caption)
    logging.info(f"Reel posted! {media.pk}")
    os.unlink(img_path)
    os.unlink(out_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not IG_USERNAME or not IG_PASSWORD:
        logging.error("IG credentials not set!")
        sys.exit(1)
    mode = sys.argv[1] if len(sys.argv) > 1 else "photo"
    logging.info(f"Mode={mode} | IG={IG_USERNAME[:5]}***")
    if mode == "photo":
        post_photo_job()
    elif mode == "story":
        post_story_job()
    elif mode == "reel":
        post_reel_job()
    else:
        logging.error(f"Unknown mode: {mode}")
        sys.exit(1)
