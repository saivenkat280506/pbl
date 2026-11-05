"""Perfected UI Card System for Volt Vision v2 in Blender 5.2.

Creates properly scaled, non-glare, solid dark-navy callout cards,
pointers, color-key legend, and scenario HUD for both CAM_TOP_DOWN and CAM_ANGLED_VIEW.
"""
import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
SCENE = bpy.context.scene

# Clean UI collection
COL_UI = bpy.data.collections.get("CAMPUS_UI_SYSTEM")
if not COL_UI:
    COL_UI = bpy.data.collections.new("CAMPUS_UI_SYSTEM")
    SCENE.collection.children.link(COL_UI)

for ob in list(COL_UI.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

# Emissive Materials (Solid Colors, Zero Glare)
def get_emissive(name, color, strength=1.0):
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

MAT_CARD_BG = get_emissive("UI_Card_Navy", (0.05, 0.08, 0.14), strength=1.0)       # Solid Dark Navy
MAT_CARD_BORDER = get_emissive("UI_Card_Border", (0.28, 0.60, 0.90), strength=1.4)  # Cyan Border
MAT_CARD_TEXT = get_emissive("UI_Card_Text", (0.98, 0.98, 0.99), strength=1.2)      # Crisp White
MAT_CARD_SUB = get_emissive("UI_Card_SubText", (0.75, 0.82, 0.92), strength=1.0)    # Light Slate
MAT_CARD_PTR = get_emissive("UI_Pointer_Line", (0.35, 0.68, 0.95), strength=1.4)    # Thin Cyan Line

MAT_ACCENT_DC = get_emissive("UI_Accent_DC", (0.98, 0.15, 0.08), strength=1.5)
MAT_ACCENT_AC = get_emissive("UI_Accent_AC", (1.0, 0.52, 0.05), strength=1.5)
MAT_ACCENT_DATA = get_emissive("UI_Accent_Data", (0.10, 0.92, 0.25), strength=1.5)
MAT_ACCENT_GRID = get_emissive("UI_Accent_Grid", (0.85, 0.90, 0.98), strength=1.5)

def make_card(name, loc, size_xy, border=0.06):
    """Creates a card using an Empty root so scale is NOT multiplied to children."""
    root = bpy.data.objects.new(name, None)
    root.location = loc
    root.scale = (1.0, 1.0, 1.0)
    COL_UI.objects.link(root)

    # Border backing mesh
    b_me = bpy.data.meshes.new(f"{name}_b_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(b_me)
    bm.free()
    b_ob = bpy.data.objects.new(f"{name}_Border", b_me)
    b_ob.scale = (size_xy[0] + border * 2, size_xy[1] + border * 2, 0.02)
    b_ob.data.materials.append(MAT_CARD_BORDER)
    b_ob.parent = root
    b_ob.location = (0, 0, 0)
    COL_UI.objects.link(b_ob)

    # Face mesh
    f_me = bpy.data.meshes.new(f"{name}_f_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(f_me)
    bm.free()
    f_ob = bpy.data.objects.new(f"{name}_Face", f_me)
    f_ob.scale = (size_xy[0], size_xy[1], 0.022)
    f_ob.data.materials.append(MAT_CARD_BG)
    f_ob.parent = root
    f_ob.location = (0, 0, 0.012)
    COL_UI.objects.link(f_ob)

    return root

def add_label(parent_root, name, text, local_xy, size=0.24, mat=MAT_CARD_TEXT, align="LEFT"):
    t_data = bpy.data.curves.new(name, "FONT")
    t_data.body = text
    t_data.size = size
    t_data.align_x = align
    t_data.align_y = "CENTER"
    t_data.extrude = 0.005
    t_ob = bpy.data.objects.new(name, t_data)
    t_ob.data.materials.append(mat)
    t_ob.parent = parent_root
    t_ob.location = (local_xy[0], local_xy[1], 0.025)
    COL_UI.objects.link(t_ob)
    return t_ob

def add_pointer(name, start_xyz, end_xyz):
    c_data = bpy.data.curves.new(name, "CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.018
    spline = c_data.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (*start_xyz, 1.0)
    spline.points[1].co = (*end_xyz, 1.0)
    p_ob = bpy.data.objects.new(name, c_data)
    p_ob.data.materials.append(MAT_CARD_PTR)
    COL_UI.objects.link(p_ob)
    return p_ob

print("Constructing properly scaled presentation cards...")

# 1. Solar Panels Callout Card
# Rooftop array at (-3.5, 12.8, 5.8)
card_solar = make_card("Card_Solar", (-3.5, 15.6, 6.2), (3.6, 0.9))
add_label(card_solar, "Txt_Solar_T", "SOLAR PANELS", (-1.6, 0.20), 0.24, MAT_CARD_TEXT)
add_label(card_solar, "Txt_Solar_S", "ROOFTOP PV ARRAY", (-1.6, -0.18), 0.17, MAT_CARD_SUB)
add_pointer("Ptr_Solar", (-3.5, 15.1, 6.2), (-3.5, 13.8, 5.8))

# 2. Control Unit (ESP32) Callout Card
# Control unit at (-9.2, 1.8, 0.3)
card_ctrl = make_card("Card_Control", (-12.8, 1.8, 1.2), (3.6, 0.9))
add_label(card_ctrl, "Txt_Ctrl_T", "CONTROL UNIT", (-1.6, 0.20), 0.24, MAT_CARD_TEXT)
add_label(card_ctrl, "Txt_Ctrl_S", "ESP32 MCU • SENSING", (-1.6, -0.18), 0.16, MAT_CARD_SUB)
add_pointer("Ptr_Control", (-11.0, 1.8, 1.2), (-9.5, 1.8, 0.5))

# 3. Relay / Switching Unit Callout Card
# Relay at (-7.6, 1.8, 0.3)
card_relay = make_card("Card_Relay", (-7.6, -1.2, 1.2), (3.8, 0.9))
add_label(card_relay, "Txt_Relay_T", "RELAY / SWITCHING UNIT", (-1.7, 0.20), 0.22, MAT_CARD_TEXT)
add_label(card_relay, "Txt_Relay_S", "4-CHANNEL PRIORITY MATRIX", (-1.7, -0.18), 0.16, MAT_CARD_SUB)
add_pointer("Ptr_Relay", (-7.6, -0.7, 1.2), (-7.6, 1.2, 0.5))

# 4. Utility Grid Callout Card
# Grid pole at (15.5, -14.5, 4.5)
card_grid = make_card("Card_Grid", (15.5, -11.0, 3.8), (3.6, 0.9))
add_label(card_grid, "Txt_Grid_T", "UTILITY GRID", (-1.6, 0.20), 0.24, MAT_CARD_TEXT)
add_label(card_grid, "Txt_Grid_S", "11kV / 415V TRANSFORMER", (-1.6, -0.18), 0.16, MAT_CARD_SUB)
add_pointer("Ptr_Grid", (15.5, -11.5, 3.8), (15.5, -14.0, 4.5))

# 5. Top-Left Campus Header Card
card_hdr = make_card("Card_Header", (-17.5, 15.5, 1.5), (8.2, 1.6))
add_label(card_hdr, "Txt_Hdr_Title", "HITAM COLLEGE", (-3.8, 0.40), 0.28, MAT_CARD_TEXT)
add_label(card_hdr, "Txt_Hdr_Sub", "SMART ENERGY MANAGEMENT SYSTEM", (-3.8, -0.05), 0.22, MAT_CARD_BORDER)
add_label(card_hdr, "Txt_Hdr_Foot", "PEOPLE | IDEAS | A GREENER TOMORROW", (-3.8, -0.48), 0.16, MAT_CARD_SUB)

# 6. Top-Right Scenario & Metrics Dashboard Card
card_metrics = make_card("Card_Metrics", (16.5, 14.5, 1.5), (9.4, 3.6))
add_label(card_metrics, "HUD_Scenario_Subtitle", "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY", (-4.4, 1.35), 0.25, MAT_CARD_BORDER)
add_label(card_metrics, "HUD_Met_Line_Solar", "SOLAR GEN   : 10.0 kW  (48V / 208A) [PEAK]", (-4.4, 0.80), 0.23, MAT_ACCENT_DC)
add_label(card_metrics, "HUD_Met_Line_Load", "CAMPUS LOAD :  8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]", (-4.4, 0.25), 0.22, MAT_ACCENT_AC)
add_label(card_metrics, "HUD_Met_Line_Net", "NET BALANCE : +1.5 kW  [100% SELF-SUSTAINING]", (-4.4, -0.30), 0.22, MAT_ACCENT_DATA)
add_label(card_metrics, "HUD_Met_Line_Grid", "GRID IMPORT :  0.0 kW  [STANDBY IDLE]", (-4.4, -0.85), 0.22, MAT_ACCENT_GRID)
add_label(card_metrics, "HUD_Met_Line_Relay", "RELAYS      : R1[ON]  R2[ON]  R3[ON]", (-4.4, -1.35), 0.21, MAT_CARD_TEXT)

# 7. Bottom-Right Color-Key Legend Card
card_legend = make_card("Card_Legend", (17.5, -6.5, 1.5), (7.0, 3.0))
add_label(card_legend, "Txt_Leg_Title", "CIRCUIT COLOR LEGEND", (-3.2, 1.05), 0.24, MAT_CARD_BORDER)

def add_swatch_row(parent, tag, mat, text, y_off):
    s_me = bpy.data.meshes.new(f"swatch_{tag}")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(s_me)
    bm.free()
    s_ob = bpy.data.objects.new(f"Swatch_{tag}", s_me)
    s_ob.scale = (0.50, 0.10, 0.02)
    s_ob.data.materials.append(mat)
    s_ob.parent = parent
    s_ob.location = (-2.7, y_off, 0.03)
    COL_UI.objects.link(s_ob)
    add_label(parent, f"Lbl_{tag}", text, (-2.3, y_off), 0.20, MAT_CARD_TEXT)

add_swatch_row(card_legend, "DC", MAT_ACCENT_DC, "DC Power (Solar PV String)", 0.55)
add_swatch_row(card_legend, "AC", MAT_ACCENT_AC, "AC Power (Campus Distribution)", 0.10)
add_swatch_row(card_legend, "Data", MAT_ACCENT_DATA, "Sensor / Data Feedback (ESP32)", -0.35)
add_swatch_row(card_legend, "Grid", MAT_ACCENT_GRID, "Utility Grid Connection (11kV)", -0.80)

# Save
bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
print("Updated VoltVision_v2_WORKING.blend with perfected card system.")
