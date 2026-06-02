# -*- coding: utf-8 -*-
import os, sys, logging, urllib.request, urllib.parse, random, tempfile
logging.basicConfig(level=logging.INFO)

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

STORY_THEMES = [
    "candid selfie in gym mirror, athletic wear, natural lighting",
    "morning coffee flat lay on marble countertop, cozy aesthetic",
    "sunset run on beach, action shot, golden light, athletic body",
    "fresh smoothie bowl close-up, acai bowl, aesthetic food",
    "yoga mat on hotel balcony, city view, morning light",
    "candid laughing moment, outdoor cafe, lifestyle photography",
    "gym progress photo, mirror selfie, athletic outfit",
    "healthy meal prep, colorful vegetables, kitchen, clean eating",
    "poolside relaxation, luxury resort, candid vacation photo",
    "night workout, gym lights, determined expression, authentic",
    "morning skincare routine, bathroom mirror selfie, natural look",
    "reading on sunny terrace, coffee nearby, relaxed lifestyle",
]
CAPTIONS = [
    "Rise and shine. Make today count.",
    "Your body is your temple. Treat it like one.",
    "Travel. Train. Thrive. Repeat.",
    "Consistency changes everything.",
    "Luxury is a mindset, not a price tag.",
    "Strong women build each other up.",
    "This view though. Never taking it for granted.",
    "Wellness is a daily choice.",
]
HASHTAGS = (
    "#LuxuryFitness #WellnessLifestyle #FitTravel #HealthyLiving "
    "#MotivationMonday #GymLife #TravelGoals #WellnessInspo"
)

def gen_image(prompt, w=1080, h=1080):
    import random
    seed = random.randint(1000, 99999)
    url  = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width={w}&height={h}&seed={seed}&nologo=true"
    req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()

def login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]
    cl.login(IG_USERNAME, IG_PASSWORD)
    return cl

def post_photo():
    logging.info("Posting daily photo...")
    prompt = (
        "beautiful mixed ethnicity female influencer age 25, "
        "long wavy dark brown hair, luxury athleisure outfit, "
        "professional Instagram photo, wellness lifestyle, cinematic 4K"
    )
    data = gen_image(prompt)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(data); path = f.name
    caption = random.choice(CAPTIONS) + "\n\n" + HASHTAGS
    cl = login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted: {media.pk}")

def post_story():
    import datetime, time as t
    hour = datetime.datetime.utcnow().hour + 3  # Israel time
    idx  = hash(str(datetime.date.today()) + str(hour)) % len(STORY_THEMES)
    theme = STORY_THEMES[idx]
    logging.info(f"Posting story: {theme[:40]}")
    prompt = (
        f"realistic Instagram story, mixed female influencer age 25, "
        f"long dark hair, {theme}, vertical 9:16, candid authentic, "
        f"natural lighting, high quality Instagram aesthetic"
    )
    data = gen_image(prompt, 1080, 1920)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(data); path = f.name
    cl = login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted: {media.pk}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "photo"
    if cmd == "photo":
        post_photo()
    elif cmd == "story":
        post_story()
    else:
        print(f"Unknown command: {cmd}")
