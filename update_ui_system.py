"""Master update and verification for Volt Vision v2 in Blender 5.2.

Implements perfected UI card system with emissive solid dark-navy fill,
razor-sharp white typography, glowing accent borders, camera-billboarded
orientation, realistic equipment pointers, and multi-scenario states.
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
SCENE = bpy.context.scene

# ---------------------------------------------------------------------------
# Clean Shaders for Solid Dark Navy Cards & Crisp Text
# ---------------------------------------------------------------------------
def make_emissive_mat(name, color, strength=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

# High-contrast solid dark navy (no specular wash-out from sky)
MAT_CARD_BG = make_emissive_mat("UI_Card_Navy", (0.05, 0.08, 0.14), strength=1.0)
MAT_CARD_BORDER = make_emissive_mat("UI_Card_Border", (0.28, 0.62, 0.92), strength=1.4)
MAT_CARD_TEXT = make_emissive_mat("UI_Card_Text", (0.98, 0.98, 0.99), strength=1.2)
MAT_CARD_SUBTEXT = make_emissive_mat("UI_Card_SubText", (0.75, 0.82, 0.90), strength=1.1)
MAT_CARD_POINTER = make_emissive_mat("UI_Pointer_Line", (0.35, 0.70, 0.95), strength=1.3)

MAT_ACCENT_DC = make_emissive_mat("UI_Accent_DC", (0.98, 0.15, 0.08), strength=1.5)
MAT_ACCENT_AC = make_emissive_mat("UI_Accent_AC", (1.0, 0.52, 0.05), strength=1.5)
MAT_ACCENT_DATA = make_emissive_mat("UI_Accent_Data", (0.1, 0.92, 0.25), strength=1.5)
MAT_ACCENT_GRID = make_emissive_mat("UI_Accent_Grid", (0.85, 0.90, 0.98), strength=1.5)

# Architectural Plaster & Window Shaders
mat_plaster = bpy.data.materials.get("HITAM_Plaster")
if mat_plaster and mat_plaster.use_nodes:
    bs = mat_plaster.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value = (0.78, 0.60, 0.42, 1.0) # Warm sandstone
        bs.inputs["Roughness"].default_value = 0.72

mat_terra = bpy.data.materials.get("HITAM_Terracotta")
if mat_terra and mat_terra.use_nodes:
    bs = mat_terra.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value = (0.48, 0.14, 0.07, 1.0) # Rich terracotta

mat_grass = bpy.data.materials.get("Campus_Lawn")
if mat_grass and mat_grass.use_nodes:
    bs = mat_grass.node_tree.nodes.get("Principled BSDF")
    if bs:
        bs.inputs["Base Color"].default_value = (0.06, 0.18, 0.04, 1.0) # Rich lawn green

COL_UI = bpy.data.collections.get("CAMPUS_UI_SYSTEM")
if not COL_UI:
    COL_UI = bpy.data.collections.new("CAMPUS_UI_SYSTEM")
    SCENE.collection.children.link(COL_UI)

def link_ui(ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    COL_UI.objects.link(ob)
    return ob

# ---------------------------------------------------------------------------
# Rebuild UI System with Proportional Presentation Sizes
# ---------------------------------------------------------------------------
def clear_ui():
    for ob in list(COL_UI.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

clear_ui()

def make_box(name, loc, size, mat, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.scale = size
    if mat:
        ob.data.materials.append(mat)
    if bevel > 0.0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
    return link_ui(ob)

def build_card(name, loc, size, border_thick=0.06):
    # Border backing
    b_ob = make_box(f"{name}_Border", loc, (size[0] + border_thick*2, size[1] + border_thick*2, size[2]), MAT_CARD_BORDER, bevel=0.03)
    # Dark navy face
    f_ob = make_box(f"{name}_Face", (0, 0, 0.015), size, MAT_CARD_BG, bevel=0.02)
    f_ob.parent = b_ob
    return b_ob

def add_text(name, parent_card, body, local_xy, size=0.28, mat=MAT_CARD_TEXT, align="LEFT"):
    t_data = bpy.data.curves.new(name, "FONT")
    t_data.body = body
    t_data.size = size
    t_data.align_x = align
    t_data.align_y = "CENTER"
    t_data.extrude = 0.005
    t_ob = bpy.data.objects.new(name, t_data)
    t_ob.data.materials.append(mat)
    link_ui(t_ob)
    t_ob.parent = parent_card
    t_ob.location = (local_xy[0], local_xy[1], 0.03)
    return t_ob

def build_pointer(name, start_pt, end_pt):
    c_data = bpy.data.curves.new(name, "CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.02
    spline = c_data.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (*start_pt, 1.0)
    spline.points[1].co = (*end_pt, 1.0)
    p_ob = bpy.data.objects.new(name, c_data)
    p_ob.data.materials.append(MAT_CARD_POINTER)
    return link_ui(p_ob)

print("Building callout cards with pointers...")

# 1. Solar Panels Callout Card
# Rooftop array is at (-3.5, 12.8, 5.8)
card_solar = build_card("Card_Solar", (-3.5, 15.6, 6.6), (3.6, 1.0, 0.04))
add_text("Txt_Solar_Title", card_solar, "SOLAR PANELS", (-1.6, 0.22), 0.26, MAT_CARD_TEXT)
add_text("Txt_Solar_Sub", card_solar, "ROOFTOP PV ARRAY", (-1.6, -0.20), 0.19, MAT_CARD_SUBTEXT)
build_pointer("Ptr_Solar", (-3.5, 15.0, 6.6), (-3.5, 13.5, 5.8))

# 2. Control Unit (ESP32) Callout Card
# Control unit is at (-9.2, 1.8, 0.3)
card_ctrl = build_card("Card_Control", (-12.8, 1.8, 1.8), (3.8, 1.0, 0.04))
add_text("Txt_Ctrl_Title", card_ctrl, "CONTROL UNIT", (-1.7, 0.22), 0.26, MAT_CARD_TEXT)
add_text("Txt_Ctrl_Sub", card_ctrl, "ESP32 MCU • MPPT SENSING", (-1.7, -0.20), 0.18, MAT_CARD_SUBTEXT)
build_pointer("Ptr_Control", (-10.8, 1.8, 1.8), (-9.5, 1.8, 0.6))

# 3. Relay / Switching Unit Callout Card
# Relay unit is at (-7.6, 1.8, 0.3)
card_relay = build_card("Card_Relay", (-7.6, -1.2, 1.6), (4.0, 1.0, 0.04))
add_text("Txt_Relay_Title", card_relay, "RELAY / SWITCHING UNIT", (-1.8, 0.22), 0.25, MAT_CARD_TEXT)
add_text("Txt_Relay_Sub", card_relay, "4-CHANNEL PRIORITY MATRIX", (-1.8, -0.20), 0.18, MAT_CARD_SUBTEXT)
build_pointer("Ptr_Relay", (-7.6, -0.6, 1.6), (-7.6, 1.2, 0.6))

# 4. Utility Grid Callout Card
# Transformer / Pole is at (15.5, -14.5, 4.5)
card_grid = build_card("Card_Grid", (15.5, -10.8, 4.2), (3.6, 1.0, 0.04))
add_text("Txt_Grid_Title", card_grid, "UTILITY GRID", (-1.6, 0.22), 0.26, MAT_CARD_TEXT)
add_text("Txt_Grid_Sub", card_grid, "11kV / 415V TRANSFORMER", (-1.6, -0.20), 0.18, MAT_CARD_SUBTEXT)
build_pointer("Ptr_Grid", (15.5, -11.4, 4.2), (15.5, -14.0, 4.5))

# ---------------------------------------------------------------------------
# Dashboard HUD & Legend Cards
# ---------------------------------------------------------------------------
# Top-Left Scenario Banner Card
card_banner = build_card("Card_HUD_Scenario", (-16.0, 15.5, 2.0), (8.6, 1.8, 0.04))
add_text("HUD_Scen_Header", card_banner, "VOLT VISION  |  SMART MICROGRID", (-4.0, 0.45), 0.28, MAT_CARD_BORDER)
add_text("HUD_Scenario_Subtitle", card_banner, "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY", (-4.0, -0.05), 0.30, MAT_CARD_TEXT)
add_text("HUD_Scen_Footer", card_banner, "HITAM CAMPUS REAL-TIME ENERGY BALANCING", (-4.0, -0.52), 0.19, MAT_CARD_SUBTEXT)

# Top-Right Metrics Dashboard Card
card_metrics = build_card("Card_HUD_Metrics", (15.5, 14.5, 2.0), (8.8, 3.8, 0.04))
add_text("HUD_Met_Title", card_metrics, "POWER METRICS & LOAD STATUS", (-4.1, 1.45), 0.26, MAT_CARD_BORDER)
add_text("HUD_Met_Line_Solar", card_metrics, "SOLAR GEN   : 10.0 kW  (48V / 208A) [PEAK]", (-4.1, 0.85), 0.26, MAT_ACCENT_DC)
add_text("HUD_Met_Line_Load", card_metrics, "CAMPUS LOAD :  8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]", (-4.1, 0.25), 0.25, MAT_ACCENT_AC)
add_text("HUD_Met_Line_Net", card_metrics, "NET BALANCE : +1.5 kW  [100% SELF-SUSTAINING]", (-4.1, -0.35), 0.25, MAT_ACCENT_DATA)
add_text("HUD_Met_Line_Grid", card_metrics, "GRID IMPORT :  0.0 kW  [STANDBY IDLE]", (-4.1, -0.95), 0.25, MAT_ACCENT_GRID)
add_text("HUD_Met_Line_Relay", card_metrics, "RELAYS      : R1[ON]  R2[ON]  R3[ON]", (-4.1, -1.50), 0.24, MAT_CARD_TEXT)

# Bottom-Right Color-Key Legend Card
card_legend = build_card("Card_HUD_Legend", (16.0, -6.5, 2.0), (7.0, 3.2, 0.04))
add_text("HUD_Leg_Title", card_legend, "CIRCUIT COLOR LEGEND", (-3.2, 1.15), 0.26, MAT_CARD_BORDER)

# Legend Items with Swatches
def add_legend_row(parent, tag, color_mat, label, y_off):
    # accent color pill
    pill = make_box(f"Swatch_{tag}", (-2.8, y_off, 0.03), (0.45, 0.10, 0.02), color_mat)
    pill.parent = parent
    add_text(f"Lbl_{tag}", parent, label, (-2.4, y_off), 0.22, MAT_CARD_TEXT)

add_legend_row(card_legend, "DC", MAT_ACCENT_DC, "DC Power (Solar PV String)", 0.60)
add_legend_row(card_legend, "AC", MAT_ACCENT_AC, "AC Power (Campus Distribution)", 0.10)
add_legend_row(card_legend, "Data", MAT_ACCENT_DATA, "Sensor / Data Feedback (ESP32)", -0.40)
add_legend_row(card_legend, "Grid", MAT_ACCENT_GRID, "Utility Grid Connection (11kV)", -0.90)

# ---------------------------------------------------------------------------
# Cameras Setup & Billboard Alignment
# ---------------------------------------------------------------------------
# 1. Top Down Camera
cam_top = bpy.data.objects.get("CAM_TOP_DOWN")
if not cam_top:
    c_data = bpy.data.cameras.new("CAM_TOP_DOWN")
    cam_top = bpy.data.objects.new("CAM_TOP_DOWN", c_data)
    SCENE.collection.objects.link(cam_top)

cam_top.location = (0.0, -0.5, 58.0)
cam_top.rotation_euler = (0.0, 0.0, 0.0) # True vertical aerial view
cam_top.data.lens = 32
cam_top.data.clip_end = 500

# 2. Angled 3/4 Aerial View (matching reference photo)
cam_ang = bpy.data.objects.get("CAM_ANGLED_VIEW")
if not cam_ang:
    c_data = bpy.data.cameras.new("CAM_ANGLED_VIEW")
    cam_ang = bpy.data.objects.new("CAM_ANGLED_VIEW", c_data)
    SCENE.collection.objects.link(cam_ang)

cam_ang.location = (25.0, -32.0, 24.0)
target = Vector((0.0, 6.0, 2.5))
cam_ang.rotation_euler = (target - Vector(cam_ang.location)).to_track_quat("-Z", "Y").to_euler()
cam_ang.data.lens = 34
cam_ang.data.clip_end = 500

# Function to align cards to camera orientation
def align_cards_to_cam(cam):
    all_cards = [
        card_solar, card_ctrl, card_relay, card_grid,
        card_banner, card_metrics, card_legend
    ]
    if cam.name == "CAM_TOP_DOWN":
        for c in all_cards:
            c.rotation_euler = (0, 0, 0)
    elif cam.name == "CAM_ANGLED_VIEW":
        # Orient cards to match angled camera view angle
        rot = cam.rotation_euler
        for c in all_cards:
            c.rotation_euler = rot

align_cards_to_cam(cam_top)
SCENE.camera = cam_top

bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
print("UI system rebuild complete and saved.")
