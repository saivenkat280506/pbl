"""Render solar_management.blend (6300f @ 30fps) with Eevee to JPEG frames, then MP4.

  blender --background solar_management.blend --python volt_vision_blender/render_solar_management.py
"""
import os
import sys
import subprocess
import bpy

blend = bpy.data.filepath
root = os.path.dirname(os.path.abspath(blend))
frames_dir = os.path.join(root, "renders", "solar_management_frames")
os.makedirs(frames_dir, exist_ok=True)
mp4_path = os.path.join(root, "solar_management.mp4")

s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE"
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.resolution_percentage = 100
s.render.image_settings.file_format = "JPEG"
s.render.image_settings.quality = 92
s.render.image_settings.color_mode = "RGB"
s.render.use_file_extension = True
s.render.fps = 30
s.frame_start = 1
s.frame_end = 6300
s.frame_step = 1

ee = s.eevee
if hasattr(ee, "taa_render_samples"):
    ee.taa_render_samples = 8
if hasattr(ee, "use_bloom"):
    ee.use_bloom = True
if hasattr(ee, "use_gtao"):
    ee.use_gtao = True

print("ENGINE", s.render.engine)
print("FRAMES", s.frame_start, s.frame_end, "step", s.frame_step)
print("OUT", frames_dir)

mode = "anim"
if "--" in sys.argv:
    extra = sys.argv[sys.argv.index("--") + 1 :]
    if extra:
        mode = extra[0]

if mode == "test":
    s.frame_current = 180
    bpy.context.view_layer.update()
    s.render.filepath = os.path.join(root, "renders", "solar_management_test")
    bpy.ops.render.render(write_still=True)
    print("WROTE_TEST")
    raise SystemExit(0)

# Resume-friendly still loop (skip frames already on disk)
for f in range(s.frame_start, s.frame_end + 1, s.frame_step):
    dest = os.path.join(frames_dir, f"frame_{f:04d}.jpg")
    if os.path.isfile(dest) and os.path.getsize(dest) > 10000:
        if f % 300 == 0:
            print("SKIP", dest)
        continue
    s.frame_current = f
    s.render.filepath = os.path.splitext(dest)[0]
    bpy.ops.render.render(write_still=True)
    if f == s.frame_start or f % 30 == 0:
        print("WROTE", dest)

print("DONE_FRAMES", frames_dir)

# Encode if ffmpeg is available
ffmpeg = "ffmpeg"
try:
    subprocess.run([ffmpeg, "-version"], capture_output=True, check=True)
except Exception:
    print("NO_FFMPEG")
    raise SystemExit(0)

cmd = [
    ffmpeg, "-y",
    "-framerate", "30",
    "-i", os.path.join(frames_dir, "frame_%04d.jpg"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "medium", "-crf", "18",
    "-movflags", "+faststart",
    mp4_path,
]
print("+", " ".join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-4000:])
    raise SystemExit(r.returncode)
print("WROTE_MP4", mp4_path, os.path.getsize(mp4_path))
