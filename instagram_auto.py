# -*- coding: utf-8 -*-
"""
Instagram automation - fetches real lifestyle photos from Pexels API.
Photos look completely authentic (they ARE real photos).
"""
import os, json, logging, urllib.request, urllib.parse, random, sys, tempfile
from pathlib import Path

IG_USERNAME  = os.environ.get("IG_USERNAME", "")
IG_PASSWORD  = os.environ.get("IG_PASSWORD", "")
PEXELS_KEY   = os.environ.get("PEXELS_KEY", "")

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
    "#ActiveLifestyle #FitnessJourney #LuxuryTravel #GlowUp"
)

PHOTO_QUERIES = [
    "fitness woman gym",
    "yoga woman lifestyle",
    "wellness woman luxury",
    "athletic woman workout",
    "healthy lifestyle woman",
    "travel fitness woman",
]

STORY_QUERIES = [
    "selfie woman fitness",
    "woman workout gym",
    "wellness lifestyle woman",
    "woman yoga beach",
    "healthy food woman",
    "woman running outdoor",
    "woman spa wellness",
    "woman travel lifestyle",
]


def _fetch_pexels_photo(query, orientation="square"):
    """Fetch a random photo from Pexels matching the query."""
    if not PEXELS_KEY:
        raise RuntimeError("PEXELS_KEY not set in environment!")

    page = random.randint(1, 5)
    url  = (
        f"https://api.pexels.com/v1/search"
        f"?query={urllib.parse.quote(query)}"
        f"&orientation={orientation}"
        f"&per_page=15"
        f"&page={page}"
        f"&size=large"
    )
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY, "User-Agent": "vita-luxe"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    photos = data.get("photos", [])
    if not photos:
        raise RuntimeError(f"No photos found for query: {query}")

    photo = random.choice(photos)
    img_url = photo["src"]["large2x"]  # High quality

    req2 = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req2, timeout=30) as r:
        return r.read()


def _ig_login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]

    # Try loading saved session first (avoids Instagram challenge)
    session_file = Path("ig_session.json")
    if session_file.exists():
        logging.info("Loading saved Instagram session...")
        cl.load_settings(session_file)
        cl.login(IG_USERNAME, IG_PASSWORD)  # Reuse existing session tokens
    else:
        logging.info("No session file found, doing fresh login...")
        cl.login(IG_USERNAME, IG_PASSWORD)

    return cl


def _save_tmp(data: bytes, suffix=".jpg") -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


def post_photo_job():
    """Post a daily photo to Instagram using Pexels."""
    query = random.choice(PHOTO_QUERIES)
    logging.info(f"Fetching photo: '{query}'")

    img  = _fetch_pexels_photo(query, orientation="square")
    path = _save_tmp(img)

    caption = random.choice(CAPTIONS) + "\n\n" + HASHTAGS
    logging.info(f"Photo size: {len(img)//1024}KB | Logging into Instagram...")

    cl    = _ig_login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted! ID: {media.pk}")
    os.unlink(path)


def post_story_job():
    """Post a story to Instagram using Pexels."""
    query = random.choice(STORY_QUERIES)
    logging.info(f"Fetching story photo: '{query}'")

    img  = _fetch_pexels_photo(query, orientation="portrait")
    path = _save_tmp(img)

    logging.info(f"Story size: {len(img)//1024}KB | Logging into Instagram...")
    cl    = _ig_login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted! ID: {media.pk}")
    os.unlink(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not IG_USERNAME or not IG_PASSWORD:
        logging.error("IG_USERNAME or IG_PASSWORD not set!")
        sys.exit(1)

    if not PEXELS_KEY:
        logging.error("PEXELS_KEY not set! Get free key at pexels.com/api")
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
