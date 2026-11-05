# Volt Vision — Blender 3D Simulation (BUILT + RESTRUCTURED)

Photoreal labeled-infographic explainer: **"Volt Vision — Low-Cost Real-Time Energy Monitoring and Solar Priority System for Educational Buildings Using ESP32."**

All renders below are real Blender 5.2 Eevee output from the included `.blend`, not mockups.
Restructured in place per the Muse Code brief — no geometry replaced, only recolored/restaged/rewired.

## Battery question (from brief)

Yes — the grey box near the controller **was** the battery cabinet. Per your instructions I converted
it into the **Relay/Switching Unit** (light-grey sheet metal, open tub with orange-copper busbars +
black relay coils, "RELAY / SWITCHING" label) and moved the 12V pack + charge LEDs beside it as a
separate **12V BATTERY** station. Shot 3's caption now reads "Relay/Switching Unit + 12V Battery".

## Style pass (toon_style.py — reference look)

Flat CAD animation look: Standard view transform, high-noon sun, bright sky; saturated
flat materials (bright-blue gridded PV with 36 added grid fingers, teal transformer with
insulator stacks + extra fins + orange drops, sandy pavement); background steel pylon;
video captions switched to bold black rounded bars top-left ("Solar Panel", "Grid", …).
Window emission tuned to 8/6 so close-ups don't blow out. Campus layout kept (not desert).

## Restructure changelog (restructure.py + fixup2.py, run in place)

- Lighting: single warm sun (~5500K, 45° altitude, energy 3.0) + sky fill (0.75, bluer turbidity 2.2);
  both area lights deleted. Ground = light-grey pavement with expansion-joint strips.
- PV: navy cells (0.015, 0.07, 0.30) + silver busbars; frame = brushed aluminum (metallic 1.0, rough 0.35).
- Controller: dark solder-mask base (green-black; no copper-trace texture existed, so flat
  dark-green approximates it), red + blue status LEDs, light-grey opaque enclosure + glass window face.
- Buildings: warm cream walls, blue-grey roofs, windows 14 (critical) / 10 (non-critical) warm amber.
- Grid: teal meter + teal transformer can (new, pole-mounted, grey ceramic bushings), wood-brown pole,
  grey ceramic insulators, silver-grey conductors.
- Wires: 21 tangled curves deleted; rebuilt as red DC (panel→controller), orange AC
  (controller→A/B/C, C on its own dimmable material), green DATA (controller→relay, controller→meter),
  grey dashed GRID (wave-band transparency shader) with gentle arcs. Legend board bottom-right.
- Cameras/labels: untouched angles; Shot 3 caption updated to Relay/Switching Unit.
- Cases: `scene["volt_case"]` + `renders/cases/case_{high_solar,low_solar,balanced,outage}.png`
  (CAM_Final). Outage hides grid lines, shows red X at meter (small — grid absence + dark C carry it),
  C windows go dark via material swap (WinC has load-shed keyframes, so presets swap materials
  instead of fighting the fcurve). Toggle live: set `scene["volt_case"]` and call the preset block
  in `render_cases.py`.

## Deliverables

- `volt_vision.blend` — full scene (252 objects: 6 tracked cameras, 600-frame timeline with markers, animated LED blink + Building-C load-shed, pylon, transformer detail)
- `volt_vision_scene.py` — builder script (re-run to regenerate the `.blend`)
- `render_stills.py` — hero-still renderer (Blender background mode)
- `make_video.py` — captioned explainer assembler (PIL + ffmpeg)
- `renders/stills/` — 7 hero stills, 1920×1080 PNG (Eevee)
- `renders/cases/` — 4 case-variant wides (high_solar / low_solar / balanced / outage)
- `renders/volt_vision_explainer.mp4` — **30 s, 1920×1080, 24 fps, H.264** captioned explainer

## Video shot list (matches master prompt)

| Time | Still | Caption (white-on-black) |
|---|---|---|
| 0–3 s | `shot1_solar.png` | Solar Panel — Rooftop PV Array (30° tilt, blue AR cells + busbars, alu frame + legs) |
| 3–7 s | `shot2_controller.png` | ESP32 Controller — Real-Time Monitoring and MPPT (ESP32, CN3791, 2× ACS712, 2× ZMPT101B, 16×2 LCD, blinking LED) |
| 7–10 s | `shot3_battery.png` | 12V Battery — Backup Storage (cabinet + 4 green charge LEDs) |
| 10–13 s | `shot4_grid.png` | Grid — Backup Supply (wall meter + breaker + conduit to campus pole) |
| 13–16 s | `shot5_buildings_lit.png` | Buildings A + B — Critical Loads (always on, warm amber) |
| 16–20 s | `shot5_buildings_shed.png` | Building C — Non-Critical, Auto Load-Shed (dims f440→480) |
| 20–25 s | `shot6_final.png` | VOLT VISION — Campus Solar Priority System (pull-back: amber=solar, green=battery, purple=grid) |
| 25–29 s | end card | VOLT VISION / Campus Solar Priority System |

## Rebuild / re-render

```bash
# 1. Regenerate .blend (Blender 4.x/5.x, ~10 s)
blender --background --python volt_vision_blender/volt_vision_scene.py

# 2. Re-render hero stills (~40 s, Eevee 1080p)
blender --background volt_vision_blender/volt_vision.blend \
  --python volt_vision_blender/render_stills.py

# 3. Rebuild captioned MP4 (~30 s, needs ffmpeg + PIL)
python3 volt_vision_blender/make_video.py

# 3b. Re-render case variants (~20 s)
blender --background volt_vision_blender/volt_vision.blend \
  --python volt_vision_blender/render_cases.py

# 4. (Optional) Full 600-frame camera animation — SLOW on CPU Eevee
#    (~30 s/frame at 1080p ≈ 5 h). Render overnight or on GPU, or
#    disable DoF / drop to 50% resolution first:
blender --background volt_vision_blender/volt_vision.blend \
  --render-output volt_vision_blender/renders/frames/frame_#### \
  --frame-start 1 --frame-end 600 --render-anim
```

## Scene notes

- Cameras use TRACK_TO constraints to focus empties, with keyframed lateral glide (shots 1–5) and pull-back (final). Lenses: 45/40/38/35 mm close-ups (DoF f/2.8), 26/24 mm wides.
- Markers SHOT1..SHOT6 carry camera binding (`camera` on 5.x / `camera_data` on 4.x).
- Lighting: sun 2.6 + area key 450 + fill 160, sky background 0.55, Filmic, exposure −0.4, bloom on.
- Captions are burned in post (PIL) for crisp text; the 3D scene stays clean from every angle.
- Eevee default (fast iteration); switch Render Engine to Cycles + Denoise for hero glass/metal frames.
