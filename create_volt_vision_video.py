"""Create a cinematic, broadcast-quality presentation video for Volt Vision.

Features:
- Title card with college branding and system specs
- Campus architecture & 4-bus circuit overview
- All 4 power consumption & utilization scenarios (Angled 3D view + Top-down aerial schematic)
- Beautiful glassmorphic HUD overlays, telemetry gauges, glowing status badges
- Smooth Ken Burns pan/zoom motion and crossfade transitions
- Conclusion impact summary card
Output: volt_vision_campus_simulation.mp4 (1080p 30fps)
"""
import os
import sys
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERS_DIR = os.path.join(ROOT_DIR, "renders", "presentation")
OUTPUT_VIDEO = os.path.join(ROOT_DIR, "volt_vision_campus_simulation.mp4")
TEMP_DIR = os.path.join(ROOT_DIR, "renders", "_video_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

FONT_HELVETICA = "/System/Library/Fonts/Helvetica.ttc"
FONT_ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
FPS = 30
W, H = 1920, 1080

def get_font(size, bold=False):
    try:
        if bold and os.path.exists(FONT_ARIAL):
            return ImageFont.truetype(FONT_ARIAL, size)
        return ImageFont.truetype(FONT_HELVETICA, size)
    except Exception:
        return ImageFont.load_default()

def create_title_card(output_path, duration=5.0):
    """Generate high-end cinematic title card."""
    img = Image.new("RGBA", (W, H), (11, 19, 38, 255))
    draw = ImageDraw.Draw(img)

    # Ambient radial gradient
    for r in range(700, 0, -10):
        alpha = int(40 * (1.0 - r / 700.0))
        draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], fill=(22, 54, 98, alpha))

    # Top Pill Header
    header_box = [W//2 - 340, 180, W//2 + 340, 230]
    draw.rounded_rectangle(header_box, radius=25, fill=(16, 36, 68, 230), outline=(56, 114, 196, 200), width=2)
    f_badge = get_font(22, bold=True)
    draw.text((W//2, 205), "HITAM COLLEGE OF ENGINEERING & TECHNOLOGY", font=f_badge, fill=(120, 190, 255), anchor="mm")

    # Main Title
    f_title = get_font(72, bold=True)
    draw.text((W//2, 330), "VOLT VISION", font=f_title, fill=(255, 255, 255), anchor="mm")

    f_sub = get_font(34, bold=True)
    draw.text((W//2, 400), "Smart Campus Microgrid & Energy Management System", font=f_sub, fill=(255, 200, 80), anchor="mm")

    # Gold Divider
    draw.line([W//2 - 350, 445, W//2 + 350, 445], fill=(230, 160, 40), width=3)

    # Key Features Cards
    features = [
        ("AUTONOMOUS CONTROL", "ESP32 Priority Routing Engine", (30, 80, 150)),
        ("CLEAN GENERATION", "10 kW Rooftop Solar PV Array", (40, 130, 90)),
        ("LOAD SHEDDING", "Selective Relay Load Isolation", (130, 60, 40)),
        ("GRID INTERACTIVE", "11kV / 415V Net Metering Sync", (70, 50, 140)),
    ]
    card_w, card_h = 360, 150
    start_x = (W - (4 * card_w + 3 * 30)) // 2
    for i, (title, desc, color) in enumerate(features):
        x = start_x + i * (card_w + 30)
        y = 520
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=16, fill=(18, 30, 56, 220), outline=color, width=2)
        f_ct = get_font(20, bold=True)
        f_cd = get_font(18)
        draw.text((x + card_w//2, y + 45), title, font=f_ct, fill=(240, 245, 255), anchor="mm")
        draw.text((x + card_w//2, y + 95), desc, font=f_cd, fill=(170, 190, 220), anchor="mm")

    # Footer
    f_foot = get_font(20)
    draw.text((W//2, 820), "Real-Time 3D Digital Twin Simulation • Comprehensive Multi-Scenario Analysis", font=f_foot, fill=(140, 160, 195), anchor="mm")
    f_ver = get_font(17)
    draw.text((W//2, 860), "PBL Engineering Capstone • Department of Electrical & Electronics Engineering", font=f_ver, fill=(100, 125, 160), anchor="mm")

    img.convert("RGB").save(output_path)

def create_summary_card(output_path, duration=5.0):
    """Generate high-end conclusion summary card."""
    img = Image.new("RGBA", (W, H), (11, 19, 38, 255))
    draw = ImageDraw.Draw(img)

    for r in range(700, 0, -10):
        alpha = int(40 * (1.0 - r / 700.0))
        draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r], fill=(22, 54, 98, alpha))

    # Header
    header_box = [W//2 - 250, 140, W//2 + 250, 190]
    draw.rounded_rectangle(header_box, radius=25, fill=(16, 36, 68, 230), outline=(56, 114, 196, 200), width=2)
    f_badge = get_font(22, bold=True)
    draw.text((W//2, 165), "PERFORMANCE & SIMULATION SUMMARY", font=f_badge, fill=(120, 190, 255), anchor="mm")

    f_title = get_font(54, bold=True)
    draw.text((W//2, 260), "Volt Vision Campus Impact", font=f_title, fill=(255, 255, 255), anchor="mm")

    draw.line([W//2 - 300, 310, W//2 + 300, 310], fill=(230, 160, 40), width=3)

    metrics = [
        ("100%", "Critical Uptime", "Zero brownouts for Wing A Labs under all weather conditions", (40, 160, 90)),
        ("+42%", "Energy Cost Reduction", "Self-consumption prioritized with reverse net-metering export", (30, 120, 200)),
        ("< 50ms", "Switching Response", "ESP32 microcontroller autonomous load shed & grid synchronizer", (210, 140, 30)),
        ("3-Tier", "Priority Matrix", "Tier 1: Labs (Critical) | Tier 2: Classrooms | Tier 3: Auditorium", (160, 60, 180)),
    ]

    card_w, card_h = 520, 180
    xs = [W//2 - card_w - 20, W//2 + 20]
    ys = [370, 590]

    for idx, (val, title, desc, col) in enumerate(metrics):
        col_idx = idx % 2
        row_idx = idx // 2
        x = xs[col_idx]
        y = ys[row_idx]
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=18, fill=(16, 28, 52, 230), outline=col, width=2)
        
        f_val = get_font(44, bold=True)
        f_mt = get_font(22, bold=True)
        f_md = get_font(16)
        
        draw.text((x + 35, y + 40), val, font=f_val, fill=(255, 255, 255))
        draw.text((x + 35, y + 88), title, font=f_mt, fill=col)
        draw.text((x + 35, y + 128), desc, font=f_md, fill=(180, 195, 215))

    f_foot = get_font(20)
    draw.text((W//2, 850), "HITAM College — Smart Solutions, Brighter Generations", font=f_foot, fill=(255, 200, 80), anchor="mm")

    img.convert("RGB").save(output_path)

def overlay_scenario_card(img_path, output_path, badge_text, badge_color, lines, subheader=""):
    """Render a sleek broadcast HUD overlay directly onto an existing still."""
    im = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Top Left Scenario Badge
    bx0, by0 = 40, 40
    bw, bh = 720, 60
    d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=12, fill=(10, 18, 36, 230), outline=badge_color, width=2)
    
    # Glowing status dot
    d.ellipse([bx0 + 20, by0 + 20, bx0 + 38, by0 + 38], fill=badge_color)
    f_badge = get_font(22, bold=True)
    d.text((bx0 + 55, by0 + 30), badge_text, font=f_badge, fill=(255, 255, 255), anchor="lm")

    # Bottom Left Telemetry HUD
    card_w, card_h = 820, 275
    cx0, cy0 = 40, H - card_h - 40
    d.rounded_rectangle([cx0, cy0, cx0 + card_w, cy0 + card_h], radius=16, fill=(10, 18, 36, 235), outline=(50, 90, 150), width=2)

    # Telemetry Header & Subheader (stacked cleanly)
    f_th = get_font(21, bold=True)
    d.text((cx0 + 24, cy0 + 26), "LIVE TELEMETRY & ESP32 POWER FLOW", font=f_th, fill=(100, 180, 255), anchor="lm")
    if subheader:
        f_sub = get_font(17, bold=True)
        d.text((cx0 + 24, cy0 + 52), subheader, font=f_sub, fill=(255, 200, 80), anchor="lm")
    d.line([cx0 + 20, cy0 + 68, cx0 + card_w - 20, cy0 + 68], fill=(40, 70, 110), width=1)

    # Telemetry Lines
    f_line = get_font(18, bold=True)
    f_mono = get_font(18)
    for i, (label, val, val_col) in enumerate(lines):
        ly = cy0 + 92 + i * 35
        d.text((cx0 + 24, ly), label, font=f_line, fill=(200, 215, 235))
        d.text((cx0 + 270, ly), ": " + val, font=f_mono, fill=val_col)

    # Composite overlay
    final_im = Image.alpha_composite(im, overlay).convert("RGB")
    final_im.save(output_path)

def make_clip(input_img, output_mp4, duration, zoom_type="static"):
    """Create video clip from image with optional Ken Burns subtle zoom/pan."""
    num_frames = int(duration * FPS)
    if zoom_type == "zoom_in":
        vf = f"scale=8000:-1,zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={num_frames}:s={W}x{H}:fps={FPS}"
    elif zoom_type == "zoom_out":
        vf = f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.06,max(1.001,zoom-0.0006))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={num_frames}:s={W}x{H}:fps={FPS}"
    elif zoom_type == "pan_down":
        vf = f"scale=8000:-1,zoompan=z='1.05':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+((ih/zoom/4)*(on/{num_frames}))':d={num_frames}:s={W}x{H}:fps={FPS}"
    else:
        vf = f"scale=8000:-1,zoompan=z='min(zoom+0.0003,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={num_frames}:s={W}x{H}:fps={FPS}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", input_img,
        "-t", str(duration),
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        output_mp4
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  Generated clip: {os.path.basename(output_mp4)} ({duration}s)")

def build_full_video():
    print("\n=== Building Volt Vision Presentation Video ===")
    
    # 1. Create Title Card Still
    title_png = os.path.join(TEMP_DIR, "title_card.png")
    create_title_card(title_png)
    
    # 2. Create Summary Card Still
    summary_png = os.path.join(TEMP_DIR, "summary_card.png")
    create_summary_card(summary_png)

    # 3. Create Overlaid Stills for Scenarios
    scenarios_data = [
        {
            "id": 1,
            "name": "sufficiency",
            "badge": "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY",
            "badge_col": (46, 204, 113),
            "sub": "Peak Daylight Operation",
            "lines": [
                ("SOLAR GENERATION", "10.0 kW (48V / 208A) [PEAK]", (46, 204, 113)),
                ("CAMPUS DEMAND", "8.5 kW [Wing A: 3.5k | B: 3.0k | C: 2.0k]", (255, 255, 255)),
                ("NET POWER BALANCE", "+1.5 kW Surplus [100% SELF-SUSTAINING]", (46, 204, 113)),
                ("UTILITY GRID IMPORT", "0.0 kW [STANDBY IDLE - 0 COST]", (180, 200, 220)),
                ("RELAY STATUS", "R1 [ON]  R2 [ON]  R3 [ON] (All Active)", (255, 200, 80)),
            ]
        },
        {
            "id": 2,
            "name": "deficit",
            "badge": "SCENARIO 2: SOLAR DEFICIT / PEAK DEMAND",
            "badge_col": (243, 156, 18),
            "sub": "Grid Assist Active",
            "lines": [
                ("SOLAR GENERATION", "3.0 kW (48V / 62A) [REDUCED CLOUD]", (243, 156, 18)),
                ("CAMPUS DEMAND", "7.5 kW [Wing A: 3.0k | B: 2.5k | C: 2.0k]", (255, 255, 255)),
                ("NET POWER BALANCE", "-4.5 kW Deficit [GRID ASSIST ACTIVE]", (231, 76, 60)),
                ("UTILITY GRID IMPORT", "+4.5 kW [SEAMLESS GRID BACKUP]", (243, 156, 18)),
                ("RELAY STATUS", "R1 [ON]  R2 [ON]  R3 [ON] (Zero Brownout)", (46, 204, 113)),
            ]
        },
        {
            "id": 3,
            "name": "surplus",
            "badge": "SCENARIO 3: SOLAR SURPLUS / GRID EXPORT",
            "badge_col": (52, 152, 219),
            "sub": "Net-Metering Reverse Flow",
            "lines": [
                ("SOLAR GENERATION", "12.0 kW (48V / 250A) [MAX SOLAR INSOLATION]", (52, 152, 219)),
                ("CAMPUS DEMAND", "6.0 kW [Wing A: 2.5k | B: 2.0k | C: 1.5k]", (255, 255, 255)),
                ("NET POWER BALANCE", "+6.0 kW Surplus [EXPORTING CLEAN ENERGY]", (52, 152, 219)),
                ("UTILITY GRID EXPORT", "-6.0 kW [REVERSE METERING CREDIT]", (46, 204, 113)),
                ("RELAY STATUS", "R1 [ON]  R2 [ON]  R3 [ON] (Full Capacity)", (255, 200, 80)),
            ]
        },
        {
            "id": 4,
            "name": "night_shed",
            "badge": "SCENARIO 4: NIGHT OPERATION & LOAD SHEDDING",
            "badge_col": (155, 89, 182),
            "sub": "Smart Priority Protection",
            "lines": [
                ("SOLAR GENERATION", "0.0 kW (0V / 0A) [NIGHT INACTIVE]", (150, 150, 150)),
                ("CAMPUS DEMAND", "4.5 kW [Wing A: 2.0k | B: 1.7k | C: SHED]", (255, 255, 255)),
                ("ESP32 DECISION LOGIC", "Trip Relay 3 (Auditorium Non-Critical Shed)", (231, 76, 60)),
                ("UTILITY GRID IMPORT", "+4.5 kW [ESSENTIAL BACKUP ONLY]", (243, 156, 18)),
                ("RELAY STATUS", "R1 [ON]  R2 [ON]  R3 [OFF: AUDITORIUM SHED]", (231, 76, 60)),
            ]
        },
    ]

    clips = []
    
    # Clip 0: Title Card
    c0 = os.path.join(TEMP_DIR, "clip_00_title.mp4")
    make_clip(title_png, c0, duration=4.5, zoom_type="zoom_in")
    clips.append(c0)

    # Scenario Clips
    clip_idx = 1
    for sc in scenarios_data:
        s_id = sc["id"]
        s_name = sc["name"]
        
        # Angled Still with HUD
        src_angled = os.path.join(RENDERS_DIR, f"v4_angled_scenario_{s_id}_{s_name}.png")
        if not os.path.exists(src_angled):
            print(f"Warning: {src_angled} missing!")
            continue
        ov_angled = os.path.join(TEMP_DIR, f"ov_angled_sc_{s_id}.png")
        overlay_scenario_card(src_angled, ov_angled, sc["badge"], sc["badge_col"], sc["lines"], sc["sub"] + " • Angled 3D View")
        
        clip_ang = os.path.join(TEMP_DIR, f"clip_{clip_idx:02d}_sc{s_id}_ang.mp4")
        make_clip(ov_angled, clip_ang, duration=4.5, zoom_type="zoom_in")
        clips.append(clip_ang)
        clip_idx += 1

        # Top Down Still with HUD
        src_top = os.path.join(RENDERS_DIR, f"v4_top_down_scenario_{s_id}_{s_name}.png")
        if not os.path.exists(src_top):
            print(f"Warning: {src_top} missing!")
            continue
        ov_top = os.path.join(TEMP_DIR, f"ov_top_sc_{s_id}.png")
        overlay_scenario_card(src_top, ov_top, sc["badge"], sc["badge_col"], sc["lines"], sc["sub"] + " • Top-Down Schematic View")
        
        clip_top = os.path.join(TEMP_DIR, f"clip_{clip_idx:02d}_sc{s_id}_top.mp4")
        make_clip(ov_top, clip_top, duration=4.5, zoom_type="zoom_out")
        clips.append(clip_top)
        clip_idx += 1

    # Final Clip: Summary Card
    c_end = os.path.join(TEMP_DIR, f"clip_{clip_idx:02d}_summary.mp4")
    make_clip(summary_png, c_end, duration=5.0, zoom_type="static")
    clips.append(c_end)

    # 4. Concatenate all clips with ffmpeg concat demuxer
    list_txt = os.path.join(TEMP_DIR, "clips_list.txt")
    with open(list_txt, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    print("\nEncoding master presentation video...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_txt,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd_concat, check=True)
    
    file_size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"\nSUCCESS! Master video created: {OUTPUT_VIDEO} ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    build_full_video()
