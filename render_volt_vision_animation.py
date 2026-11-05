"""Render animated Volt Vision campus simulation with traveling power dots.

Targets a <=1 hour render via the default `1hr` mode:
  - 1280x720, low Eevee samples, bloom on for glow visibility
  - CAM_ANGLED_VIEW, 300 frames (10s @ 30fps)
  - Auto-benchmarks one frame and trims frame count if needed

Usage:
  blender --background VoltVision_v2_WORKING.blend --python enable_power_flow_animation.py
  blender --background VoltVision_v2_WORKING.blend --python render_volt_vision_animation.py -- 1hr
"""
import os
import subprocess
import sys
import time
import bpy

ROOT = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(ROOT, "renders", "animation_frames")
OUTPUT_MP4 = os.path.join(ROOT, "volt_vision_campus_simulation.mp4")
TARGET_SECONDS = 3600  # 1 hour budget

s = bpy.context.scene
mode = "1hr"
if "--" in sys.argv:
    extra = sys.argv[sys.argv.index("--") + 1 :]
    if extra:
        mode = extra[0]

# ---------------------------------------------------------------------------
# Fast render profile (keeps dotted pulses visible)
# ---------------------------------------------------------------------------
s.render.engine = "BLENDER_EEVEE"
s.render.resolution_x = 1280
s.render.resolution_y = 720
s.render.resolution_percentage = 100
s.render.image_settings.file_format = "JPEG"
s.render.image_settings.quality = 85
s.render.image_settings.color_mode = "RGB"
s.render.use_file_extension = True
s.render.fps = 30

ee = s.eevee
if hasattr(ee, "taa_render_samples"):
    ee.taa_render_samples = 6
if hasattr(ee, "use_bloom"):
    ee.use_bloom = True
if hasattr(ee, "use_gtao"):
    ee.use_gtao = False
if hasattr(ee, "use_ssr"):
    ee.use_ssr = False

cam = bpy.data.objects.get("CAM_ANGLED_VIEW") or bpy.data.objects.get("Main_Camera")
if cam:
    s.camera = cam
    print("CAMERA", cam.name)

if mode == "test":
    os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
    s.frame_set(120)
    s.render.filepath = os.path.join(ROOT, "renders", "animation_test_frame")
    bpy.ops.render.render(write_still=True)
    print("WROTE_TEST", s.render.filepath)
    raise SystemExit(0)

# ---------------------------------------------------------------------------
# Benchmark one frame to stay inside the 1-hour budget
# ---------------------------------------------------------------------------
s.frame_set(90)
t0 = time.time()
s.render.filepath = os.path.join(ROOT, "renders", "_bench_frame")
bpy.ops.render.render(write_still=True)
bench_sec = max(time.time() - t0, 1.0)
print(f"BENCHMARK {bench_sec:.1f}s per frame @ {s.render.resolution_x}x{s.render.resolution_y}")

desired_frames = 300  # 10 seconds @ 30fps
if mode == "1hr":
    max_frames = int(TARGET_SECONDS / bench_sec)
    frame_end = min(desired_frames, max_frames, s.frame_end)
    frame_end = max(frame_end, 90)  # at least 3 seconds
elif mode == "short":
    frame_end = 450
elif mode == "full":
    frame_end = s.frame_end
else:
    frame_end = desired_frames

frame_start = 1
duration = frame_end / s.render.fps
eta_min = (bench_sec * frame_end) / 60.0
print(f"PLAN frames={frame_end} duration={duration:.1f}s ETA~{eta_min:.0f}min bench={bench_sec:.1f}s/frame")

os.makedirs(FRAMES_DIR, exist_ok=True)

for f in range(frame_start, frame_end + 1):
    dest = os.path.join(FRAMES_DIR, f"frame_{f:04d}.jpg")
    if os.path.isfile(dest) and os.path.getsize(dest) > 8000:
        if f % 60 == 0:
            print("SKIP", dest)
        continue
    s.frame_set(f)
    s.render.filepath = os.path.splitext(dest)[0]
    bpy.ops.render.render(write_still=True)
    if f == frame_start or f % 30 == 0:
        elapsed = time.time() - t0
        done = f - frame_start + 1
        remaining = frame_end - f
        eta = (elapsed / done) * remaining
        print(f"WROTE {dest} | {done}/{frame_end} | ETA {eta/60:.0f}min")

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(s.render.fps),
    "-start_number", str(frame_start),
    "-i", os.path.join(FRAMES_DIR, "frame_%04d.jpg"),
    "-frames:v", str(frame_end - frame_start + 1),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "fast",
    "-crf", "20",
    "-movflags", "+faststart",
    OUTPUT_MP4,
]
print("+", " ".join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-4000:])
    raise SystemExit(r.returncode)

size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
print("DONE", OUTPUT_MP4, f"{size_mb:.2f} MB", f"{duration:.1f}s")
