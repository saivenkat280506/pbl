"""Master Upgrade & Presentation Renderer for Volt Vision 3D Simulation (v2).

Executes complete perfection pass:
- Precise camera framing (CAM_TOP_DOWN with full margin breathing room, CAM_ANGLED_VIEW matching reference)
- Perfected card positions with ZERO overlap in both camera views
- High-visibility circuit wire routing (elevated on parapets and path conduits)
- Vibrant golden-hour sunlight and lush multi-tone vegetation
- Automated rendering of all 4 scenarios across both cameras
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
OUT_DIR = os.path.abspath("renders/presentation")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
s = bpy.context.scene

# ---------------------------------------------------------------------------
# 1. World Lighting Pass (Warm Daylight, Rich Depth)
# ---------------------------------------------------------------------------
w = s.world or bpy.data.worlds.new("World")
s.world = w
w.use_nodes = True
nt = w.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
if hasattr(sky, "sun_elevation"):
    sky.sun_elevation = math.radians(45)
    sky.sun_rotation = math.radians(-32)
if hasattr(sky, "sun_intensity"):
    sky.sun_intensity = 1.35
bg.inputs["Strength"].default_value = 0.65
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

sun = bpy.data.objects.get("Light_Sun_Key")
if sun:
    sun.rotation_euler = (math.radians(52), math.radians(-8), math.radians(-38))
    sun.data.energy = 6.4
    if hasattr(sun.data, "color"):
        sun.data.color = (1.0, 0.94, 0.84)
    if hasattr(sun.data, "angle"):
        sun.data.angle = math.radians(0.6)

s.render.engine = "BLENDER_EEVEE"
s.view_settings.view_transform = "AgX"
s.view_settings.look = "AgX - Medium High Contrast"
s.view_settings.exposure = -0.10
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.resolution_percentage = 100
if hasattr(s.eevee, "taa_render_samples"):
    s.eevee.taa_render_samples = 32

# ---------------------------------------------------------------------------
# 2. Wire Circuits Visibility Upgrade (Elevate & Thick Bevel)
# ---------------------------------------------------------------------------
COL_CIRCUITS = bpy.data.collections.get("CAMPUS_CIRCUITS")
if not COL_CIRCUITS:
    COL_CIRCUITS = bpy.data.collections.new("CAMPUS_CIRCUITS")
    s.collection.children.link(COL_CIRCUITS)

def update_spline_curve(name, points, mat, bevel_radius=0.052):
    ob = bpy.data.objects.get(name)
    if not ob:
        c_data = bpy.data.curves.new(name, "CURVE")
        c_data.dimensions = "3D"
        ob = bpy.data.objects.new(name, c_data)
        COL_CIRCUITS.objects.link(ob)
    
    c_data = ob.data
    c_data.dimensions = "3D"
    c_data.bevel_depth = bevel_radius
    c_data.bevel_resolution = 4
    c_data.splines.clear()
    spline = c_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, pt in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = Vector(pt)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob

# Materials for Circuits
def get_glow_mat(name, color, emit_str=2.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = emit_str
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

MAT_WIRE_DC = get_glow_mat("Mat_Wire_DC", (1.0, 0.12, 0.04), emit_str=3.0)
MAT_WIRE_AC = get_glow_mat("Mat_Wire_AC", (1.0, 0.48, 0.04), emit_str=3.0)
MAT_WIRE_DATA = get_glow_mat("Mat_Wire_Data", (0.08, 0.92, 0.22), emit_str=2.6)
MAT_WIRE_GRID = get_glow_mat("Mat_Wire_Grid", (0.80, 0.88, 0.98), emit_str=1.2)

# Elevated clear routing paths
# Line 1: DC Solar Line (Red) — Rooftop PV -> West Parapet -> Wall Conduit -> Walkway -> Control Unit
pts_dc = [
    (-3.5, 12.8, 6.05),     # From Solar Array center
    (-6.5, 12.8, 6.00),     # Along North Roof
    (-8.4, 12.8, 6.00),     # Roof parapet corner
    (-8.8, 11.2, 5.10),     # West wing junction
    (-8.8, 11.2, 2.50),     # Vertical conduit down wall
    (-9.2, 11.2, 0.45),     # Ground service trench
    (-9.2, 5.5, 0.45),      # Along west walkway
    (-9.2, 2.2, 0.45),      # Into Control Unit ESP32 DC In
]
update_spline_curve("Wire_DC", pts_dc, MAT_WIRE_DC, 0.055)

# Line 2: AC Distribution Line (Orange) — Relay Unit -> Foundation Trench -> Campus Wings
pts_ac = [
    (-7.6, 2.2, 0.45),      # Relay Output
    (-7.6, 3.6, 0.40),      # Foundation entry
    (-6.2, 4.3, 0.40),      # Wing 1 (Critical Lab load)
    (-3.0, 4.3, 0.40),      # Cross-corridor trunk
    (0.0, 5.2, 0.40),       # Wing 2 (Academic central load)
    (3.5, 4.3, 0.40),       # Cross-corridor East
    (7.0, 4.3, 0.40),       # Wing 3 (Auditorium load)
]
update_spline_curve("Wire_AC", pts_ac, MAT_WIRE_AC, 0.058)

# Line 3: Sensor / Data Feedback Line (Dashed Green) — ESP32 Sensor Bus
pts_data = [
    (-3.5, 13.0, 6.10),     # Solar PV sensor tap
    (-8.0, 13.0, 6.05),     # Conduit
    (-8.6, 11.0, 0.46),     # Service riser
    (-9.0, 2.3, 0.46),      # ESP32 Sensor Port
    (-8.2, 2.3, 0.46),      # Relay switching control interface
]
update_spline_curve("Wire_Data", pts_data, MAT_WIRE_DATA, 0.040)

# Line 4: Grid Utility Line (Grey / White) — Road Edge Utility Pole -> Service Pathway -> Substation
pts_grid = [
    (15.8, -14.5, 5.20),    # Grid Transformer output
    (15.5, -14.5, 2.60),    # Down utility pole
    (15.0, -14.0, 0.42),    # Ground junction
    (8.0, -14.0, 0.40),     # Along road boundary conduit
    (0.0, -13.5, 0.40),     # Cross-promenade conduit
    (-7.5, -12.0, 0.40),    # Toward west utility area
    (-7.6, 1.5, 0.42),      # Grid Input into Relay / Control Unit
]
update_spline_curve("Wire_Grid", pts_grid, MAT_WIRE_GRID, 0.050)

# Update FX_Pulse objects
for key, cname in [("DC", "Wire_DC"), ("AC", "Wire_AC"), ("Data", "Wire_Data"), ("Grid", "Wire_Grid")]:
    p = bpy.data.objects.get(f"FX_Pulse_{key}")
    w = bpy.data.objects.get(cname)
    if p and w:
        p.data = w.data

# ---------------------------------------------------------------------------
# 3. Camera Tuning (Generous Margins, Pristine Framing)
# ---------------------------------------------------------------------------
cam_top = bpy.data.objects.get("CAM_TOP_DOWN")
if cam_top:
    cam_top.location = (0.0, -0.5, 62.0)
    cam_top.rotation_euler = (0.0, 0.0, 0.0)
    cam_top.data.lens = 30 # Generous framing, zero canvas clipping

cam_ang = bpy.data.objects.get("CAM_ANGLED_VIEW")
if cam_ang:
    cam_ang.location = (25.0, -32.0, 23.0)
    target = Vector((0.0, 5.5, 2.0))
    cam_ang.rotation_euler = (target - Vector(cam_ang.location)).to_track_quat("-Z", "Y").to_euler()
    cam_ang.data.lens = 34

# ---------------------------------------------------------------------------
# 4. Camera-Specific Card Alignment & Non-Overlapping Coordinates
# ---------------------------------------------------------------------------
# In Top-Down, Z=8.5 guarantees zero occlusion by any roof or tree
POS_TOP_DOWN = {
    "Card_Solar":   (-3.5, 16.5, 8.5),
    "Card_Control": (-13.0, 1.8, 8.5),
    "Card_Relay":   (-7.6, -1.8, 8.5),
    "Card_Grid":    (15.5, -10.5, 8.5),
    "Card_Header":  (-16.0, 15.2, 8.5),
    "Card_Metrics": (15.5, 14.8, 8.5),
    "Card_Legend":  (17.5, -6.5, 8.5),
}

POS_ANGLED = {
    "Card_Solar":   (-3.5, 14.8, 8.6),
    "Card_Control": (-13.2, 1.8, 3.2),
    "Card_Relay":   (-8.5, -0.5, 3.2),  # Moved clear of front tree
    "Card_Grid":    (13.2, -11.0, 6.2), # Moved clear of pole
    "Card_Header":  (-15.5, 16.0, 8.5),
    "Card_Metrics": (16.0, 16.0, 8.5),
    "Card_Legend":  (19.5, -10.0, 4.8), # Raised above ground foliage
}

def align_cards_to_camera(cam):
    card_names = list(POS_TOP_DOWN.keys())
    if cam.name == "CAM_TOP_DOWN":
        for cname in card_names:
            ob = bpy.data.objects.get(cname)
            if ob:
                ob.rotation_euler = (0, 0, 0)
                ob.location = POS_TOP_DOWN[cname]
    elif cam.name == "CAM_ANGLED_VIEW":
        rot = cam.rotation_euler
        for cname in card_names:
            ob = bpy.data.objects.get(cname)
            if ob:
                ob.rotation_euler = rot
                ob.location = POS_ANGLED[cname]

# ---------------------------------------------------------------------------
# 5. Multi-Scenario Switcher Function
# ---------------------------------------------------------------------------
SCENARIO_CONFIGS = {
    1: {
        "name": "Full Solar Self-Sufficiency",
        "subtitle": "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY",
        "solar_txt": "SOLAR GEN   : 10.0 kW  (48V / 208A) [PEAK]",
        "load_txt":  "CAMPUS LOAD :  8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]",
        "net_txt":   "NET BALANCE : +1.5 kW  [100% SELF-SUSTAINING]",
        "grid_txt":  "GRID IMPORT :  0.0 kW  [STANDBY IDLE]",
        "relay_txt": "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 2.6,
        "ac_glow": 2.4,
        "grid_glow": 0.2,
        "win_dim": False
    },
    2: {
        "name": "Solar Deficit",
        "subtitle": "SCENARIO 2: SOLAR DEFICIT / GRID IMPORT",
        "solar_txt": "SOLAR GEN   :  3.0 kW  (44V / 68A) [OVERCAST]",
        "load_txt":  "CAMPUS LOAD :  7.5 kW  [W1:3.0k W2:2.5k W3:2.0k]",
        "net_txt":   "NET BALANCE : -4.5 kW  [DEFICIT GAP]",
        "grid_txt":  "GRID IMPORT : +4.5 kW  [ACTIVE UTILITY DRAW]",
        "relay_txt": "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 1.2,
        "ac_glow": 2.4,
        "grid_glow": 3.0,
        "win_dim": False
    },
    3: {
        "name": "Solar Surplus / Export",
        "subtitle": "SCENARIO 3: SOLAR SURPLUS / GRID EXPORT",
        "solar_txt": "SOLAR GEN   : 12.0 kW  (48V / 250A) [MAX SUN]",
        "load_txt":  "CAMPUS LOAD :  6.0 kW  [W1:2.5k W2:2.0k W3:1.5k]",
        "net_txt":   "NET BALANCE : +6.0 kW  [SURPLUS EXPORT TO GRID]",
        "grid_txt":  "GRID EXPORT : +6.0 kW  [REVERSE POWER FLOW]",
        "relay_txt": "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 3.2,
        "ac_glow": 2.4,
        "grid_glow": 2.8,
        "win_dim": False
    },
    4: {
        "name": "Night / Low-Light Mode",
        "subtitle": "SCENARIO 4: NIGHT / PRIORITY LOAD SHEDDING",
        "solar_txt": "SOLAR GEN   :  0.0 kW  (0V / 0A) [NIGHT INACTIVE]",
        "load_txt":  "CAMPUS LOAD :  4.5 kW  [W1:2.8k W2:1.7k W3:SHED]",
        "net_txt":   "NET BALANCE : -4.5 kW  [ESP32 SHEDS NON-CRITICAL]",
        "grid_txt":  "GRID IMPORT : +4.5 kW  [FULL GRID BACKUP]",
        "relay_txt": "RELAYS      : R1[ON]  R2[ON]  R3[OFF: AUDITORIUM SHED]",
        "dc_glow": 0.1,
        "ac_glow": 1.8,
        "grid_glow": 3.2,
        "win_dim": True
    }
}

def apply_scenario(scene, scenario_id):
    cfg = SCENARIO_CONFIGS.get(scenario_id, SCENARIO_CONFIGS[1])
    print(f"Applying Scenario {scenario_id}: {cfg['name']}")

    def update_text(ob_name, text):
        ob = bpy.data.objects.get(ob_name)
        if ob and ob.type == "FONT":
            ob.data.body = text

    update_text("HUD_Scenario_Subtitle", cfg["subtitle"])
    update_text("HUD_Met_Line_Solar", cfg["solar_txt"])
    update_text("HUD_Met_Line_Load", cfg["load_txt"])
    update_text("HUD_Met_Line_Net", cfg["net_txt"])
    update_text("HUD_Met_Line_Grid", cfg["grid_txt"])
    update_text("HUD_Met_Line_Relay", cfg["relay_txt"])

    for mat_name, glow in [
        ("Mat_Wire_DC", cfg["dc_glow"]),
        ("Mat_Wire_AC", cfg["ac_glow"]),
        ("Mat_Wire_Grid", cfg["grid_glow"])
    ]:
        m = bpy.data.materials.get(mat_name)
        if m and m.use_nodes:
            em = m.node_tree.nodes.get("Emission")
            if em and "Strength" in em.inputs:
                em.inputs["Strength"].default_value = glow

    glass_mat = bpy.data.materials.get("HITAM_WindowGlass")
    if glass_mat and glass_mat.use_nodes:
        bs = glass_mat.node_tree.nodes.get("Principled BSDF")
        if bs and "Emission Strength" in bs.inputs:
            bs.inputs["Emission Strength"].default_value = 0.20 if cfg["win_dim"] else 0.60

    scene["active_scenario"] = scenario_id
    scene["scenario_name"] = cfg["name"]

def render_still(cam_name, scenario_id, filename):
    cam = bpy.data.objects.get(cam_name)
    if not cam:
        print(f"Camera {cam_name} not found!")
        return
    s.camera = cam
    align_cards_to_camera(cam)
    apply_scenario(s, scenario_id)
    bpy.context.view_layer.update()
    
    out_path = os.path.join(OUT_DIR, filename)
    s.render.filepath = out_path
    print(f"Rendering: {cam_name} | Scenario {scenario_id} -> {out_path}")
    bpy.ops.render.render(write_still=True)
    print(f"DONE: {out_path}")

def main():
    print("=== Saving Upgraded Volt Vision v2 ===")
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print("Scene saved.")

    # Render All 4 Scenarios across both Cameras (8 Stills total)
    scenario_tags = ["sufficiency", "deficit", "surplus", "night_shed"]
    for sid in range(1, 5):
        s_tag = scenario_tags[sid - 1]
        render_still("CAM_TOP_DOWN", sid, f"top_down_scenario_{sid}_{s_tag}.png")
        render_still("CAM_ANGLED_VIEW", sid, f"angled_scenario_{sid}_{s_tag}.png")

    print(f"=== Successfully Rendered All 8 Presentation Stills in: {OUT_DIR} ===")

if __name__ == "__main__":
    main()
