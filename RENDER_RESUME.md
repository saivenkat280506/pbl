# Volt Vision Animation Render — Resume Guide

**Stopped:** Friday, 18 September 2026, 10:05 PM (IST / UTC+5:30)

---

## Where we stopped

| Item | Status |
|------|--------|
| Blender model | `VoltVision_v2_WORKING.blend` — ready |
| Power-flow dots | Enabled via `enable_power_flow_animation.py` |
| Animation frames | **61 / 300** completed |
| Last frame on disk | `renders/animation_frames/frame_0061.jpg` |
| Final MP4 | **Not encoded yet** (old `volt_vision_campus_simulation.mp4` is the static slideshow, not this render) |

**Render was manually stopped** after ~10 minutes. At ~10 sec/frame, **239 frames remain** (~40 min) plus ~2 min FFmpeg encode.

---

## Target output

- **Video:** `volt_vision_campus_simulation.mp4`
- **Frames folder:** `renders/animation_frames/`
- **Settings (1hr mode):** 1280×720, 30 fps, 300 frames (10 sec), Eevee 6 samples, `CAM_ANGLED_VIEW`
- **Reference style:** `~/Movies/solar_management.mp4` (dotted power pulses along circuit wires)

---

## Resume when ready

From the project root (`/Users/saivenkat/Projects/pbl`):

```bash
# Optional: re-apply pulse materials if the blend was edited
blender --background VoltVision_v2_WORKING.blend \
  --python enable_power_flow_animation.py

# Resume render (skips existing frames 0001–0061 automatically)
blender --background VoltVision_v2_WORKING.blend \
  --python render_volt_vision_animation.py -- 1hr
```

The render script skips any frame file already in `renders/animation_frames/` with size > 8 KB, so it will continue from **frame 62**.

---

## Key scripts

| File | Purpose |
|------|---------|
| `enable_power_flow_animation.py` | Emissive/dashed wires + traveling pulse dots on `FX_Pulse_*` curves |
| `render_volt_vision_animation.py` | Benchmark + render frames + FFmpeg to MP4 (`1hr` mode) |
| `create_volt_vision_video.py` | **Old** static slideshow from PNG stills (not the animated sim) |

---

## Notes

- Full-scene 1080p animation was estimated at **3–11+ hours**; `1hr` mode was chosen to finish in ~50 min.
- If you need a longer clip later, use `-- full` or increase `desired_frames` in `render_volt_vision_animation.py` (expect proportionally longer render time).
