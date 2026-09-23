"""1080p Eevee render of solar_management.blend, sped to a 1:30 video.

The scene is 6300 frames at 30 fps (3:30). This samples 2700 of those
frames and plays them at 30 fps, which is 90 seconds.
"""
import os
import subprocess
import bpy

SRC_START = 1
SRC_END = 6300
OUT_FPS = 30
OUT_SECONDS = 90
OUT_FRAMES = OUT_FPS * OUT_SECONDS  # 2700

root = os.path.dirname(os.path.abspath(bpy.data.filepath))
frames_dir = os.path.join(root, "renders", "solar_management_1080p")
os.makedirs(frames_dir, exist_ok=True)
mp4_path = os.path.join(root, "solar_management_1080p.mp4")

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 90
scene.render.image_settings.color_mode = "RGB"
scene.render.use_file_extension = True
scene.render.fps = OUT_FPS

eevee = scene.eevee
if hasattr(eevee, "taa_render_samples"):
    eevee.taa_render_samples = 8

def source_frame(index):
    span = OUT_FRAMES - 1
    return int(round(SRC_START + (index / span) * (SRC_END - SRC_START)))

print(f"PLAN {OUT_FRAMES} frames @ {OUT_FPS}fps = {OUT_SECONDS}s from source {SRC_START}-{SRC_END}")

for index in range(OUT_FRAMES):
    dest = os.path.join(frames_dir, f"frame_{index + 1:04d}.jpg")
    if os.path.isfile(dest) and os.path.getsize(dest) > 10000:
        continue
    scene.frame_set(source_frame(index))
    scene.render.filepath = os.path.splitext(dest)[0]
    bpy.ops.render.render(write_still=True)
    if index == 0 or (index + 1) % 30 == 0:
        print(f"WROTE {index + 1}/{OUT_FRAMES}", flush=True)

print("DONE_FRAMES", frames_dir)

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(OUT_FPS),
    "-i", os.path.join(frames_dir, "frame_%04d.jpg"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "medium", "-crf", "18",
    "-movflags", "+faststart",
    mp4_path,
]
print("+", " ".join(cmd))
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(result.stderr[-4000:])
    raise SystemExit(result.returncode)
print("WROTE_MP4", mp4_path, os.path.getsize(mp4_path))
