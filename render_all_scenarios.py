"""Render all 4 scenarios from both cameras for the beautified scene."""
import bpy, os, sys

# Insert parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCENE = bpy.context.scene
OUT_DIR = os.path.abspath("renders/presentation")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------
# Scenario configurations
# ---------------------------------------------------------------
SCENARIOS = {
    1: {
        "name": "FULL SOLAR SELF-SUFFICIENCY",
        "subtitle": "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY",
        "solar_txt":  "SOLAR GEN   : 10.0 kW  (48V / 208A) [PEAK]",
        "load_txt":   "CAMPUS LOAD :  8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]",
        "net_txt":    "NET BALANCE : +1.5 kW  [100% SELF-SUSTAINING]",
        "grid_txt":   "GRID IMPORT :  0.0 kW  [STANDBY IDLE]",
        "relay_txt":  "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 2.5, "ac_glow": 2.4, "grid_glow": 0.3, "win_dim": False,
    },
    2: {
        "name": "SOLAR DEFICIT / PEAK DEMAND",
        "subtitle": "SCENARIO 2: SOLAR DEFICIT / PEAK DEMAND",
        "solar_txt":  "SOLAR GEN   :  3.0 kW  (48V / 62A) [REDUCED]",
        "load_txt":   "CAMPUS LOAD :  7.5 kW  [W1:3.0k W2:2.5k W3:2.0k]",
        "net_txt":    "NET BALANCE : -4.5 kW  [DEFICIT - GRID ASSIST]",
        "grid_txt":   "GRID IMPORT : +4.5 kW  [ACTIVE IMPORT]",
        "relay_txt":  "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 1.2, "ac_glow": 2.4, "grid_glow": 3.0, "win_dim": False,
    },
    3: {
        "name": "SOLAR SURPLUS / GRID EXPORT",
        "subtitle": "SCENARIO 3: SOLAR SURPLUS / GRID EXPORT",
        "solar_txt":  "SOLAR GEN   : 12.0 kW  (48V / 250A) [PEAK SUN]",
        "load_txt":   "CAMPUS LOAD :  6.0 kW  [W1:2.5k W2:2.0k W3:1.5k]",
        "net_txt":    "NET BALANCE : +6.0 kW  [SURPLUS EXPORT TO GRID]",
        "grid_txt":   "GRID EXPORT : -6.0 kW  [REVERSE POWER FLOW]",
        "relay_txt":  "RELAYS      : R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 3.0, "ac_glow": 2.0, "grid_glow": 2.8, "win_dim": False,
    },
    4: {
        "name": "NIGHT / PRIORITY LOAD SHEDDING",
        "subtitle": "SCENARIO 4: NIGHT / PRIORITY LOAD SHEDDING",
        "solar_txt":  "SOLAR GEN   :  0.0 kW  (0V / 0A) [NIGHT INACTIVE]",
        "load_txt":   "CAMPUS LOAD :  4.5 kW  [W1:2.0k W2:1.7k W3:SHED]",
        "net_txt":    "NET BALANCE : -4.5 kW  [ESP32 SHEDS NON-CRITICAL]",
        "grid_txt":   "GRID IMPORT : +4.5 kW  [FULL GRID BACKUP]",
        "relay_txt":  "RELAYS      : R1[ON]  R2[ON]  R3[OFF: AUDITORIUM SHED]",
        "dc_glow": 0.1, "ac_glow": 1.8, "grid_glow": 3.2, "win_dim": True,
    },
}

def apply_scenario(sc_id):
    cfg = SCENARIOS[sc_id]
    print(f"  Applying Scenario {sc_id}: {cfg['name']}")

    def set_text(ob_name, text):
        ob = bpy.data.objects.get(ob_name)
        if ob and ob.type == "FONT":
            ob.data.body = text

    set_text("HUD_Scenario_Subtitle", cfg["subtitle"])
    set_text("HUD_Met_Line_Solar",    cfg["solar_txt"])
    set_text("HUD_Met_Line_Load",     cfg["load_txt"])
    set_text("HUD_Met_Line_Net",      cfg["net_txt"])
    set_text("HUD_Met_Line_Grid",     cfg["grid_txt"])
    set_text("HUD_Met_Line_Relay",    cfg["relay_txt"])

    # Update circuit glow
    for mat_name, glow in [
        ("Mat_Wire_DC",   cfg["dc_glow"]),
        ("Mat_Wire_AC",   cfg["ac_glow"]),
        ("Mat_Wire_Grid", cfg["grid_glow"]),
    ]:
        m = bpy.data.materials.get(mat_name)
        if m and m.use_nodes:
            bs = m.node_tree.nodes.get("Principled BSDF")
            if bs and "Emission Strength" in bs.inputs:
                bs.inputs["Emission Strength"].default_value = glow

    # Dim windows if load shed
    glass_mat = bpy.data.materials.get("HITAM_WindowGlass")
    if glass_mat and glass_mat.use_nodes:
        bs = glass_mat.node_tree.nodes.get("Principled BSDF")
        if bs and "Emission Strength" in bs.inputs:
            bs.inputs["Emission Strength"].default_value = 0.3 if cfg["win_dim"] else 0.8

SCENE.render.engine = "BLENDER_EEVEE"
if hasattr(SCENE.eevee, "taa_render_samples"):
    SCENE.eevee.taa_render_samples = 32
SCENE.render.resolution_x = 1920
SCENE.render.resolution_y = 1080
SCENE.render.image_settings.file_format = "PNG"
SCENE.render.image_settings.color_mode = "RGBA"

scenario_names = {
    1: "sufficiency",
    2: "deficit",
    3: "surplus",
    4: "night_shed",
}

cam_configs = [
    ("CAM_ANGLED_VIEW", "angled"),
    ("CAM_TOP_DOWN",    "top_down"),
]

for sc_id in [1, 2, 3, 4]:
    apply_scenario(sc_id)
    for cam_name, cam_tag in cam_configs:
        cam = bpy.data.objects.get(cam_name)
        if not cam:
            print(f"  [WARN] Camera {cam_name} not found, skipping.")
            continue
        SCENE.camera = cam
        fname = f"v4_{cam_tag}_scenario_{sc_id}_{scenario_names[sc_id]}.png"
        fpath = os.path.join(OUT_DIR, fname)
        SCENE.render.filepath = fpath
        bpy.ops.render.render(write_still=True)
        print(f"  RENDERED: {fname}")

print("\n=== All 8 scenario renders complete ===")
