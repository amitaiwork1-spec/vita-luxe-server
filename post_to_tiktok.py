# -*- coding: utf-8 -*-
"""
TikTok Auto-Poster for Vita Luxe
Uses saved session so login is needed only ONCE manually.
"""
import sys, io, os, json, random, tempfile, subprocess, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

env = {}
with open(Path(__file__).parent / ".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"')

TOKEN = env.get("GITHUB_TOKEN", "")
REPO  = "amitaiwork1-spec/vita-luxe-server"
HDR   = {"Authorization": "token " + TOKEN, "User-Agent": "vita-luxe"}
SESSION_FILE = Path(__file__).parent / "tiktok_session.json"

CAPTIONS = [
    "She shows up every single day 🔥 That's the real secret #VitaLuxe #FitnessMotivation #GlowUp #FitGirl #GymTok",
    "Luxury is a mindset 💎 Not a price tag #VitaLuxe #WellnessJourney #FitnessTok #BodyGoals #GlowUp",
    "Train like nobody's watching ✨ Glow like everyone is #VitaLuxe #WorkoutMotivation #FitnessGirl #GymLife",
    "Same girl. Different energy. 👑 #VitaLuxe #GlowUp #FitnessMotivation #FitnessTok #BodyGoals",
    "Morning workout hits different when you love yourself 🌅 #VitaLuxe #MorningRoutine #FitnessJourney",
]


def get_photos(count=6):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/images/photos", headers=HDR)
    with urllib.request.urlopen(req, timeout=15) as r:
        files = [f for f in json.loads(r.read()) if f.get("size", 0) > 100000]
    random.shuffle(files)
    paths = []
    for f in files[:count]:
        req2 = urllib.request.Request(f["download_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=30) as r:
            data = r.read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(data); tmp.close()
        paths.append(tmp.name)
        print(f"  {f['name']} ({len(data)//1024}KB)")
    return paths


def create_video(photo_paths):
    n = len(photo_paths)
    dur = round(15.0 / n, 2)
    out = tempfile.mktemp(suffix=".mp4")
    inputs = []
    for p in photo_paths:
        inputs += ["-loop", "1", "-t", str(dur + 0.5), "-i", p]
    sf = "".join([
        f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setpts=PTS-STARTPTS[v{i}];"
        for i in range(n)
    ])
    sf += "".join([f"[v{i}]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[vout]"
    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex", sf, "-map", "[vout]",
        "-t", "15", "-c:v", "libx264", "-preset", "fast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", out
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    size = os.path.getsize(out)
    print(f"Video ready: {size//1024}KB")
    return out


def post_to_tiktok(video_path, caption):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=800)

        # Load saved session if exists
        if SESSION_FILE.exists():
            print("Loading saved TikTok session...")
            ctx = browser.new_context(
                storage_state=str(SESSION_FILE),
                viewport={"width": 1280, "height": 900}
            )
        else:
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})

        page = ctx.new_page()

        # Go to TikTok Studio
        print("Opening TikTok Studio...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Check if logged in
        if "login" in page.url or "passport" in page.url:
            print("\n" + "="*50)
            print("  PLEASE LOG IN MANUALLY IN THE BROWSER!")
            print("  1. Enter email: amitaiwork1@gmail.com")
            print("  2. Enter password: Amitai2612")
            print("  3. Complete any CAPTCHA if shown")
            print("  4. Wait - script will continue automatically")
            print("="*50)

            # Wait up to 90 seconds for manual login
            for i in range(90):
                time.sleep(1)
                if "tiktokstudio" in page.url or "upload" in page.url:
                    print("Login detected! Continuing...")
                    break
                if i % 10 == 0:
                    print(f"  Waiting for login... ({90-i}s remaining)")

        # Save session for future use
        ctx.storage_state(path=str(SESSION_FILE))
        print("Session saved for future use!")

        # Now on TikTok Studio - wait for upload area
        print("Looking for upload area...")
        page.wait_for_timeout(3000)

        # Find file input
        file_input = page.query_selector("input[type='file']")
        if not file_input:
            # Try clicking the upload area
            try:
                page.click("text=Select file", timeout=5000)
                page.wait_for_timeout(1000)
                file_input = page.query_selector("input[type='file']")
            except:
                pass

        if file_input:
            print("Uploading video...")
            file_input.set_input_files(video_path)
            page.wait_for_timeout(10000)  # Wait for upload to process
            print("Video uploaded!")

            # Add caption - find the text editor
            print("Adding caption...")
            for sel in [
                "[data-contents='true']",
                ".public-DraftEditor-content",
                "div[contenteditable='true']",
                ".notranslate",
                "[placeholder*='caption']",
                "[class*='caption']",
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        page.wait_for_timeout(500)
                        page.keyboard.press("Control+a")
                        page.keyboard.type(caption[:2200])
                        print(f"  Caption added via: {sel}")
                        break
                except: pass

            page.wait_for_timeout(2000)

            # Click Post button
            print("Posting...")
            for btn in ["Post", "Publish", "Upload", "Submit"]:
                try:
                    page.click(f"button:has-text('{btn}')", timeout=5000)
                    page.wait_for_timeout(5000)
                    print(f"POSTED via '{btn}' button!")
                    break
                except: pass

        else:
            print("Upload area not found - screenshot saved")
            page.screenshot(path=r"C:\Users\10022\AppData\Local\Temp\tt_debug.png")
            print("Check: C:\\Users\\10022\\AppData\\Local\\Temp\\tt_debug.png")
            page.wait_for_timeout(30000)  # Give user time to see

        page.wait_for_timeout(3000)
        browser.close()


# Run
print("="*55)
print("  TikTok Auto-Poster - Vita Luxe")
print("="*55)
print("\nDownloading photos...")
photos = get_photos(5)
print("\nCreating video (1080x1920)...")
video = create_video(photos)
caption = random.choice(CAPTIONS)
print(f"\nCaption: {caption[:60]}...")
print("\nPosting to TikTok...")
post_to_tiktok(video, caption)
for p in photos:
    try: os.unlink(p)
    except: pass
print("\nDone!")
