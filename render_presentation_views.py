"""Render presentation stills for Volt Vision v2 across scenarios and camera views."""
import os
import sys
import math
import bpy
from mathutils import Vector, Euler

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
OUT_DIR = os.path.abspath("renders/presentation")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
s = bpy.context.scene

# World Lighting Settings
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
bg.inputs["Strength"].default_value = 0.70
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

sun = bpy.data.objects.get("Light_Sun_Key")
if sun:
    sun.rotation_euler = (math.radians(52), math.radians(-8), math.radians(-38))
    sun.data.energy = 6.2
    if hasattr(sun.data, "color"):
        sun.data.color = (1.0, 0.95, 0.88)

s.render.engine = "BLENDER_EEVEE"
s.view_settings.view_transform = "AgX"
s.view_settings.look = "AgX - Medium High Contrast"
s.view_settings.exposure = -0.10
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.resolution_percentage = 100
if hasattr(s.eevee, "taa_render_samples"):
    s.eevee.taa_render_samples = 32

SCENARIO_CONFIGS = {
    1: {
        "name": "Full Solar Self-Sufficiency",
        "subtitle": "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY",
        "solar_txt": "SOLAR GEN   : 10.0 kW  (48V / 208A) [PEAK]",
        "load_txt":  "CAMPUS LOAD :  8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]",
        "net_txt":   "NET BALANCE : +1.5 kW  [100% SELF-SUSTAINING]",
        "grid_txt":  "GRID IMPORT :  0.0 kW  [STANDBY IDLE]",
        "relay_txt": "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 2.5,
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
        "dc_glow": 3.0,
        "ac_glow": 2.4,
        "grid_glow": 2.6,
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

POS_TOP_DOWN = {
    "Card_Solar":   (-3.5, 15.6, 6.2),
    "Card_Control": (-12.8, 1.8, 1.2),
    "Card_Relay":   (-7.6, -1.2, 1.2),
    "Card_Grid":    (15.5, -11.0, 3.8),
    "Card_Header":  (-17.5, 15.5, 1.5),
    "Card_Metrics": (16.5, 14.5, 1.5),
    "Card_Legend":  (17.5, -6.5, 1.5),
}

POS_ANGLED = {
    "Card_Solar":   (-3.5, 14.5, 8.2),
    "Card_Control": (-13.2, 1.8, 2.8),
    "Card_Relay":   (-7.6, -1.5, 2.4),
    "Card_Grid":    (15.5, -11.0, 5.8),
    "Card_Header":  (-16.0, 16.0, 7.5),
    "Card_Metrics": (16.0, 16.0, 7.5),
    "Card_Legend":  (19.0, -8.0, 4.0),
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

if __name__ == "__main__":
    mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "test"
    if mode == "test":
        render_still("CAM_TOP_DOWN", 1, "test_top_down_s1.png")
        render_still("CAM_ANGLED_VIEW", 1, "test_angled_s1.png")
    elif mode == "all":
        scenario_names = ["sufficiency", "deficit", "surplus", "night_shed"]
        for sid in range(1, 5):
            s_tag = scenario_names[sid - 1]
            render_still("CAM_TOP_DOWN", sid, f"top_down_scenario_{sid}_{s_tag}.png")
            render_still("CAM_ANGLED_VIEW", sid, f"angled_scenario_{sid}_{s_tag}.png")
