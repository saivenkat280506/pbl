"""Volt Vision v2 — Hardware Unit Upgrade Script.

Replaces the placeholder control unit boxes in the Volt Vision simulation with
two detailed, labeled hardware representations matching the real equipment:

ASSET 1: MAIN CONTROL ENCLOSURE (at X=-9.2, Y=1.8)
  - Waterproof electrical enclosure with transparent lid / open-top
  - ESP32 MCU development board (center) with RF shield, antenna, micro-USB
  - 16x2 LCD Display (top-right) with live telemetry readout:
    "Solar: 48V 208A", "Load: 8.5 kW", "Grid: OFF [Auto]"
  - Current Sensor module (top-left) with toroidal sensor
  - Voltage Sensor module (mid-left) with terminal blocks
  - Power Supply Unit (bottom-left) with perforated metal cage & caution decal
  - Solar Measurement Sensor (mid-right) with precision shunt
  - Environmental Sensor (below solar sensor) with slotted sensor housing
  - 4-Channel Relay Bank (bottom-right) with 4 blue Songle relay cubes
  - Four external cable glands at bottom:
    "Solar Input", "Battery Input", "AC Load Output", "Grid Input"
  - Exterior status LEDs: Green (Active) and Red (Fault)

ASSET 2: INVERTER + MPPT UNIT (at X=-7.6, Y=1.8)
  - Commercial solar string inverter (Fronius/Huawei style)
  - Sleek chamfered white front housing with satin finish
  - Dark charcoal rear heatsink with side cooling ventilation slats
  - Vivid green horizontal accent stripe across lower face
  - Central display window with blue telemetry screen and 4 control buttons
  - DC input connector on left (connected to Solar DC PV line)
  - AC output connector on right (connected to AC campus distribution line)
  - Data / RS485 communication port (connected to cyan line from ESP32)
  - Modest proportions mounted on dual steel stanchions on concrete pad
  - Floating specs tag listing key functions:
    • MPPT Control
    • DC to AC Conversion
    • Synchronizes with Grid
    • Power Quality Control

CIRCUIT WIRING & LABELS:
  - Wire_DC terminates at Inverter DC input
  - Wire_AC originates from Inverter AC output
  - Wire_Cyan connects Control Unit to Inverter with "ESP32 MCU • MPPT SENSING" label
  - Properly scaled dark-navy callout cards using Empty roots:
    - "Control Unit — ESP32"
    - "Inverter + MPPT Unit"
  - All existing HUD overlays, campus buildings, and circuit legend preserved.
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

# Open the working file
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
SCENE = bpy.context.scene

# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------
def get_or_create_col(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or SCENE.collection).children.link(c)
    return c

COL_EQUIPMENT = get_or_create_col("CAMPUS_EQUIPMENT")
COL_CIRCUITS  = get_or_create_col("CAMPUS_CIRCUITS")
COL_UI        = get_or_create_col("CAMPUS_UI_SYSTEM")

def link_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def get_mat(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0,
            emit=None, emit_str=1.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1.0)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bs.inputs["Alpha"].default_value = alpha
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
        if hasattr(m, "surface_render_method"):
            try:
                m.surface_render_method = "BLENDED"
            except Exception:
                pass
    if emit:
        bs.inputs["Emission Color"].default_value = (*emit, 1.0)
        bs.inputs["Emission Strength"].default_value = emit_str
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return m

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

# Hardware materials
MAT_ENCLOSURE_BODY = get_mat("HW_Enclosure_Body", (0.76, 0.77, 0.79), rough=0.45, metal=0.10)
MAT_ENCLOSURE_BACK = get_mat("HW_Enclosure_Back", (0.22, 0.23, 0.26), rough=0.70)
MAT_ENCLOSURE_LID  = get_mat("HW_Enclosure_Lid",  (0.88, 0.92, 0.96), rough=0.08, alpha=0.25, metal=0.05)
MAT_STANDOFF_METAL = get_mat("HW_Standoff_Metal", (0.80, 0.80, 0.82), rough=0.25, metal=0.90)

MAT_PCB_GREEN      = get_mat("HW_PCB_Green",      (0.04, 0.32, 0.08), rough=0.65)
MAT_PCB_BLUE       = get_mat("HW_PCB_Blue",       (0.06, 0.14, 0.48), rough=0.60)
MAT_PCB_TEAL       = get_mat("HW_PCB_Teal",       (0.05, 0.38, 0.36), rough=0.60)
MAT_CHIP_BLACK     = get_mat("HW_Chip_Black",     (0.05, 0.05, 0.06), rough=0.35, metal=0.20)
MAT_RF_SHIELD      = get_mat("HW_RF_Shield",      (0.80, 0.80, 0.83), rough=0.25, metal=0.85)

MAT_LCD_BEZEL      = get_mat("HW_LCD_Bezel",      (0.06, 0.06, 0.08), rough=0.35, metal=0.25)
MAT_LCD_BACKLIGHT  = get_emissive("HW_LCD_Glow",  (0.45, 0.88, 0.15), strength=2.2)
MAT_LCD_TEXT       = get_mat("HW_LCD_Text",       (0.02, 0.08, 0.02), rough=0.30)

MAT_RELAY_BLUE     = get_mat("HW_Relay_Songle",   (0.08, 0.22, 0.72), rough=0.45)
MAT_TERMINAL_GREEN = get_mat("HW_Terminal_Green", (0.08, 0.55, 0.18), rough=0.55)
MAT_TERMINAL_BLUE  = get_mat("HW_Terminal_Blue",  (0.08, 0.35, 0.75), rough=0.55)

MAT_PSU_CASE       = get_mat("HW_PSU_Case",       (0.75, 0.65, 0.25), rough=0.40, metal=0.75)
MAT_PSU_PERF       = get_mat("HW_PSU_Perf",       (0.35, 0.34, 0.32), rough=0.55, metal=0.60)
MAT_CAUTION_YELLOW = get_emissive("HW_Caution",   (0.95, 0.85, 0.05), strength=2.0)

MAT_SENSOR_TOROID  = get_mat("HW_Sensor_Toroid",  (0.06, 0.28, 0.65), rough=0.50)
MAT_SENSOR_DHT     = get_mat("HW_Sensor_DHT",     (0.20, 0.68, 0.88), rough=0.40)

MAT_CABLE_GLAND    = get_mat("HW_CableGland",     (0.10, 0.10, 0.12), rough=0.35, metal=0.50)
MAT_CONCRETE_PAD   = get_mat("HW_ConcretePad",    (0.50, 0.48, 0.44), rough=0.85)
MAT_POLE_STEEL     = get_mat("HW_PoleSteel",      (0.40, 0.42, 0.45), rough=0.30, metal=0.85)

MAT_WIRE_RED       = get_mat("HW_Wire_Red",       (0.90, 0.08, 0.05), rough=0.40)
MAT_WIRE_BLUE      = get_mat("HW_Wire_Blue",      (0.06, 0.20, 0.85), rough=0.40)
MAT_WIRE_YELLOW    = get_mat("HW_Wire_Yellow",    (0.92, 0.80, 0.05), rough=0.40)
MAT_WIRE_BLACK     = get_mat("HW_Wire_Black",     (0.08, 0.08, 0.09), rough=0.45)

MAT_LED_GREEN      = get_emissive("HW_LED_Active",(0.08, 1.0, 0.15), strength=6.0)
MAT_LED_RED        = get_emissive("HW_LED_Fault", (1.0, 0.06, 0.05), strength=4.0)

# Inverter materials
MAT_INV_WHITE      = get_mat("HW_Inv_White",      (0.92, 0.92, 0.93), rough=0.35, metal=0.08)
MAT_INV_CHARCOAL   = get_mat("HW_Inv_Charcoal",   (0.12, 0.12, 0.14), rough=0.45, metal=0.35)
MAT_INV_STRIPE     = get_emissive("HW_Inv_Stripe",(0.12, 0.88, 0.22), strength=2.2)
MAT_INV_SCREEN     = get_emissive("HW_Inv_Screen",(0.12, 0.50, 0.95), strength=2.0)

# UI / Card materials (matching existing scene exactly)
MAT_CARD_BG        = get_emissive("UI_Card_Navy",     (0.05, 0.08, 0.14), strength=1.0)
MAT_CARD_BORDER    = get_emissive("UI_Card_Border",   (0.28, 0.60, 0.90), strength=1.4)
MAT_CARD_TEXT      = get_emissive("UI_Card_Text",     (0.98, 0.98, 0.99), strength=1.2)
MAT_CARD_SUB       = get_emissive("UI_Card_SubText",  (0.75, 0.82, 0.92), strength=1.0)
MAT_CARD_PTR       = get_emissive("UI_Pointer_Line",  (0.35, 0.68, 0.95), strength=1.4)

# Circuit wires
MAT_WIRE_DC   = get_emissive("Mat_Wire_DC",   (1.0, 0.15, 0.05), strength=3.0)
MAT_WIRE_AC   = get_emissive("Mat_Wire_AC",   (1.0, 0.52, 0.05), strength=3.0)
MAT_WIRE_DATA = get_emissive("Mat_Wire_Data", (0.08, 0.92, 0.25), strength=2.6)
MAT_WIRE_GRID = get_emissive("Mat_Wire_Grid", (0.82, 0.90, 0.98), strength=1.2)
MAT_WIRE_CYAN = get_emissive("Mat_Wire_Cyan", (0.10, 0.85, 0.90), strength=2.8)

# ---------------------------------------------------------------------------
# Mesh creation helpers
# ---------------------------------------------------------------------------
def make_box(name, loc, size, mat, col=COL_EQUIPMENT, bevel=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.scale = size
    ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    if bevel > 0.0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
    return link_to(ob, col)

def make_cyl(name, loc, radius, depth, mat, col=COL_EQUIPMENT, verts=16, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return link_to(ob, col)

# ---------------------------------------------------------------------------
# UI Helpers using EMPTY ROOT (Zero scale multiplication bug!)
# ---------------------------------------------------------------------------
def make_card(name, loc, size_xy, border=0.06):
    """Creates a card using an Empty root so scale is NOT multiplied to children."""
    # Clean previous instances
    for suffix in ["", "_Border", "_Face"]:
        old = bpy.data.objects.get(f"{name}{suffix}")
        if old:
            bpy.data.objects.remove(old, do_unlink=True)

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
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
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
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
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

def add_label_3d(name, loc, text, font_size=0.14, mat=MAT_CARD_TEXT, align="CENTER"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    t_data = bpy.data.curves.new(name, "FONT")
    t_data.body = text
    t_data.size = font_size
    t_data.align_x = align
    t_data.align_y = "CENTER"
    t_data.extrude = 0.005
    t_ob = bpy.data.objects.new(name, t_data)
    t_ob.location = loc
    t_ob.data.materials.append(mat)
    try:
        t_ob.visible_shadow = False
    except Exception:
        pass
    return link_to(t_ob, COL_UI)

# ---------------------------------------------------------------------------
# STEP 0 — Remove Old Placeholder Objects & Stale Upgrades
# ---------------------------------------------------------------------------
def remove_old_placeholders():
    print("Cleaning placeholder and previous hardware objects...")
    prefixes = [
        "Control_ESP32", "Relay_Module_1", "Control_Post", "Relay_Post",
        "Control_Terminal", "Relay_Terminal", "Relay_Contactor", "Relay_InternalWire",
        "Control_LED", "Relay_LED", "Relay_Unit",
        "HW_Ctrl_", "HW_Inv_", "HW_MPPT_", "HW_Lbl_",
        "Card_Callout_", "Pointer_Callout_", "Txt_Callout_",
    ]
    exact = [
        "Card_Control", "Card_Control_Border", "Card_Control_Face",
        "Card_Relay", "Card_Relay_Border", "Card_Relay_Face",
        "Ptr_Control", "Ptr_Relay", "Txt_Ctrl_T", "Txt_Ctrl_S",
        "Txt_Relay_T", "Txt_Relay_S",
        "Wire_Cyan_Ctrl_MPPT",
    ]
    to_delete = []
    for ob in bpy.data.objects:
        if ob.name in exact:
            to_delete.append(ob)
        elif any(ob.name.startswith(p) for p in prefixes):
            to_delete.append(ob)
    for ob in to_delete:
        bpy.data.objects.remove(ob, do_unlink=True)
    print(f"  Removed {len(to_delete)} objects.")

# ---------------------------------------------------------------------------
# STEP 1 — Build Concrete Utility Equipment Pad
# ---------------------------------------------------------------------------
def build_utility_pad():
    # Spans both Asset 1 (-9.2) and Asset 2 (-7.6) with generous margin
    pad_cx = -8.4
    pad_cy = 1.8
    make_box("HW_Equipment_Pad", (pad_cx, pad_cy, 0.06),
             (3.8, 2.2, 0.12), MAT_CONCRETE_PAD, COL_EQUIPMENT, bevel=0.03)

# ---------------------------------------------------------------------------
# STEP 2 — Build ASSET 1: Main Control Enclosure (X = -9.2, Y = 1.8)
# ---------------------------------------------------------------------------
CTRL_X, CTRL_Y = -9.2, 1.8

def build_control_enclosure():
    print("Building ASSET 1: Main Control Enclosure...")

    # Dual mounting stanchions / legs
    for dx in (-0.45, 0.45):
        make_cyl(f"HW_Ctrl_Leg_{dx}", (CTRL_X + dx, CTRL_Y, 0.35),
                 0.045, 0.58, MAT_POLE_STEEL, COL_EQUIPMENT, 10)

    # --- Enclosure Box Shell ---
    # Width = 1.40m, Depth = 0.85m, Height = 0.42m
    # Base sits at Z = 0.65m. Walls extend up to Z = 1.07m.
    # Open-top with transparent lid allows complete visibility from CAM_TOP_DOWN and CAM_ANGLED_VIEW!
    BOX_W, BOX_D, BOX_H = 1.40, 0.85, 0.42
    base_z = 0.65
    mid_z  = base_z + BOX_H / 2

    # Bottom floor / base
    make_box("HW_Ctrl_Box_Bottom", (CTRL_X, CTRL_Y, base_z),
             (BOX_W, BOX_D, 0.04), MAT_ENCLOSURE_BODY, COL_EQUIPMENT, bevel=0.01)

    # Dark backplate inside where components mount
    make_box("HW_Ctrl_Backplate", (CTRL_X, CTRL_Y, base_z + 0.025),
             (BOX_W - 0.08, BOX_D - 0.08, 0.01), MAT_ENCLOSURE_BACK, COL_EQUIPMENT)

    # Outer perimeter walls (industrial grey enclosure rim)
    wall_thick = 0.035
    # North wall (+Y)
    make_box("HW_Ctrl_Wall_N", (CTRL_X, CTRL_Y + BOX_D/2 - wall_thick/2, mid_z),
             (BOX_W, wall_thick, BOX_H), MAT_ENCLOSURE_BODY, COL_EQUIPMENT)
    # South wall (-Y)
    make_box("HW_Ctrl_Wall_S", (CTRL_X, CTRL_Y - BOX_D/2 + wall_thick/2, mid_z),
             (BOX_W, wall_thick, BOX_H), MAT_ENCLOSURE_BODY, COL_EQUIPMENT)
    # West wall (-X)
    make_box("HW_Ctrl_Wall_W", (CTRL_X - BOX_W/2 + wall_thick/2, CTRL_Y, mid_z),
             (wall_thick, BOX_D, BOX_H), MAT_ENCLOSURE_BODY, COL_EQUIPMENT)
    # East wall (+X)
    make_box("HW_Ctrl_Wall_E", (CTRL_X + BOX_W/2 - wall_thick/2, CTRL_Y, mid_z),
             (wall_thick, BOX_D, BOX_H), MAT_ENCLOSURE_BODY, COL_EQUIPMENT)

    # Four corner metallic standoffs/screw mounts
    for cx in (-BOX_W/2 + 0.05, BOX_W/2 - 0.05):
        for cy in (-BOX_D/2 + 0.05, BOX_D/2 - 0.05):
            make_cyl(f"HW_Ctrl_Screw_{cx}_{cy}", (CTRL_X + cx, CTRL_Y + cy, base_z + BOX_H),
                     0.022, 0.04, MAT_STANDOFF_METAL, COL_EQUIPMENT, 8)

    # Open-top waterproof enclosure (as specified in requirements)
    # The interior components are directly visible and crystal clear without any glare
    old_lid = bpy.data.objects.get("HW_Ctrl_Lid")
    if old_lid:
        bpy.data.objects.remove(old_lid, do_unlink=True)

    # Component base height (resting right on backplate)
    cz = base_z + 0.04

    # -----------------------------------------------------------------------
    # Internal Components Layout (Ref 2 3x3 layout)
    #   Top-Left: Current Sensor | Center: ESP32 MCU | Top-Right: LCD Display
    #   Mid-Left: Voltage Sensor |                   | Mid-Right: Solar Sensor
    #   Btm-Left: PSU (12V/5V)   | Wiring trunk      | Below Mid: Env Sensor
    #                            |                   | Btm-Right: 4-Ch Relay Bank
    # -----------------------------------------------------------------------

    # 1. ESP32 MCU (Center, Top)
    esp_x, esp_y = CTRL_X, CTRL_Y + 0.12
    # Perfboard carrier
    make_box("HW_Ctrl_ESP32_Carrier", (esp_x, esp_y, cz + 0.015),
             (0.36, 0.28, 0.025), MAT_PSU_CASE, COL_EQUIPMENT, bevel=0.005)
    # ESP32 main black board
    make_box("HW_Ctrl_ESP32_PCB", (esp_x, esp_y, cz + 0.035),
             (0.26, 0.20, 0.02), MAT_PCB_GREEN, COL_EQUIPMENT, bevel=0.004)
    # Metal RF shield can (ESP-WROOM-32)
    make_box("HW_Ctrl_ESP32_Shield", (esp_x, esp_y + 0.04, cz + 0.055),
             (0.14, 0.10, 0.02), MAT_RF_SHIELD, COL_EQUIPMENT)
    # Antenna trace block (black top)
    make_box("HW_Ctrl_ESP32_Ant", (esp_x, esp_y + 0.085, cz + 0.05),
             (0.12, 0.03, 0.015), MAT_CHIP_BLACK, COL_EQUIPMENT)
    # Micro-USB port at bottom of ESP32
    make_box("HW_Ctrl_ESP32_USB", (esp_x, esp_y - 0.09, cz + 0.05),
             (0.05, 0.04, 0.018), MAT_STANDOFF_METAL, COL_EQUIPMENT)

    # 2. LCD Display 16x2 (Top-Right)
    lcd_x, lcd_y = CTRL_X + 0.42, CTRL_Y + 0.22
    # Green PCB substrate
    make_box("HW_Ctrl_LCD_PCB", (lcd_x, lcd_y, cz + 0.02),
             (0.48, 0.22, 0.02), MAT_PCB_GREEN, COL_EQUIPMENT, bevel=0.006)
    # Black bezel frame
    make_box("HW_Ctrl_LCD_Bezel", (lcd_x, lcd_y, cz + 0.04),
             (0.40, 0.16, 0.02), MAT_LCD_BEZEL, COL_EQUIPMENT, bevel=0.004)
    # Glowing screen surface
    make_box("HW_Ctrl_LCD_Screen", (lcd_x, lcd_y, cz + 0.052),
             (0.36, 0.12, 0.008), MAT_LCD_BACKLIGHT, COL_EQUIPMENT)
    # Live text readout on LCD screen
    add_label_3d("HW_Ctrl_LCD_Txt1", (lcd_x - 0.16, lcd_y + 0.025, cz + 0.06),
                 "Solar: 48V  208A", font_size=0.028, mat=MAT_LCD_TEXT, align="LEFT")
    add_label_3d("HW_Ctrl_LCD_Txt2", (lcd_x - 0.16, lcd_y - 0.025, cz + 0.06),
                 "Load: 8.5kW Grid:OFF", font_size=0.028, mat=MAT_LCD_TEXT, align="LEFT")

    # 3. Current Sensor (Top-Left, AC load current)
    cs_x, cs_y = CTRL_X - 0.44, CTRL_Y + 0.25
    make_box("HW_Ctrl_Current_PCB", (cs_x, cs_y, cz + 0.02),
             (0.24, 0.16, 0.02), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.005)
    # Blue toroidal current transformer / sensor block
    make_cyl("HW_Ctrl_Current_Toroid", (cs_x - 0.04, cs_y, cz + 0.05),
             0.045, 0.04, MAT_SENSOR_TOROID, COL_EQUIPMENT, 12)
    # Terminal block (green)
    make_box("HW_Ctrl_Current_Term", (cs_x + 0.06, cs_y, cz + 0.04),
             (0.06, 0.08, 0.03), MAT_TERMINAL_GREEN, COL_EQUIPMENT)

    # 4. Voltage Sensor (Mid-Left, grid/solar voltage)
    vs_x, vs_y = CTRL_X - 0.44, CTRL_Y + 0.05
    make_box("HW_Ctrl_Voltage_PCB", (vs_x, vs_y, cz + 0.02),
             (0.22, 0.18, 0.02), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.005)
    # 3-pin green screw terminals
    make_box("HW_Ctrl_Voltage_Term", (vs_x - 0.06, vs_y, cz + 0.04),
             (0.05, 0.12, 0.03), MAT_TERMINAL_GREEN, COL_EQUIPMENT)
    # Transformer / optocoupler chip
    make_box("HW_Ctrl_Voltage_Chip", (vs_x + 0.03, vs_y, cz + 0.035),
             (0.08, 0.08, 0.02), MAT_CHIP_BLACK, COL_EQUIPMENT)

    # 5. Power Supply Unit (Bottom-Left, 12V/5V DC)
    psu_x, psu_y = CTRL_X - 0.38, CTRL_Y - 0.20
    # Gold vented casing
    make_box("HW_Ctrl_PSU_Case", (psu_x, psu_y, cz + 0.06),
             (0.38, 0.24, 0.10), MAT_PSU_CASE, COL_EQUIPMENT, bevel=0.01)
    # Perforated top face
    make_box("HW_Ctrl_PSU_Perf", (psu_x - 0.04, psu_y, cz + 0.112),
             (0.24, 0.18, 0.008), MAT_PSU_PERF, COL_EQUIPMENT)
    # Yellow CAUTION triangle sticker
    make_box("HW_Ctrl_PSU_Caution", (psu_x - 0.04, psu_y, cz + 0.118),
             (0.08, 0.08, 0.004), MAT_CAUTION_YELLOW, COL_EQUIPMENT)

    # 6. Solar Measurement Sensor (Mid-Right, PV voltage & current)
    ss_x, ss_y = CTRL_X + 0.42, CTRL_Y + 0.06
    make_box("HW_Ctrl_Solar_PCB", (ss_x, ss_y, cz + 0.02),
             (0.28, 0.12, 0.02), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.004)
    # Blue terminal block
    make_box("HW_Ctrl_Solar_Term", (ss_x + 0.08, ss_y, cz + 0.035),
             (0.05, 0.08, 0.025), MAT_TERMINAL_BLUE, COL_EQUIPMENT)
    # INA219 / Shunt resistor chip
    make_box("HW_Ctrl_Solar_Shunt", (ss_x - 0.04, ss_y, cz + 0.032),
             (0.06, 0.04, 0.015), MAT_PSU_CASE, COL_EQUIPMENT)

    # 7. Environmental Sensor (Below Solar Sensor, temperature/irradiance)
    es_x, es_y = CTRL_X + 0.42, CTRL_Y - 0.08
    make_box("HW_Ctrl_Env_PCB", (es_x, es_y, cz + 0.02),
             (0.26, 0.12, 0.02), MAT_PCB_GREEN, COL_EQUIPMENT, bevel=0.004)
    # Light blue slotted DHT/sensor module
    make_box("HW_Ctrl_Env_DHT", (es_x + 0.04, es_y, cz + 0.04),
             (0.09, 0.08, 0.03), MAT_SENSOR_DHT, COL_EQUIPMENT, bevel=0.004)
    # Sensor IC
    make_box("HW_Ctrl_Env_IC", (es_x - 0.06, es_y, cz + 0.03),
             (0.04, 0.04, 0.015), MAT_CHIP_BLACK, COL_EQUIPMENT)

    # 8. 4-Channel Relay Bank (Bottom-Right, controls load priority)
    rl_x, rl_y = CTRL_X + 0.36, CTRL_Y - 0.25
    # Blue carrier PCB
    make_box("HW_Ctrl_Relay_PCB", (rl_x, rl_y, cz + 0.02),
             (0.44, 0.18, 0.02), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.005)
    # Four Songle blue relay cubes
    for ri in range(4):
        rx = rl_x - 0.15 + ri * 0.10
        make_box(f"HW_Ctrl_Relay_Cube_{ri}", (rx, rl_y, cz + 0.055),
                 (0.08, 0.11, 0.05), MAT_RELAY_BLUE, COL_EQUIPMENT, bevel=0.004)
    # Green screw terminals at south edge
    make_box("HW_Ctrl_Relay_Term_S", (rl_x, rl_y - 0.065, cz + 0.035),
             (0.38, 0.035, 0.025), MAT_TERMINAL_GREEN, COL_EQUIPMENT)
    # Terminal block at north edge
    make_box("HW_Ctrl_Relay_Term_N", (rl_x, rl_y + 0.065, cz + 0.035),
             (0.38, 0.035, 0.025), MAT_TERMINAL_GREEN, COL_EQUIPMENT)

    # 9. Internal Wiring Traces / Bundles
    def make_internal_wire(name, pts, mat):
        c_data = bpy.data.curves.new(name, "CURVE")
        c_data.dimensions = "3D"
        c_data.bevel_depth = 0.007
        c_data.bevel_resolution = 2
        spline = c_data.splines.new("BEZIER")
        spline.bezier_points.add(len(pts) - 1)
        for i, pt in enumerate(pts):
            bp = spline.bezier_points[i]
            bp.co = Vector(pt)
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
        w_ob = bpy.data.objects.new(name, c_data)
        w_ob.data.materials.append(mat)
        return link_to(w_ob, COL_EQUIPMENT)

    # Red power wire: PSU -> ESP32
    make_internal_wire("HW_Ctrl_Wire_Power",
                       [(psu_x + 0.12, psu_y, cz + 0.06),
                        (CTRL_X - 0.10, CTRL_Y - 0.05, cz + 0.03),
                        (esp_x - 0.08, esp_y - 0.06, cz + 0.04)], MAT_WIRE_RED)
    # Blue signal wire: Current/Voltage sensors -> ESP32
    make_internal_wire("HW_Ctrl_Wire_Sensors",
                       [(cs_x + 0.08, cs_y, cz + 0.03),
                        (vs_x + 0.08, vs_y, cz + 0.03),
                        (esp_x - 0.10, esp_y, cz + 0.04)], MAT_WIRE_BLUE)
    # Yellow I2C wire: ESP32 -> LCD
    make_internal_wire("HW_Ctrl_Wire_LCD",
                       [(esp_x + 0.10, esp_y, cz + 0.04),
                        (lcd_x - 0.18, lcd_y, cz + 0.03)], MAT_WIRE_YELLOW)
    # Yellow/Orange control wire: ESP32 -> Relay bank
    make_internal_wire("HW_Ctrl_Wire_Relays",
                       [(esp_x + 0.04, esp_y - 0.08, cz + 0.03),
                        (rl_x - 0.10, rl_y + 0.06, cz + 0.03)], MAT_WIRE_YELLOW)

    # 10. Four External Cable Glands at Base (South edge)
    glands = [
        ("Solar Input",     -0.42, MAT_WIRE_RED),
        ("Battery Input",   -0.14, MAT_WIRE_RED),
        ("AC Load Output",   0.14, MAT_WIRE_BLACK),
        ("Grid Input",       0.42, MAT_WIRE_BLUE),
    ]
    gland_y = CTRL_Y - BOX_D / 2 - 0.04
    gland_z = base_z + BOX_H * 0.35

    for gi, (lbl, dx, w_mat) in enumerate(glands):
        gx = CTRL_X + dx
        # Threaded gland nut
        make_cyl(f"HW_Ctrl_Gland_{gi}", (gx, gland_y, gland_z),
                 0.032, 0.07, MAT_CABLE_GLAND, COL_EQUIPMENT, 10,
                 rot=(math.pi / 2, 0, 0))
        # Wire stub coming out
        make_cyl(f"HW_Ctrl_GlandWire_{gi}", (gx, gland_y - 0.07, gland_z),
                 0.016, 0.10, w_mat, COL_EQUIPMENT, 8,
                 rot=(math.pi / 2, 0, 0))
        # Neat label below gland
        add_label_3d(f"HW_Ctrl_GlandLbl_{gi}",
                     (gx, gland_y - 0.16, gland_z - 0.06),
                     lbl, font_size=0.055, mat=MAT_CARD_SUB)

    # 11. Status LEDs on South Exterior Face
    led_y = CTRL_Y - BOX_D / 2 - 0.015
    led_z = base_z + BOX_H * 0.75
    # Green active LED
    make_cyl("HW_Ctrl_LED_Green", (CTRL_X - 0.10, led_y, led_z),
             0.022, 0.025, MAT_LED_GREEN, COL_EQUIPMENT, 10,
             rot=(math.pi / 2, 0, 0))
    # Red fault LED
    make_cyl("HW_Ctrl_LED_Red", (CTRL_X + 0.10, led_y, led_z),
             0.022, 0.025, MAT_LED_RED, COL_EQUIPMENT, 10,
             rot=(math.pi / 2, 0, 0))

    print("  ASSET 1: Main Control Enclosure built successfully.")

# ---------------------------------------------------------------------------
# STEP 3 — Build ASSET 2: Inverter + MPPT Unit (X = -7.6, Y = 1.8)
# ---------------------------------------------------------------------------
INV_X, INV_Y = -7.6, 1.8

def build_inverter_mppt_unit():
    print("Building ASSET 2: Inverter + MPPT Unit...")

    # Dual mounting stanchions / legs
    for dx in (-0.22, 0.22):
        make_cyl(f"HW_Inv_Leg_{dx}", (INV_X + dx, INV_Y, 0.35),
                 0.040, 0.58, MAT_POLE_STEEL, COL_EQUIPMENT, 10)

    # Inverter dimensions: Width = 0.85m, Depth = 0.32m, Height = 0.95m
    INV_W, INV_D, INV_H = 0.85, 0.32, 0.95
    base_z = 0.65
    mid_z  = base_z + INV_H / 2

    # 1. Dark charcoal rear heatsink chassis
    make_box("HW_Inv_RearChassis", (INV_X, INV_Y + 0.04, mid_z),
             (INV_W * 0.96, INV_D * 0.75, INV_H), MAT_INV_CHARCOAL, COL_EQUIPMENT, bevel=0.02)

    # Side ventilation louvers / cooling slats
    for vi in range(7):
        vz = base_z + 0.15 + vi * 0.11
        for side in (-1, 1):
            sx = INV_X + side * (INV_W * 0.48)
            make_box(f"HW_Inv_Vane_{side}_{vi}", (sx, INV_Y + 0.04, vz),
                     (0.015, INV_D * 0.55, 0.04), MAT_STANDOFF_METAL, COL_EQUIPMENT)

    # 2. Sleek white chamfered front casing
    make_box("HW_Inv_FrontCasing", (INV_X, INV_Y - 0.06, mid_z),
             (INV_W, INV_D * 0.45, INV_H), MAT_INV_WHITE, COL_EQUIPMENT, bevel=0.035)

    # Four decorative corner assembly bolts on front face
    for bx in (-INV_W/2 + 0.06, INV_W/2 - 0.06):
        for bz in (base_z + 0.06, base_z + INV_H - 0.06):
            make_cyl(f"HW_Inv_Bolt_{bx}_{bz}", (INV_X + bx, INV_Y - INV_D/2 - 0.005, bz),
                     0.012, 0.015, MAT_STANDOFF_METAL, COL_EQUIPMENT, 8,
                     rot=(math.pi / 2, 0, 0))

    # 3. Vivid green horizontal accent stripe (lower third, Ref 1)
    stripe_z = base_z + INV_H * 0.30
    make_box("HW_Inv_GreenStripe", (INV_X, INV_Y - INV_D/2 - 0.002, stripe_z),
             (INV_W * 0.92, 0.01, 0.028), MAT_INV_STRIPE, COL_EQUIPMENT)

    # 4. Central dark screen bezel module
    screen_z = base_z + INV_H * 0.70
    make_box("HW_Inv_ScreenBezel", (INV_X, INV_Y - INV_D/2 - 0.004, screen_z),
             (0.34, 0.015, 0.22), MAT_INV_CHARCOAL, COL_EQUIPMENT, bevel=0.01)

    # Glowing blue telemetry LCD screen
    make_box("HW_Inv_Screen", (INV_X, INV_Y - INV_D/2 - 0.012, screen_z + 0.03),
             (0.24, 0.008, 0.12), MAT_INV_SCREEN, COL_EQUIPMENT)

    # Four tactile buttons below screen
    for bi, bdx in enumerate((-0.075, -0.025, 0.025, 0.075)):
        make_cyl(f"HW_Inv_Btn_{bi}", (INV_X + bdx, INV_Y - INV_D/2 - 0.014, screen_z - 0.06),
                 0.014, 0.012, MAT_STANDOFF_METAL, COL_EQUIPMENT, 8,
                 rot=(math.pi / 2, 0, 0))

    # 5. Bottom cable connectors
    # DC Input (West side / left, connecting to Solar DC line)
    make_cyl("HW_Inv_DC_Gland", (INV_X - 0.22, INV_Y - 0.04, base_z - 0.04),
             0.030, 0.08, MAT_CABLE_GLAND, COL_EQUIPMENT, 10)
    # AC Output (East side / right, connecting to AC line)
    make_cyl("HW_Inv_AC_Gland", (INV_X + 0.22, INV_Y - 0.04, base_z - 0.04),
             0.030, 0.08, MAT_CABLE_GLAND, COL_EQUIPMENT, 10)
    # Data / RS485 communication port (Center top, connecting to cyan line)
    make_cyl("HW_Inv_Data_Port", (INV_X - 0.15, INV_Y, base_z + INV_H + 0.03),
             0.022, 0.06, MAT_CABLE_GLAND, COL_EQUIPMENT, 10)

    # 6. Floating Inverter Functions Specs Tag
    # Neatly positioned at X=-5.5, Y=1.8, Z=1.3 (open space to the right)
    tag_x, tag_y, tag_z = -5.5, 1.8, 1.3
    tag = make_card("Card_Inv_Specs", (tag_x, tag_y, tag_z), (2.6, 1.25), border=0.04)
    add_label(tag, "Txt_Inv_Spec_Title", "INVERTER & MPPT FUNCTIONS",
              (-1.18, 0.42), 0.16, MAT_CARD_BORDER)
    add_label(tag, "Txt_Inv_Spec_1", "• MPPT Solar Optimization",
              (-1.18, 0.18), 0.14, MAT_CARD_TEXT)
    add_label(tag, "Txt_Inv_Spec_2", "• High-Efficiency DC→AC Conversion",
              (-1.18, -0.04), 0.14, MAT_CARD_TEXT)
    add_label(tag, "Txt_Inv_Spec_3", "• Grid Sync & Islanding Protection",
              (-1.18, -0.26), 0.14, MAT_CARD_TEXT)
    add_label(tag, "Txt_Inv_Spec_4", "• Active Power Quality Control",
              (-1.18, -0.48), 0.14, MAT_CARD_TEXT)
    # Pointer from specs tag to Inverter unit
    add_pointer("Ptr_Inv_Specs", (tag_x - 1.35, tag_y, tag_z), (INV_X + 0.45, INV_Y, mid_z))

    print("  ASSET 2: Inverter + MPPT Unit built successfully.")

# ---------------------------------------------------------------------------
# STEP 4 — Update Circuit Wiring
# ---------------------------------------------------------------------------
def update_circuit_wiring():
    print("Updating circuit wiring for new hardware configuration...")

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

    # 1. DC Solar Line (Orange/Red)
    # PV Array -> West Roof Parapet -> Wall Conduit -> Ground Trench -> Inverter DC Input (-7.82, 1.76, 0.61)
    pts_dc = [
        (-3.5, 12.8, 6.05),
        (-6.5, 12.8, 6.00),
        (-8.4, 12.8, 6.00),
        (-8.8, 11.2, 5.10),
        (-8.8, 11.2, 2.50),
        (-8.8, 11.2, 0.40),
        (-8.4, 5.5, 0.40),
        (-8.2, 1.8, 0.45),
        (INV_X - 0.22, INV_Y - 0.04, 0.61),  # Into Inverter DC Input
    ]
    update_spline_curve("Wire_DC", pts_dc, MAT_WIRE_DC, 0.055)

    # 2. AC Distribution Line (Yellow/Orange)
    # Inverter AC Output (-7.38, 1.76, 0.61) -> Ground Trench -> Building Foundation -> Lab/Wing Loads
    pts_ac = [
        (INV_X + 0.22, INV_Y - 0.04, 0.61),  # Originates at Inverter AC Output
        (-7.4, 2.2, 0.40),
        (-7.6, 3.6, 0.35),
        (-6.2, 4.3, 0.35),
        (-3.0, 4.3, 0.35),
        (0.0, 5.2, 0.35),
        (3.5, 4.3, 0.35),
        (7.0, 4.3, 0.35),
    ]
    update_spline_curve("Wire_AC", pts_ac, MAT_WIRE_AC, 0.058)

    # 3. Sensor / Data Feedback Line (Green)
    # Roof PV Sensor tap -> Conduit -> Control Unit Sensor Port
    pts_data = [
        (-3.5, 13.0, 6.10),
        (-8.0, 13.0, 6.05),
        (-8.6, 11.0, 0.42),
        (-9.2, 2.6, 0.42),
        (CTRL_X, CTRL_Y + 0.40, 0.65),       # Into Control Unit Enclosure
    ]
    update_spline_curve("Wire_Data", pts_data, MAT_WIRE_DATA, 0.040)

    # 4. Grid Utility Line (Grey/White)
    # Grid Transformer -> Boundary Conduit -> Utility Area (Control/Inverter)
    pts_grid = [
        (15.8, -14.5, 5.20),
        (15.5, -14.5, 2.60),
        (15.0, -14.0, 0.38),
        (8.0, -14.0, 0.35),
        (0.0, -13.5, 0.35),
        (-7.5, -12.0, 0.35),
        (CTRL_X + 0.42, CTRL_Y - 0.46, 0.58), # Into Grid Input cable gland of Control Enclosure
    ]
    update_spline_curve("Wire_Grid", pts_grid, MAT_WIRE_GRID, 0.050)

    # 5. NEW: Cyan Line — ESP32 MCU • MPPT SENSING
    # Runs directly from Control Unit enclosure top to Inverter top!
    pts_cyan = [
        (CTRL_X + 0.20, CTRL_Y, 1.08),           # Exit top of Control Enclosure
        (CTRL_X + 0.20, CTRL_Y, 1.45),           # Rise up
        ((CTRL_X + INV_X)/2, CTRL_Y, 1.55),      # Arch center
        (INV_X - 0.15, INV_Y, 1.65),             # Arch into Inverter
        (INV_X - 0.15, INV_Y, 1.60),             # Inverter communication port
    ]
    w_cyan = update_spline_curve("Wire_Cyan_Ctrl_MPPT", pts_cyan, MAT_WIRE_CYAN, 0.038)
    try:
        w_cyan.visible_shadow = False
    except Exception:
        pass

    # Text label floating along the cyan line
    cyan_mid_x = (CTRL_X + INV_X) / 2
    add_label_3d("HW_Lbl_CyanLine", (cyan_mid_x, CTRL_Y, 1.72),
                 "ESP32 MCU • MPPT SENSING", font_size=0.10, mat=MAT_WIRE_CYAN)

    # Refresh animation pulse objects if they exist
    for key, cname in [("DC", "Wire_DC"), ("AC", "Wire_AC"),
                       ("Data", "Wire_Data"), ("Grid", "Wire_Grid")]:
        p = bpy.data.objects.get(f"FX_Pulse_{key}")
        w = bpy.data.objects.get(cname)
        if p and w:
            p.data = w.data

    print("  Circuit wiring updated successfully.")

# ---------------------------------------------------------------------------
# STEP 5 — Update Callout Cards (Proportional, Clean UI)
# ---------------------------------------------------------------------------
def update_callout_cards():
    print("Constructing proportional callout cards...")

    # 1. Asset 1: Control Unit — ESP32 Callout Card
    # Position: (-12.2, -0.6, 1.2) - south of pergola beam for full visibility
    card_ctrl = make_card("Card_Control", (-12.2, -0.6, 1.2), (3.8, 0.95))
    add_label(card_ctrl, "Txt_Ctrl_T", "CONTROL UNIT — ESP32", (-1.7, 0.20), 0.22, MAT_CARD_TEXT)
    add_label(card_ctrl, "Txt_Ctrl_S", "MCU • SENSORS • LCD • RELAY BANK", (-1.7, -0.18), 0.14, MAT_CARD_SUB)
    add_pointer("Ptr_Control", (-10.3, -0.2, 1.2), (CTRL_X - 0.2, CTRL_Y - 0.3, 0.85))

    # 2. Asset 2: Inverter + MPPT Unit Callout Card (replaces old Card_Relay)
    # Position: (-7.6, -1.2, 1.2)
    card_inv = make_card("Card_Inverter", (-7.6, -1.2, 1.2), (3.8, 0.95))
    add_label(card_inv, "Txt_Inv_T", "INVERTER + MPPT UNIT", (-1.7, 0.20), 0.22, MAT_CARD_TEXT)
    add_label(card_inv, "Txt_Inv_S", "DC→AC CONVERTER • GRID SYNC", (-1.7, -0.18), 0.15, MAT_CARD_SUB)
    add_pointer("Ptr_Inverter", (-7.6, -0.7, 1.2), (INV_X, INV_Y, 0.85))

    print("  Callout cards updated successfully.")

# ---------------------------------------------------------------------------
# STEP 6 — Save Blend File and Render Views
# ---------------------------------------------------------------------------
def render_views():
    print("Saving updated blend file...")
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Scene saved to {BLEND_PATH}")

    print("Configuring render settings for clean presentation...")
    SCENE.render.engine = "BLENDER_EEVEE"
    SCENE.render.resolution_x = 1920
    SCENE.render.resolution_y = 1080
    SCENE.render.resolution_percentage = 100

    # Ensure lighting and bloom
    if hasattr(SCENE.eevee, "use_bloom"):
        SCENE.eevee.use_bloom = True

    # Setup or update closeup camera for detailed inspection
    cam_close = bpy.data.objects.get("CAM_HARDWARE_CLOSEUP")
    if not cam_close:
        cd = bpy.data.cameras.new("CAM_HARDWARE_CLOSEUP")
        cd.lens = 42.0
        cam_close = bpy.data.objects.new("CAM_HARDWARE_CLOSEUP", cd)
        SCENE.collection.objects.link(cam_close)
    cam_close.location = (-8.4, -1.8, 3.4)
    cam_close.rotation_euler = (math.radians(64), 0, 0)

    views = [
        ("CAM_TOP_DOWN", os.path.join(OUT_DIR, "v5_top_down_hardware_upgrade.png")),
        ("CAM_ANGLED_VIEW", os.path.join(OUT_DIR, "v5_angled_hardware_upgrade.png")),
        ("CAM_HARDWARE_CLOSEUP", os.path.join(OUT_DIR, "v5_hardware_closeup.png")),
    ]

    for cam_name, out_path in views:
        cam_ob = bpy.data.objects.get(cam_name)
        if not cam_ob:
            print(f"Warning: Camera {cam_name} not found!")
            continue
        print(f"Rendering: {cam_name} -> {out_path}")
        SCENE.camera = cam_ob
        SCENE.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"  DONE: {out_path}")

    print("All renders completed successfully.")

# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("============================================================")
    print("  VOLT VISION — HARDWARE UNIT UPGRADE (V5 CLEAN)")
    print("============================================================")
    remove_old_placeholders()
    build_utility_pad()
    build_control_enclosure()
    build_inverter_mppt_unit()
    update_circuit_wiring()
    update_callout_cards()
    render_views()
    print("============================================================")
    print("  HARDWARE UPGRADE COMPLETE")
    print("============================================================")
