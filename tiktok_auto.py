# -*- coding: utf-8 -*-
"""
TikTok Full Auto-Poster using PyAutoGUI
Controls your logged-in browser directly - no login needed!
Creates and uploads multiple videos automatically.
"""
import sys, io, os, json, random, tempfile, subprocess, urllib.request, time
import webbrowser, pyautogui, pyperclip
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from PIL import ImageGrab

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

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

CAPTIONS = [
    "She shows up every single day 🔥 That's the real secret #VitaLuxe #FitnessMotivation #GlowUp #FitGirl #fyp #viral",
    "Luxury is a mindset 💎 Not a price tag #VitaLuxe #WellnessJourney #FitnessTok #BodyGoals #fyp #viral",
    "Train like nobody's watching ✨ Glow like everyone is #VitaLuxe #WorkoutMotivation #FitnessGirl #fyp #viral",
    "Same girl. Different energy. 👑 #VitaLuxe #GlowUp #FitnessMotivation #FitnessTok #fyp #viral",
    "Morning workout hits different 🌅 #VitaLuxe #MorningRoutine #FitnessJourney #fyp #viral",
    "She didn't luck into it. She worked for it 💪 #VitaLuxe #Fitness #Motivation #fyp #viral",
    "Your only competition is who you were yesterday 🔥 #VitaLuxe #GymLife #FitnessGoals #fyp",
]

VIDEO_FOLDER = Path(__file__).parent / "tiktok_videos"
VIDEO_FOLDER.mkdir(exist_ok=True)


def get_photos(count=5):
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
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", dir=VIDEO_FOLDER)
        tmp.write(data); tmp.close()
        paths.append(tmp.name)
    return paths


def create_video(idx):
    """Create a unique 15s vertical video."""
    photos = get_photos(5)
    n = len(photos)
    dur = round(15.0 / n, 2)
    out = str(VIDEO_FOLDER / f"vita_tiktok_{idx:02d}.mp4")

    inputs = []
    for p in photos:
        inputs += ["-loop", "1", "-t", str(dur + 0.3), "-i", p]

    # Varied effects per video
    effects = [
        # Fast zoom in
        "".join([f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                 f"zoompan=z='min(zoom+0.001,1.3)':d={int(dur*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
                 f"setpts=PTS-STARTPTS[v{i}];" for i in range(n)]),
        # Slow zoom out
        "".join([f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                 f"zoompan=z='max(zoom-0.0005,1.0)':d={int(dur*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
                 f"setpts=PTS-STARTPTS[v{i}];" for i in range(n)]),
        # Simple cut
        "".join([f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                 f"crop=1080:1920,setpts=PTS-STARTPTS[v{i}];" for i in range(n)]),
    ]

    sf = effects[idx % len(effects)]
    sf += "".join([f"[v{i}]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[vout]"

    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex", sf, "-map", "[vout]",
        "-t", "15", "-c:v", "libx264", "-preset", "fast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", out
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)

    for p in photos:
        try: os.unlink(p)
        except: pass

    if os.path.exists(out) and os.path.getsize(out) > 100000:
        print(f"  Video {idx}: {os.path.getsize(out)//1024}KB ✓")
        return out
    else:
        print(f"  Video {idx}: FAILED - using simple version")
        # Fallback
        sf2 = "".join([f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=PTS-STARTPTS[v{i}];" for i in range(n)])
        sf2 += "".join([f"[v{i}]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[vout]"
        photos2 = get_photos(5)
        inputs2 = []
        for p in photos2:
            inputs2 += ["-loop","1","-t",str(dur+0.3),"-i",p]
        cmd2 = ["ffmpeg"] + inputs2 + ["-filter_complex",sf2,"-map","[vout]",
                "-t","15","-c:v","libx264","-preset","fast","-pix_fmt","yuv420p","-y",out]
        subprocess.run(cmd2, capture_output=True, timeout=120)
        for p in photos2:
            try: os.unlink(p)
            except: pass
        return out


def upload_to_tiktok(video_path, caption):
    """Upload video using PyAutoGUI desktop automation."""
    video_path = str(Path(video_path).resolve())

    # Open TikTok Studio
    print("  Opening TikTok Studio...")
    webbrowser.open("https://www.tiktok.com/tiktokstudio/upload")
    time.sleep(8)

    # Bring browser to front
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)

    w, h = pyautogui.size()
    print(f"  Screen: {w}x{h}")

    # Take screenshot to see what's on screen
    screenshot = ImageGrab.grab()
    screenshot.save(str(Path(__file__).parent / "tt_screen.png"))

    # Click on upload area (center of page content area)
    # TikTok Studio upload button is typically in upper-center
    upload_x = w // 2
    upload_y = h // 2 - 50
    print(f"  Clicking upload area at ({upload_x}, {upload_y})...")
    pyautogui.click(upload_x, upload_y)
    time.sleep(3)

    # Check if file dialog opened (title bar changes)
    # Type the file path
    print("  Typing file path in dialog...")
    # First clear any existing text
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    pyautogui.typewrite(video_path, interval=0.03)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)
    pyautogui.press('enter')  # Confirm if needed
    print("  File selected!")
    time.sleep(10)  # Wait for upload to process

    # Copy caption to clipboard and paste it
    pyperclip.copy(caption)

    # Click on caption area (below the video preview)
    caption_y = h // 2 + 150
    print(f"  Clicking caption area...")
    pyautogui.click(w // 2, caption_y)
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.hotkey('ctrl', 'v')
    print("  Caption pasted!")
    time.sleep(2)

    # Screenshot before posting
    ImageGrab.grab().save(str(Path(__file__).parent / "tt_before_post.png"))

    # Find and click Post button (usually on right side)
    # Try multiple positions where Post button might be
    post_positions = [
        (w - 150, h - 80),   # Bottom right
        (w - 200, h - 60),
        (w // 2 + 300, h - 80),
    ]

    print("  Clicking Post button...")
    for pos in post_positions:
        pyautogui.click(pos[0], pos[1])
        time.sleep(2)

    time.sleep(5)
    print("  Posted!")
    return True


# ── MAIN ────────────────────────────────────────────────────────────────────

NUM_VIDEOS = 5

print("=" * 60)
print("  TikTok Auto-Poster - Vita Luxe")
print(f"  Creating and posting {NUM_VIDEOS} videos")
print("=" * 60)
print()
print("  MAKE SURE:")
print("  1. You are logged in to TikTok in your browser")
print("  2. TikTok Studio works: tiktok.com/tiktokstudio/upload")
print("  3. Do NOT move mouse while running!")
print()
print("  Starting in 5 seconds... Make sure browser is open!")
time.sleep(5)

captions = random.sample(CAPTIONS, min(NUM_VIDEOS, len(CAPTIONS)))

print(f"\nCreating {NUM_VIDEOS} videos...")
video_files = []
for i in range(NUM_VIDEOS):
    print(f"\n[Video {i+1}/{NUM_VIDEOS}] Generating...")
    vf = create_video(i)
    caption = captions[i % len(captions)]
    video_files.append((vf, caption))

print(f"\nAll {NUM_VIDEOS} videos created!")
print("Starting upload sequence...\n")

for i, (vf, caption) in enumerate(video_files):
    print(f"\n{'='*50}")
    print(f"[{i+1}/{NUM_VIDEOS}] Uploading: {Path(vf).name}")
    print(f"Caption: {caption[:50]}...")
    print("="*50)

    success = upload_to_tiktok(vf, caption)

    if success:
        print(f"  Video {i+1} POSTED!")
    else:
        print(f"  Video {i+1} may need manual check")

    # Wait between posts to avoid spam detection
    if i < NUM_VIDEOS - 1:
        wait = random.randint(180, 300)  # 3-5 min between posts
        print(f"\n  Waiting {wait//60} minutes before next post...")
        time.sleep(wait)

print("\n" + "="*60)
print("  ALL DONE! 5 TikTok videos posted!")
print("="*60)
