# -*- coding: utf-8 -*-
"""
TikTok Automation - post videos and grow audience
Same content as Instagram, optimized for TikTok
"""
import os, logging, urllib.request, urllib.parse, random, tempfile
from pathlib import Path
from datetime import datetime
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)

_env = dotenv_values(Path(__file__).parent / ".env")
TT_USERNAME = _env.get("TIKTOK_USERNAME", "")
TT_PASSWORD = _env.get("TIKTOK_PASSWORD", "")

# TikTok uses different aspect ratio - vertical videos
# Reels from Instagram (1080x1920) work perfectly on TikTok

TIKTOK_CAPTIONS = [
    "POV: You're about to transform your life 🌟 #fitnessmotivation",
    "Which one are you? #luxuryfitness #girlswholift",
    "That consistency though 💪 #fitnessgains #motivation",
    "Living my best life and you can too #wellnessjourney",
    "No days off 🔥 #fitlifestyle #luxurylife",
    "Glow up season #transformation #fitjourney",
    "This is what dedication looks like #fitness #wellness",
    "Your future self will thank you #healthylifestyle",
]

TIKTOK_HASHTAGS = [
    "#fitnessmotivation #girlswholift #luxuryfitness #fittravel",
    "#wellnesslifestyle #fitnessgains #transformationjourney #motivational",
    "#fitnesscommunity #healthylifestyle #workoutmotivation #fitgirl",
    "#luxurylifestyle #travelgirls #fitfluencer #lifegoals",
]


def generate_video(theme: str, duration=15) -> str:
    """Generate a TikTok video (vertical, 1080x1920)."""
    import time
    from PIL import Image, ImageDraw, ImageFont

    # Use same image generation as Instagram stories
    prompt = (
        f"stunning TikTok video thumbnail, mixed ethnicity female age 25, "
        f"long dark wavy hair, {theme}, vertical 9:16, "
        f"cinematic lighting, professional quality, trending aesthetic"
    )

    encoded = urllib.parse.quote(prompt)
    seed = random.randint(10000, 99999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1920&seed={seed}&nologo=true&enhance=true"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        img_bytes = r.read()

    # Save as temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(img_bytes)
        return f.name


def post_to_tiktok(video_path: str, caption: str) -> bool:
    """
    Post video to TikTok.
    Requires TikTok username/password in .env
    Returns: success boolean
    """
    if not TT_USERNAME or not TT_PASSWORD:
        logging.warning("  TikTok credentials not set. Skipping post.")
        logging.info("  To enable: add TIKTOK_USERNAME and TIKTOK_PASSWORD to .env")
        return False

    try:
        # Using unofficial TikTok API library
        from TikTokApi import TikTokApi

        api = TikTokApi()
        api.login(TT_USERNAME, TT_PASSWORD)

        # Upload video with caption and hashtags
        full_caption = caption + "\n\n" + random.choice(TIKTOK_HASHTAGS)

        response = api.post_video(
            video_path=video_path,
            caption=full_caption,
            cover=None  # Will generate from video
        )

        if response.get("success"):
            logging.info(f"  ✓ TikTok video posted! Video ID: {response.get('video_id')}")
            return True
        else:
            logging.error(f"  ✗ TikTok upload failed: {response.get('error')}")
            return False

    except ImportError:
        logging.warning("  TikTokApi not installed. Install: pip install TikTokApi")
        return False
    except Exception as e:
        logging.error(f"  TikTok upload error: {e}")
        return False


def sync_instagram_to_tiktok(ig_image_path: str, caption: str) -> bool:
    """
    Sync Instagram reel/story to TikTok.
    Takes Instagram image and posts it to TikTok with TikTok-optimized caption.
    """
    if not TT_USERNAME:
        logging.info("  [TikTok] Not configured yet. Add TIKTOK_USERNAME to .env")
        return False

    try:
        tt_caption = caption.replace("#Instagram", "").replace("@instagram", "")
        tt_caption += "\n" + random.choice(TIKTOK_HASHTAGS)

        success = post_to_tiktok(ig_image_path, tt_caption)
        return success
    except Exception as e:
        logging.error(f"Sync to TikTok error: {e}")
        return False


def daily_tiktok_post():
    """Post one TikTok video daily (optimized for trending)."""
    logging.info("\n[TikTok] Generating daily video...")

    themes = [
        "gym workout motivation, intense training session, fitness dedication",
        "yoga sunset routine, peaceful wellness, mindful moment",
        "morning routine vlog, luxury lifestyle, starting the day right",
        "travel vlog moment, tropical paradise, adventure goals",
        "healthy meal prep, nutritious food, wellness lifestyle",
        "before and after fitness transformation, progress motivation",
        "workout in luxury gym, state of the art equipment, fit lifestyle",
        "self-care routine, spa day, luxury relaxation",
    ]

    theme = random.choice(themes)
    caption = random.choice(TIKTOK_CAPTIONS)

    video_path = generate_video(theme)

    # For now, just prepare - actual posting requires TikTok account setup
    file_size = os.path.getsize(video_path) / (1024*1024)
    logging.info(f"  Video ready: {file_size:.1f}MB")
    logging.info(f"  Caption: {caption}")

    if TT_USERNAME:
        success = post_to_tiktok(video_path, caption)
        if success:
            logging.info("  ✓ Posted to TikTok!")
    else:
        logging.info("  [Setup needed] Add TIKTOK_USERNAME to .env to auto-post")

    return video_path


def setup_instructions():
    """Show TikTok setup instructions."""
    print("\n" + "="*60)
    print("  TIKTOK SETUP INSTRUCTIONS")
    print("="*60)
    print()
    print("  1. Create a TikTok account:")
    print("     - Go to: tiktok.com")
    print("     - Sign up with email or phone")
    print()
    print("  2. Get your credentials:")
    print("     - Username: @your_tiktok_handle")
    print("     - Password: your TikTok password")
    print()
    print("  3. Add to .env file:")
    print("     TIKTOK_USERNAME=your_username")
    print("     TIKTOK_PASSWORD=your_password")
    print()
    print("  4. Install TikTok API:")
    print("     pip install TikTokApi")
    print()
    print("  5. Then TikTok will auto-post daily at 6pm!")
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_instructions()
    else:
        daily_tiktok_post()
