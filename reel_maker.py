# -*- coding: utf-8 -*-
"""
Viral Reel Creator for Vita Luxe
Creates professional-looking reels with:
- Multiple photos with smooth transitions
- Text overlays with trending captions
- Dynamic zoom/pan effects
- Optimized for virality
"""
import os, sys, json, random, logging, urllib.request, tempfile, subprocess
from pathlib import Path

REPO = "amitaiwork1-spec/vita-luxe-server"

VIRAL_CAPTIONS_TEXT = [
    "She didn't luck into it.\nShe worked for it. 💪",
    "Train like nobody's watching.\nGlow like everyone is. ✨",
    "Your body is a luxury.\nTreat it like one. 💎",
    "Same girl.\nDifferent energy. 🔥",
    "Morning workout hits different\nwhen you love yourself. 🌅",
    "Not a trend.\nA lifestyle. 👑",
    "She said she'd start Monday.\nShe started today. ⚡",
    "Swipe to see the glow up. 💫",
]

REEL_HASHTAGS = (
    "#FitnessMotivation #GlowUp #FitGirl #WorkoutMotivation "
    "#LuxuryLifestyle #FitnessJourney #BodyGoals #GymLife "
    "#HealthyLiving #FitnessInspo #VitaLuxe #ViralFitness "
    "#FitnessTok #MotivationMonday #WellnessJourney"
)


def get_photos_from_repo(count=6):
    """Download multiple photos from GitHub for the reel."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/images/photos",
        headers={"User-Agent": "vita-luxe"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        files = [f for f in json.loads(r.read()) if f.get("size", 0) > 30000]

    selected = random.sample(files, min(count, len(files)))
    paths = []
    for f in selected:
        req2 = urllib.request.Request(f["download_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=30) as r:
            data = r.read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(data)
        tmp.close()
        paths.append(tmp.name)
        logging.info(f"  Downloaded: {f['name']} ({len(data)//1024}KB)")
    return paths


def create_viral_reel(photo_paths, output_path):
    """
    Create a viral-style reel:
    - Each photo: 2.5 seconds with smooth Ken Burns effect
    - Fade transitions between photos
    - Motivational text overlay
    - Total: ~15 seconds (6 photos x 2.5s)
    """
    n = len(photo_paths)
    duration_each = 15.0 / n  # spread evenly across 15 seconds

    # Build filter complex for ffmpeg
    inputs = []
    for p in photo_paths:
        inputs.extend(["-loop", "1", "-t", str(duration_each + 0.5), "-i", p])

    # Scale each input to 1080x1080, then apply zoompan
    filter_parts = []
    zooms = ["min(zoom+0.0008,1.3)", "max(zoom-0.0005,1.0)", "min(zoom+0.001,1.4)"]

    for i in range(n):
        zoom_expr = zooms[i % len(zooms)]
        d = int(duration_each * 30)  # frames at 30fps
        x_expr = "iw/2-(iw/zoom/2)" if i % 2 == 0 else "0"
        y_expr = "ih/2-(ih/zoom/2)" if i % 3 != 2 else "0"
        filter_parts.append(
            f"[{i}:v]scale=1080:1080:force_original_aspect_ratio=increase,"
            f"crop=1080:1080,"
            f"zoompan=z='{zoom_expr}':d={d}:x='{x_expr}':y='{y_expr}':s=1080x1080:fps=30,"
            f"setpts=PTS-STARTPTS[v{i}]"
        )

    # Crossfade between clips
    concat_filter = ""
    if n == 1:
        concat_filter = f"[v0]copy[vout]"
    else:
        # Chain xfades
        prev = "v0"
        for i in range(1, n):
            offset = duration_each * i - 0.3
            out = f"xf{i}" if i < n - 1 else "vout"
            concat_filter += f"[{prev}][v{i}]xfade=transition=fade:duration=0.3:offset={offset:.2f}[{out}];"
            prev = out
        concat_filter = concat_filter.rstrip(";")

    # Text overlay with motivational quote
    quote = random.choice(VIRAL_CAPTIONS_TEXT).replace("'", "\\'")
    line1 = quote.split("\\n")[0] if "\\n" in quote else quote[:30]
    line2 = quote.split("\\n")[1] if "\\n" in quote else ""

    text_filter = (
        f"[vout]drawtext=text='{line1}':fontsize=52:fontcolor=white:x=(w-text_w)/2:y=h*0.08:"
        f"shadowcolor=black:shadowx=2:shadowy=2:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf,"
        f"drawtext=text='{line2}':fontsize=46:fontcolor=white:x=(w-text_w)/2:y=h*0.08+70:"
        f"shadowcolor=black:shadowx=2:shadowy=2:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf[vfinal]"
        if line2 else
        f"[vout]drawtext=text='{line1}':fontsize=52:fontcolor=white:x=(w-text_w)/2:y=h*0.1:"
        f"shadowcolor=black:shadowx=2:shadowy=2:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf[vfinal]"
    )

    full_filter = ";".join(filter_parts) + ";" + concat_filter + ";" + text_filter

    cmd = (
        inputs +
        ["-filter_complex", full_filter,
         "-map", "[vfinal]",
         "-t", "15",
         "-c:v", "libx264",
         "-preset", "fast",
         "-crf", "23",
         "-pix_fmt", "yuv420p",
         "-movflags", "+faststart",
         "-y", output_path]
    )

    logging.info("  Running ffmpeg...")
    result = subprocess.run(["ffmpeg"] + cmd, capture_output=True, timeout=180)
    if result.returncode != 0:
        # Fallback: simple slideshow without transitions
        logging.warning("  Advanced filter failed, using simple slideshow...")
        simple_cmd = inputs + [
            "-filter_complex",
            "".join([f"[{i}:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,setpts=PTS-STARTPTS[v{i}];" for i in range(n)]) +
            "".join([f"[v{i}]" for i in range(n)]) + f"concat=n={n}:v=1:a=0[vout]",
            "-map", "[vout]",
            "-t", "15",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-y", output_path
        ]
        result2 = subprocess.run(["ffmpeg"] + simple_cmd, capture_output=True, timeout=180)
        if result2.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result2.stderr.decode()[-300:]}")

    size = os.path.getsize(output_path)
    logging.info(f"  Reel created: {size//1024//1024}MB")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.info("Creating viral reel...")
    photos = get_photos_from_repo(6)
    out = tempfile.mktemp(suffix=".mp4")
    create_viral_reel(photos, out)
    logging.info(f"Reel ready at: {out}")
    for p in photos:
        os.unlink(p)
