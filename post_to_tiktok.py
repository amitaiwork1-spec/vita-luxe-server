# -*- coding: utf-8 -*-
"""
TikTok poster - opens TikTok Studio in your browser (already logged in)
and auto-uploads the video. Simple and reliable.
"""
import sys, io, os, json, random, tempfile, subprocess, urllib.request, time, webbrowser
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

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
    "She shows up every single day 🔥 That's the real secret #VitaLuxe #FitnessMotivation #GlowUp #FitGirl #GymTok #fyp",
    "Luxury is a mindset 💎 Not a price tag #VitaLuxe #WellnessJourney #FitnessTok #BodyGoals #GlowUp #fyp",
    "Train like nobody's watching ✨ Glow like everyone is #VitaLuxe #WorkoutMotivation #FitnessGirl #fyp",
    "Same girl. Different energy. 👑 #VitaLuxe #GlowUp #FitnessMotivation #FitnessTok #fyp",
    "Morning workout hits different 🌅 #VitaLuxe #MorningRoutine #FitnessJourney #fyp",
]

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
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(data); tmp.close()
        paths.append(tmp.name)
        print(f"  {f['name']} ({len(data)//1024}KB)")
    return paths

def create_video(photo_paths):
    n = len(photo_paths)
    dur = round(15.0 / n, 2)
    # Save to Desktop so easy to find
    out = str(Path.home() / "OneDrive" / "Desktop" / "vita_luxe_tiktok.mp4")
    inputs = []
    for p in photo_paths:
        inputs += ["-loop", "1", "-t", str(dur + 0.3), "-i", p]
    sf = "".join([
        f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setpts=PTS-STARTPTS[v{i}];" for i in range(n)
    ])
    sf += "".join([f"[v{i}]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[vout]"
    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex", sf, "-map", "[vout]",
        "-t", "15", "-c:v", "libx264", "-preset", "fast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-y", out
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    size = os.path.getsize(out)
    print(f"  Video: {size//1024}KB")
    return out

# Generate video
print("="*55)
print("  TikTok Video Creator - Vita Luxe")
print("="*55)
print("\nDownloading Vita Luxe photos...")
photos = get_photos(5)
print("\nCreating 15-second vertical video...")
video_path = create_video(photos)

caption = random.choice(CAPTIONS)

# Copy caption to clipboard
try:
    import subprocess as sp
    sp.run(['clip'], input=caption.encode('utf-16'), check=True)
    clipboard_ok = True
except:
    clipboard_ok = False

print("\n" + "="*55)
print("  VIDEO READY!")
print("="*55)
print(f"\n  File: {video_path}")
print(f"  Size: {os.path.getsize(video_path)//1024}KB")
print()
print("  CAPTION (copy this):")
print(f"  {caption}")
print()
if clipboard_ok:
    print("  Caption copied to clipboard automatically!")
print("="*55)
print()
print("  STEPS TO POST:")
print("  1. TikTok Studio will open in your browser")
print("  2. Click '+' or 'Select file'")
print("  3. Choose: Desktop -> vita_luxe_tiktok.mp4")
print("  4. Paste caption (Ctrl+V)")
print("  5. Click POST")
print()
print("  Opening TikTok Studio in 3 seconds...")
print("="*55)

time.sleep(3)
webbrowser.open("https://www.tiktok.com/tiktokstudio/upload")

# Also open file location
subprocess.Popen(['explorer', '/select,', video_path])

print("\nTikTok Studio opened in your browser!")
print("Drag vita_luxe_tiktok.mp4 to the upload area")
print()
print("After posting, run this script again for the next video.")

for p in photos:
    try: os.unlink(p)
    except: pass
