"""Build captioned Volt Vision explainer MP4 from Blender hero stills + end card.
Run: python3 volt_vision_blender/make_video.py
Captions are burned with PIL (no ffmpeg drawtext needed).
Output: renders/volt_vision_explainer.mp4 (1920x1080, 24fps, H.264)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STILLS = os.path.join(HERE, "renders", "stills")
OUT = os.path.join(HERE, "renders", "volt_vision_explainer.mp4")
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
FPS = 24

SEGMENTS = [
    ("shot1_solar.png", "Solar Panel", 3),
    ("shot2_controller.png", "ESP32 Controller", 4),
    ("shot3_battery.png", "Relay + Battery", 4),
    ("shot4_grid.png", "Grid", 3),
    ("shot5_buildings_lit.png", "Critical Loads", 3),
    ("shot5_buildings_shed.png", "Load-Shed", 4),
    ("shot6_final.png", "Volt Vision Solar Plant", 5),
]

def run(cmd):
    print("+", " ".join(cmd)[:200])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        sys.exit(r.returncode)
    return r

def caption_image(src, text, dst):
    """Reference style: bold black bar, top-left, white text."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(src).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")
    try:
        font = ImageFont.truetype(FONT_PATH, 56)
    except Exception:
        font = ImageFont.load_default()
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x0, y0 = 36, 30
    d.rounded_rectangle([x0, y0, x0 + tw + 56, y0 + th + 36], radius=18, fill=(0, 0, 0, 235))
    d.text((x0 + 28, y0 + 14), text, font=font, fill=(255, 255, 255))
    im.save(dst)

def end_card(dst, W=1920, H=1080):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), (10, 10, 12))
    d = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype(FONT_PATH, 120)
        f2 = ImageFont.truetype(FONT_PATH, 48)
        f3 = ImageFont.truetype(FONT_PATH, 32)
    except Exception:
        f1 = f2 = f3 = ImageFont.load_default()
    for txt, f, y, col in [
        ("VOLT VISION", f1, H // 2 - 120, (255, 255, 255)),
        ("Campus Solar Priority System", f2, H // 2 + 20, (255, 184, 77)),
        ("ESP32 : Solar Priority + Load Shedding", f3, H // 2 + 100, (255, 255, 255)),
    ]:
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((W - (bb[2] - bb[0])) / 2, y), txt, font=f, fill=col)
    im.save(dst)

def main():
    from PIL import Image  # noqa: verify early
    tmp = os.path.join(HERE, "renders", "_seg")
    os.makedirs(tmp, exist_ok=True)
    parts = []
    for i, (f, cap, secs) in enumerate(SEGMENTS):
        src = os.path.join(STILLS, f)
        if not os.path.exists(src):
            sys.exit(f"missing still: {src}")
        cap_png = os.path.join(tmp, f"cap{i}.png")
        caption_image(src, cap, cap_png)
        dst = os.path.join(tmp, f"seg{i}.mp4")
        run(["ffmpeg", "-y", "-loop", "1", "-i", cap_png,
             "-t", str(secs), "-r", str(FPS),
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "medium", "-crf", "20", dst])
        parts.append(dst)
    end_png = os.path.join(tmp, "end.png")
    end_card(end_png)
    end_mp4 = os.path.join(tmp, "end.mp4")
    run(["ffmpeg", "-y", "-loop", "1", "-i", end_png,
         "-t", "4", "-r", str(FPS),
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-preset", "medium", "-crf", "20", end_mp4])
    parts.append(end_mp4)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT])
    print("WROTE", OUT, f"({os.path.getsize(OUT)/1e6:.1f} MB)")

if __name__ == "__main__":
    main()
