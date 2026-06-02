# -*- coding: utf-8 -*-
"""
Instagram automation functions for the server
"""
import os, json, logging, urllib.request, urllib.parse, random
from pathlib import Path

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

STORY_THEMES = [
    "candid selfie in gym mirror, athletic wear, natural lighting, authentic moment",
    "morning coffee flat lay on marble countertop, cozy aesthetic",
    "sunset run on beach, action shot, golden light, athletic body",
    "fresh smoothie bowl close-up, acai bowl with fruits, aesthetic food",
    "yoga mat on hotel balcony, city view, morning light, peaceful",
    "candid laughing moment, natural expression, outdoor cafe, lifestyle",
    "gym progress photo, mirror selfie, athletic outfit, real gym",
    "healthy meal prep, colorful vegetables, kitchen, clean eating",
    "poolside relaxation, luxury resort, candid vacation, natural pose",
    "night workout, gym lights, determined expression, authentic effort",
    "morning skincare routine, bathroom mirror selfie, natural look",
    "reading on sunny terrace, coffee nearby, relaxed lifestyle",
]

CAPTIONS = [
    "Rise and shine, beautiful. Make today count.",
    "Your body is your temple. Treat it like one.",
    "Travel. Train. Thrive. Repeat.",
    "Living proof that consistency changes everything.",
    "Luxury is a mindset, not a price tag.",
    "Strong women build each other up. Tag yours below.",
    "This view though. Never taking it for granted.",
    "Wellness is not a destination. It's a daily choice.",
]

HASHTAGS = (
    "#LuxuryFitness #WellnessLifestyle #FitTravel #HealthyLiving "
    "#MotivationMonday #GymLife #TravelGoals #WellnessInspo "
    "#ActiveLifestyle #FitnessJourney #LuxuryTravel #GlowUp"
)


def _generate_image(prompt: str, width=1080, height=1080, seed=None) -> bytes:
    seed = seed or random.randint(1000, 99999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def _ig_login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]
    cl.login(IG_USERNAME, IG_PASSWORD)
    return cl


def _save_tmp(data: bytes, suffix=".jpg") -> str:
    import tempfile
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(data)
    f.close()
    return f.name


def post_photo_job():
    """Post a daily photo to Instagram."""
    logging.info("Generating daily photo...")
    prompt = (
        "beautiful mixed ethnicity female influencer age 25, long wavy dark brown hair, "
        "luxury athleisure outfit, professional Instagram photo, "
        "lifestyle wellness, cinematic lighting, 4K"
    )
    img = _generate_image(prompt)
    path = _save_tmp(img)
    caption = random.choice(CAPTIONS) + "\n\n" + HASHTAGS
    cl = _ig_login()
    media = cl.photo_upload(path, caption)
    logging.info(f"Photo posted: {media.pk}")
    os.unlink(path)


def post_story_job(story_index: int):
    """Post a story to Instagram with quality control."""
    theme = STORY_THEMES[story_index % len(STORY_THEMES)]
    logging.info(f"Generating story {story_index+1}: {theme[:40]}")

    # Try up to 3 times to get a quality image
    for attempt in range(3):
        prompt = (
            f"realistic Instagram story, mixed female influencer age 25, "
            f"long dark hair, {theme}, vertical 9:16, candid authentic feel, "
            f"natural lighting, shot on iPhone, high quality"
        )
        seed = story_index * 137 + 42 + (attempt * 1000)
        img = _generate_image(prompt, width=1080, height=1920, seed=seed)
        path = _save_tmp(img)

        # Quick quality check: file size
        file_size = os.path.getsize(path) / (1024*1024)
        if file_size < 0.05:
            logging.warning(f"  Attempt {attempt+1}: Image too small ({file_size:.2f}MB), retrying...")
            os.unlink(path)
            continue

        logging.info(f"  ✓ Image quality OK ({file_size:.2f}MB), uploading...")
        break
    else:
        logging.error(f"Could not generate quality image after 3 attempts")
        return

    cl = _ig_login()
    media = cl.photo_upload_to_story(path)
    logging.info(f"Story posted: {media.pk}")
    os.unlink(path)
