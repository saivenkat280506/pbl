"""Volt Vision v2 — Hardware Unit Upgrade Script.

Replaces the two placeholder grey boxes ("Control Unit — ESP32" and the
semi-transparent MPPT junction box) with detailed, low-poly schematic
hardware representations that match the existing scene art style.

ASSET 1: Main Control Enclosure (open-top waterproof box with internal
         components: ESP32 MCU, LCD Display, Current/Voltage/Solar/
         Environmental Sensors, Relay Bank, PSU, cable glands, status LEDs).

ASSET 2: Inverter + MPPT Unit (wall/pole-mounted DC→AC converter sitting
         on the DC-to-AC transition point in the circuit).

All existing HUD overlays, buildings, trees, cameras, and circuit color
legend are preserved unchanged.
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
# Collection helpers
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
# Material helpers
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

# --- Hardware-specific materials ---
MAT_ENCLOSURE      = get_mat("HW_Enclosure",      (0.72, 0.72, 0.70), rough=0.55, metal=0.15)
MAT_ENCLOSURE_WALL = get_mat("HW_EnclosureWall",   (0.68, 0.68, 0.66), rough=0.60, metal=0.10)
MAT_PCB_GREEN      = get_mat("HW_PCB_Green",       (0.04, 0.32, 0.08), rough=0.70)
MAT_PCB_BLUE       = get_mat("HW_PCB_Blue",        (0.06, 0.12, 0.42), rough=0.65)
MAT_CHIP_BLACK     = get_mat("HW_Chip_Black",      (0.04, 0.04, 0.06), rough=0.35, metal=0.20)
MAT_LCD_SCREEN     = get_mat("HW_LCD_Screen",      (0.15, 0.55, 0.10), rough=0.15,
                             emit=(0.20, 0.72, 0.15), emit_str=2.8)
MAT_LCD_BEZEL      = get_mat("HW_LCD_Bezel",       (0.08, 0.08, 0.10), rough=0.40, metal=0.30)
MAT_RELAY_BLUE     = get_mat("HW_Relay_Blue",      (0.10, 0.18, 0.62), rough=0.55)
MAT_RELAY_COIL     = get_mat("HW_Relay_Coil",      (0.05, 0.05, 0.08), rough=0.50)
MAT_PSU_GOLD       = get_mat("HW_PSU_Gold",        (0.72, 0.60, 0.22), rough=0.45, metal=0.65)
MAT_PSU_PERF       = get_mat("HW_PSU_Perf",        (0.38, 0.36, 0.34), rough=0.60, metal=0.50)
MAT_SENSOR_BLUE    = get_mat("HW_Sensor_Blue",     (0.08, 0.22, 0.55), rough=0.55)
MAT_SENSOR_TEAL    = get_mat("HW_Sensor_Teal",     (0.06, 0.38, 0.35), rough=0.55)
MAT_WIRE_RED       = get_mat("HW_Wire_Red",        (0.85, 0.08, 0.05), rough=0.40)
MAT_WIRE_BLUE      = get_mat("HW_Wire_Blue",       (0.08, 0.15, 0.75), rough=0.40)
MAT_WIRE_YELLOW    = get_mat("HW_Wire_Yellow",     (0.90, 0.78, 0.05), rough=0.40)
MAT_WIRE_ORANGE    = get_mat("HW_Wire_Orange",     (0.92, 0.45, 0.05), rough=0.40)
MAT_CABLE_GLAND    = get_mat("HW_CableGland",      (0.12, 0.12, 0.14), rough=0.35, metal=0.70)
MAT_LED_GREEN      = get_mat("HW_LED_Green",       (0.05, 0.85, 0.10), rough=0.20,
                             emit=(0.1, 1.0, 0.15), emit_str=5.0)
MAT_LED_RED        = get_mat("HW_LED_Red",         (0.90, 0.05, 0.05), rough=0.20,
                             emit=(1.0, 0.08, 0.05), emit_str=3.0)
MAT_POLE_METAL     = get_mat("HW_Pole_Metal",      (0.32, 0.32, 0.34), rough=0.35, metal=0.80)
MAT_INVERTER_WHITE = get_mat("HW_Inverter_White",  (0.88, 0.88, 0.86), rough=0.40, metal=0.10)
MAT_INVERTER_DARK  = get_mat("HW_Inverter_Dark",   (0.10, 0.10, 0.12), rough=0.45, metal=0.20)
MAT_INV_SCREEN     = get_mat("HW_Inv_Screen",      (0.08, 0.08, 0.10), rough=0.15,
                             emit=(0.15, 0.45, 0.90), emit_str=1.8)
MAT_INV_STRIPE     = get_mat("HW_Inv_Stripe",      (0.10, 0.72, 0.18), rough=0.30,
                             emit=(0.12, 0.80, 0.22), emit_str=1.5)
MAT_CONCRETE_PAD   = get_mat("HW_ConcretePad",     (0.48, 0.46, 0.42), rough=0.85)

# Existing UI materials (reuse from scene)
MAT_CARD_BG      = bpy.data.materials.get("UI_Card_Navy") or \
                   get_mat("UI_Card_Navy", (0.05, 0.09, 0.16), rough=0.25, alpha=0.94)
MAT_CARD_BORDER  = bpy.data.materials.get("UI_Card_Border") or \
                   get_mat("UI_Card_Border", (0.28, 0.58, 0.88), rough=0.2,
                           emit=(0.28, 0.58, 0.88), emit_str=1.2)
MAT_CARD_TEXT    = bpy.data.materials.get("UI_Card_Text") or \
                   get_mat("UI_Card_Text", (0.96, 0.97, 0.99), rough=0.2,
                           emit=(0.96, 0.97, 0.99), emit_str=0.9)
MAT_CARD_POINTER = bpy.data.materials.get("UI_Pointer_Line") or \
                   get_mat("UI_Pointer_Line", (0.45, 0.72, 0.95), rough=0.3,
                           emit=(0.45, 0.72, 0.95), emit_str=1.5)

# Circuit wire materials (preserve existing)
MAT_WIRE_DC   = get_glow_mat("Mat_Wire_DC",   (1.0, 0.12, 0.04), emit_str=3.0)
MAT_WIRE_AC   = get_glow_mat("Mat_Wire_AC",   (1.0, 0.48, 0.04), emit_str=3.0)
MAT_WIRE_DATA = get_glow_mat("Mat_Wire_Data", (0.08, 0.92, 0.22), emit_str=2.6)
MAT_WIRE_GRID = get_glow_mat("Mat_Wire_Grid", (0.80, 0.88, 0.98), emit_str=1.2)
# Cyan sensor/data line between Control Unit and Inverter
MAT_WIRE_CYAN = get_glow_mat("Mat_Wire_Cyan", (0.10, 0.82, 0.88), emit_str=2.4)

# ---------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------
def make_box(name, loc, size, mat, col=COL_EQUIPMENT, bevel=0.0):
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
# UI helpers (matching existing card style exactly)
# ---------------------------------------------------------------------------
def create_ui_card(name, loc, size, rot=(0, 0, 0)):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    old_b = bpy.data.objects.get(f"{name}_Border")
    if old_b:
        bpy.data.objects.remove(old_b, do_unlink=True)
    b_box = make_box(f"{name}_Border", loc,
                     (size[0] + 0.08, size[1] + 0.08, size[2]),
                     MAT_CARD_BORDER, COL_UI, bevel=0.04)
    b_box.rotation_euler = rot
    in_loc = (loc[0], loc[1], loc[2] + 0.015)
    c_box = make_box(name, in_loc, size, MAT_CARD_BG, COL_UI, bevel=0.03)
    c_box.rotation_euler = rot
    c_box.parent = b_box
    c_box.location = (0, 0, 0.01)
    return b_box

def add_card_text(name, parent_card, text, local_offset,
                  font_size=0.32, align="LEFT", mat=None):
    if mat is None:
        mat = MAT_CARD_TEXT
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    t_data = bpy.data.curves.new(name, "FONT")
    t_data.body = text
    t_data.size = font_size
    t_data.align_x = align
    t_data.align_y = "CENTER"
    t_data.extrude = 0.008
    t_ob = bpy.data.objects.new(name, t_data)
    t_ob.data.materials.append(mat)
    link_to(t_ob, COL_UI)
    t_ob.parent = parent_card
    t_ob.location = local_offset
    t_ob.rotation_euler = (0, 0, 0)
    return t_ob

def create_pointer_line(name, card_pt, anchor_pt):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    c_data = bpy.data.curves.new(name, "CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.02
    spline = c_data.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (*card_pt, 1.0)
    spline.points[1].co = (*anchor_pt, 1.0)
    p_ob = bpy.data.objects.new(name, c_data)
    p_ob.data.materials.append(MAT_CARD_POINTER)
    return link_to(p_ob, COL_UI)

def add_label_3d(name, loc, text, font_size=0.14, mat=None):
    """Small floating label in the 3D scene (not a card — just text)."""
    if mat is None:
        mat = MAT_CARD_TEXT
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    t_data = bpy.data.curves.new(name, "FONT")
    t_data.body = text
    t_data.size = font_size
    t_data.align_x = "CENTER"
    t_data.align_y = "CENTER"
    t_data.extrude = 0.005
    t_ob = bpy.data.objects.new(name, t_data)
    t_ob.location = loc
    t_ob.data.materials.append(mat)
    return link_to(t_ob, COL_UI)

# ---------------------------------------------------------------------------
# STEP 0 — Remove Old Placeholder Objects
# ---------------------------------------------------------------------------
def remove_old_placeholders():
    print("Removing old placeholder control unit objects...")
    # Names that match the old placeholder boxes
    remove_prefixes = [
        "Control_ESP32", "Relay_Module_1",
        "HW_Ctrl_", "HW_Inv_", "HW_MPPT_",
        "Pad_UtilityEquipment",
    ]
    # Also remove old callout cards for Control and Relay that we'll rebuild
    remove_exact = [
        "Card_Callout_Control", "Card_Callout_Control_Border",
        "Card_Callout_Relay", "Card_Callout_Relay_Border",
        "Pointer_Callout_Control", "Pointer_Callout_Relay",
        "Txt_Callout_Ctrl_Title", "Txt_Callout_Ctrl_Sub",
        "Txt_Callout_Relay_Title", "Txt_Callout_Relay_Sub",
        "Wire_Cyan_Ctrl_MPPT", "HW_Lbl_CyanLine",
    ]
    to_delete = []
    for ob in bpy.data.objects:
        if ob.name in remove_exact:
            to_delete.append(ob)
        elif any(ob.name.startswith(p) for p in remove_prefixes):
            to_delete.append(ob)
    for ob in to_delete:
        bpy.data.objects.remove(ob, do_unlink=True)
    print(f"  Removed {len(to_delete)} old objects.")

# ---------------------------------------------------------------------------
# STEP 1 — Build ASSET 1: Main Control Enclosure
# ---------------------------------------------------------------------------
# Position: Same as old Control_ESP32 location (-9.2, 1.8, Z on ground)
CTRL_X, CTRL_Y = -9.2, 1.8
CTRL_BASE_Z = 0.15  # Ground + pad height

def build_control_enclosure():
    print("Building ASSET 1: Main Control Enclosure...")

    # Concrete utility pad
    make_box("HW_Ctrl_Pad", (CTRL_X, CTRL_Y, 0.06), (2.8, 2.0, 0.12),
             MAT_CONCRETE_PAD, COL_EQUIPMENT)

    # --- Mounting post/stand ---
    make_cyl("HW_Ctrl_Post", (CTRL_X, CTRL_Y, 0.55), 0.08, 0.80,
             MAT_POLE_METAL, COL_EQUIPMENT, 8)

    # --- Enclosure shell (open-top box) ---
    # Enclosure dimensions: width=1.6, depth=0.5, height=1.2
    ENC_W, ENC_D, ENC_H = 1.6, 0.5, 1.2
    enc_z = 0.95 + ENC_H / 2  # Center Z of enclosure

    # Back wall
    make_box("HW_Ctrl_Enc_Back", (CTRL_X, CTRL_Y + ENC_D / 2, enc_z),
             (ENC_W, 0.04, ENC_H), MAT_ENCLOSURE_WALL, COL_EQUIPMENT)
    # Left wall
    make_box("HW_Ctrl_Enc_Left", (CTRL_X - ENC_W / 2, CTRL_Y, enc_z),
             (0.04, ENC_D, ENC_H), MAT_ENCLOSURE_WALL, COL_EQUIPMENT)
    # Right wall
    make_box("HW_Ctrl_Enc_Right", (CTRL_X + ENC_W / 2, CTRL_Y, enc_z),
             (0.04, ENC_D, ENC_H), MAT_ENCLOSURE_WALL, COL_EQUIPMENT)
    # Front wall (slightly transparent to show interior)
    make_box("HW_Ctrl_Enc_Front", (CTRL_X, CTRL_Y - ENC_D / 2, enc_z),
             (ENC_W, 0.03, ENC_H),
             get_mat("HW_Enc_FrontGlass", (0.60, 0.62, 0.65), rough=0.10,
                     alpha=0.35, metal=0.05),
             COL_EQUIPMENT)
    # Bottom
    make_box("HW_Ctrl_Enc_Bottom", (CTRL_X, CTRL_Y, 0.95),
             (ENC_W, ENC_D, 0.04), MAT_ENCLOSURE, COL_EQUIPMENT)

    # Interior component base Z
    int_z = 0.97  # Just above enclosure bottom

    # --- Component layout inside enclosure (matching reference image) ---
    # Layout is 3x3 grid approximately:
    #   Top-left:     Current Sensor     | Top-center: ESP32 MCU  | Top-right: LCD Display
    #   Mid-left:     Voltage Sensor     | (empty)                | Mid-right: Solar Measurement Sensor
    #   Bottom-left:  Power Supply Unit  | (wiring)               | Bottom-right: Relay/Switching Unit
    #   Below mid-right: Environmental Sensor

    cw = ENC_W / 3  # Column width ~0.53
    ch = ENC_H / 3  # Row height ~0.40

    # --- ESP32 MCU (center, top row) ---
    esp_x = CTRL_X
    esp_z = int_z + ENC_H * 0.75
    make_box("HW_Ctrl_ESP32_Board", (esp_x, CTRL_Y, esp_z),
             (0.35, 0.08, 0.22), MAT_PCB_GREEN, COL_EQUIPMENT, bevel=0.01)
    # Main chip on ESP32
    make_box("HW_Ctrl_ESP32_Chip", (esp_x, CTRL_Y - 0.01, esp_z + 0.03),
             (0.14, 0.04, 0.10), MAT_CHIP_BLACK, COL_EQUIPMENT)
    # Antenna stub
    make_box("HW_Ctrl_ESP32_Ant", (esp_x + 0.12, CTRL_Y, esp_z + 0.06),
             (0.08, 0.03, 0.04), MAT_CHIP_BLACK, COL_EQUIPMENT)

    # --- LCD Display (top right) ---
    lcd_x = CTRL_X + cw * 0.9
    lcd_z = int_z + ENC_H * 0.75
    # Bezel
    make_box("HW_Ctrl_LCD_Bezel", (lcd_x, CTRL_Y, lcd_z),
             (0.42, 0.06, 0.28), MAT_LCD_BEZEL, COL_EQUIPMENT, bevel=0.008)
    # Screen
    make_box("HW_Ctrl_LCD_Screen", (lcd_x, CTRL_Y - 0.01, lcd_z),
             (0.36, 0.03, 0.22), MAT_LCD_SCREEN, COL_EQUIPMENT)

    # --- Current Sensor (top left) ---
    cs_x = CTRL_X - cw * 0.9
    cs_z = int_z + ENC_H * 0.75
    make_box("HW_Ctrl_CurrentSensor", (cs_x, CTRL_Y, cs_z),
             (0.22, 0.08, 0.18), MAT_SENSOR_BLUE, COL_EQUIPMENT, bevel=0.01)
    # Sensor toroid
    make_cyl("HW_Ctrl_CS_Toroid", (cs_x, CTRL_Y - 0.02, cs_z),
             0.06, 0.04, MAT_SENSOR_BLUE, COL_EQUIPMENT, 12,
             rot=(math.pi / 2, 0, 0))

    # --- Voltage Sensor (below current sensor) ---
    vs_x = CTRL_X - cw * 0.9
    vs_z = int_z + ENC_H * 0.45
    make_box("HW_Ctrl_VoltageSensor", (vs_x, CTRL_Y, vs_z),
             (0.22, 0.06, 0.14), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.008)
    # Screw terminals
    for dx in (-0.06, 0.0, 0.06):
        make_box(f"HW_Ctrl_VS_Term_{int(dx * 100)}",
                 (vs_x + dx, CTRL_Y - 0.01, vs_z + 0.06),
                 (0.03, 0.02, 0.03), MAT_SENSOR_BLUE, COL_EQUIPMENT)

    # --- Solar Measurement Sensor (mid right) ---
    ss_x = CTRL_X + cw * 0.9
    ss_z = int_z + ENC_H * 0.45
    make_box("HW_Ctrl_SolarSensor", (ss_x, CTRL_Y, ss_z),
             (0.24, 0.06, 0.16), MAT_SENSOR_TEAL, COL_EQUIPMENT, bevel=0.008)
    # Current shunt
    make_box("HW_Ctrl_SS_Shunt", (ss_x - 0.05, CTRL_Y - 0.01, ss_z - 0.04),
             (0.08, 0.03, 0.04), MAT_PSU_GOLD, COL_EQUIPMENT)

    # --- Environmental Sensor (below solar sensor, right side) ---
    es_x = CTRL_X + cw * 0.9
    es_z = int_z + ENC_H * 0.20
    make_box("HW_Ctrl_EnvSensor", (es_x, CTRL_Y, es_z),
             (0.18, 0.05, 0.12), MAT_PCB_GREEN, COL_EQUIPMENT, bevel=0.006)
    # Sensor dome
    make_cyl("HW_Ctrl_ES_Dome", (es_x, CTRL_Y - 0.01, es_z + 0.04),
             0.03, 0.04, MAT_CHIP_BLACK, COL_EQUIPMENT, 8)

    # --- Power Supply Unit (bottom left) ---
    psu_x = CTRL_X - cw * 0.9
    psu_z = int_z + ENC_H * 0.18
    # PSU metal case
    make_box("HW_Ctrl_PSU_Case", (psu_x, CTRL_Y, psu_z),
             (0.30, 0.10, 0.18), MAT_PSU_GOLD, COL_EQUIPMENT, bevel=0.01)
    # PSU perforated face
    make_box("HW_Ctrl_PSU_Perf", (psu_x - 0.10, CTRL_Y, psu_z),
             (0.08, 0.09, 0.16), MAT_PSU_PERF, COL_EQUIPMENT)

    # --- Relay / Switching Unit (bottom right) ---
    rl_x = CTRL_X + cw * 0.4
    rl_z = int_z + ENC_H * 0.18
    # Relay bank base
    make_box("HW_Ctrl_Relay_Base", (rl_x, CTRL_Y, rl_z),
             (0.38, 0.08, 0.16), MAT_PCB_BLUE, COL_EQUIPMENT, bevel=0.006)
    # Four individual relays
    for ri in range(4):
        rx = rl_x - 0.12 + ri * 0.08
        make_box(f"HW_Ctrl_Relay_{ri}", (rx, CTRL_Y - 0.01, rl_z + 0.04),
                 (0.06, 0.05, 0.08), MAT_RELAY_BLUE, COL_EQUIPMENT, bevel=0.004)

    # --- Internal wiring stubs (colored wires connecting components) ---
    def make_wire_stub(name, start, end, mat):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        c_data = bpy.data.curves.new(name, "CURVE")
        c_data.dimensions = "3D"
        c_data.bevel_depth = 0.008
        c_data.bevel_resolution = 2
        spline = c_data.splines.new("BEZIER")
        spline.bezier_points.add(1)
        for i, pt in enumerate([start, end]):
            bp = spline.bezier_points[i]
            bp.co = Vector(pt)
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
        w_ob = bpy.data.objects.new(name, c_data)
        w_ob.data.materials.append(mat)
        return link_to(w_ob, COL_EQUIPMENT)

    # Red wire: PSU to ESP32
    make_wire_stub("HW_Ctrl_WireR_1",
                   (psu_x + 0.10, CTRL_Y, psu_z + 0.06),
                   (esp_x - 0.10, CTRL_Y, esp_z - 0.06), MAT_WIRE_RED)
    # Blue wire: Sensors to ESP32
    make_wire_stub("HW_Ctrl_WireB_1",
                   (cs_x + 0.08, CTRL_Y, cs_z - 0.04),
                   (esp_x - 0.10, CTRL_Y, esp_z + 0.02), MAT_WIRE_BLUE)
    # Yellow wire: ESP32 to LCD
    make_wire_stub("HW_Ctrl_WireY_1",
                   (esp_x + 0.12, CTRL_Y, esp_z),
                   (lcd_x - 0.15, CTRL_Y, lcd_z), MAT_WIRE_YELLOW)
    # Orange wire: ESP32 to Relays
    make_wire_stub("HW_Ctrl_WireO_1",
                   (esp_x, CTRL_Y, esp_z - 0.08),
                   (rl_x, CTRL_Y, rl_z + 0.10), MAT_WIRE_ORANGE)
    # Red wire: Solar Sensor to ESP32
    make_wire_stub("HW_Ctrl_WireR_2",
                   (ss_x - 0.08, CTRL_Y, ss_z),
                   (esp_x + 0.06, CTRL_Y, esp_z - 0.04), MAT_WIRE_RED)

    # --- Four cable glands at the base ---
    gland_z = 0.95
    gland_y = CTRL_Y - ENC_D / 2 - 0.02
    gland_labels = [
        ("Solar Input", -0.48),
        ("Battery Input", -0.16),
        ("AC Load Output", 0.16),
        ("Grid Input", 0.48),
    ]
    for gi, (lbl, dx) in enumerate(gland_labels):
        gx = CTRL_X + dx
        make_cyl(f"HW_Ctrl_Gland_{gi}", (gx, gland_y, gland_z),
                 0.03, 0.08, MAT_CABLE_GLAND, COL_EQUIPMENT, 10,
                 rot=(math.pi / 2, 0, 0))
        # Small label below gland
        add_label_3d(f"HW_Ctrl_GlandLbl_{gi}",
                     (gx, gland_y - 0.15, gland_z - 0.10),
                     lbl, font_size=0.06, mat=MAT_CARD_TEXT)

    # --- Status LEDs on front face ---
    led_front_y = CTRL_Y - ENC_D / 2 - 0.01
    make_cyl("HW_Ctrl_LED_Green",
             (CTRL_X - 0.12, led_front_y, enc_z + ENC_H * 0.35),
             0.025, 0.015, MAT_LED_GREEN, COL_EQUIPMENT, 10,
             rot=(math.pi / 2, 0, 0))
    make_cyl("HW_Ctrl_LED_Red",
             (CTRL_X + 0.12, led_front_y, enc_z + ENC_H * 0.35),
             0.025, 0.015, MAT_LED_RED, COL_EQUIPMENT, 10,
             rot=(math.pi / 2, 0, 0))

    print("  ASSET 1: Main Control Enclosure built.")

# ---------------------------------------------------------------------------
# STEP 2 — Build ASSET 2: Inverter + MPPT Unit
# ---------------------------------------------------------------------------
# Position: On the existing circuit path between DC solar and AC distribution.
# The DC line from solar currently ends at the Control Unit.
# We place the Inverter unit between the solar DC endpoint and the relay/AC start.
# Original DC endpoint: (-9.2, 2.2, 0.45), AC start: (-7.6, 2.2, 0.45)
# We place it at the midpoint, slightly offset for visual clarity.
INV_X, INV_Y = -8.4, 2.6
INV_BASE_Z = 0.15

def build_inverter_mppt_unit():
    print("Building ASSET 2: Inverter + MPPT Unit...")

    # Mounting pole
    make_cyl("HW_Inv_Pole", (INV_X, INV_Y, 0.50), 0.06, 0.80,
             MAT_POLE_METAL, COL_EQUIPMENT, 8)

    # --- Main inverter body (compact wall-mount style) ---
    INV_W, INV_D, INV_H = 0.70, 0.24, 0.85
    inv_z = 0.90 + INV_H / 2

    # White main body
    make_box("HW_Inv_Body", (INV_X, INV_Y, inv_z),
             (INV_W, INV_D, INV_H), MAT_INVERTER_WHITE, COL_EQUIPMENT, bevel=0.02)

    # Dark bottom section
    make_box("HW_Inv_BottomPanel", (INV_X, INV_Y - 0.005, inv_z - INV_H * 0.30),
             (INV_W * 0.96, INV_D * 0.6, INV_H * 0.35), MAT_INVERTER_DARK, COL_EQUIPMENT)

    # Green accent stripe (matching reference image)
    make_box("HW_Inv_Stripe", (INV_X, INV_Y - INV_D / 2 + 0.01, inv_z + 0.05),
             (INV_W * 0.92, 0.012, 0.03), MAT_INV_STRIPE, COL_EQUIPMENT)

    # LCD display window
    make_box("HW_Inv_Screen_Bezel", (INV_X, INV_Y - INV_D / 2 + 0.01, inv_z + INV_H * 0.18),
             (0.28, 0.015, 0.16), MAT_INVERTER_DARK, COL_EQUIPMENT, bevel=0.005)
    make_box("HW_Inv_Screen", (INV_X, INV_Y - INV_D / 2 + 0.005, inv_z + INV_H * 0.18),
             (0.24, 0.012, 0.12), MAT_INV_SCREEN, COL_EQUIPMENT)

    # Control buttons (3 dots below screen)
    for bi, dx in enumerate([-0.06, 0.0, 0.06]):
        make_cyl(f"HW_Inv_Btn_{bi}",
                 (INV_X + dx, INV_Y - INV_D / 2 + 0.005, inv_z + INV_H * 0.05),
                 0.015, 0.008, MAT_INVERTER_DARK, COL_EQUIPMENT, 8,
                 rot=(math.pi / 2, 0, 0))

    # Bottom ventilation grille
    for vi in range(4):
        vy = inv_z - INV_H * 0.35 + vi * 0.04
        make_box(f"HW_Inv_Vent_{vi}",
                 (INV_X, INV_Y - INV_D / 2 + 0.01, vy - 0.08),
                 (INV_W * 0.70, 0.008, 0.012), MAT_INVERTER_DARK, COL_EQUIPMENT)

    # DC input connector (left side)
    make_cyl("HW_Inv_DC_In", (INV_X - INV_W / 2 - 0.03, INV_Y, inv_z - 0.20),
             0.025, 0.06, MAT_CABLE_GLAND, COL_EQUIPMENT, 8,
             rot=(0, math.pi / 2, 0))

    # AC output connector (right side)
    make_cyl("HW_Inv_AC_Out", (INV_X + INV_W / 2 + 0.03, INV_Y, inv_z - 0.20),
             0.025, 0.06, MAT_CABLE_GLAND, COL_EQUIPMENT, 8,
             rot=(0, math.pi / 2, 0))

    # --- Floating info tag (functions) ---
    # Small dark-navy info card listing inverter functions
    info_tag = create_ui_card("HW_Inv_InfoTag",
                              (INV_X, INV_Y + 0.8, inv_z + INV_H * 0.6),
                              (2.2, 1.2, 0.05))
    add_card_text("HW_Inv_InfoTag_T1", info_tag,
                  "• MPPT Control", (-0.95, 0.30, 0.03), 0.16, mat=MAT_CARD_TEXT)
    add_card_text("HW_Inv_InfoTag_T2", info_tag,
                  "• DC to AC Conversion", (-0.95, 0.08, 0.03), 0.16, mat=MAT_CARD_TEXT)
    add_card_text("HW_Inv_InfoTag_T3", info_tag,
                  "• Synchronizes with Grid", (-0.95, -0.14, 0.03), 0.16, mat=MAT_CARD_TEXT)
    add_card_text("HW_Inv_InfoTag_T4", info_tag,
                  "• Power Quality Control", (-0.95, -0.36, 0.03), 0.16, mat=MAT_CARD_TEXT)

    print("  ASSET 2: Inverter + MPPT Unit built.")

# ---------------------------------------------------------------------------
# STEP 3 — Update Circuit Wiring
# ---------------------------------------------------------------------------
def update_circuit_wiring():
    print("Updating circuit wiring for new hardware placement...")

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

    # DC Solar Line (Red/Orange) — Now terminates at the Inverter + MPPT Unit
    # Rooftop PV -> West Parapet -> Wall Conduit -> Walkway -> Inverter DC Input
    pts_dc = [
        (-3.5, 12.8, 6.05),      # From Solar Array center
        (-6.5, 12.8, 6.00),      # Along North Roof
        (-8.4, 12.8, 6.00),      # Roof parapet corner
        (-8.8, 11.2, 5.10),      # West wing junction
        (-8.8, 11.2, 2.50),      # Vertical conduit down wall
        (-8.8, 11.2, 0.45),      # Ground service trench
        (-8.4, 5.5, 0.45),       # Along west walkway
        (-8.4, 2.6, 0.70),       # Into Inverter/MPPT DC input (left side)
    ]
    update_spline_curve("Wire_DC", pts_dc, MAT_WIRE_DC, 0.055)

    # AC Distribution Line (Orange) — Now originates from the Inverter + MPPT Unit
    # Inverter AC Output -> Relay/Switching -> Building Foundation -> Wing Distribution
    pts_ac = [
        (-8.4, 2.6, 0.70),       # Inverter AC Output (right side)
        (-7.6, 2.2, 0.45),       # To relay connection point
        (-7.6, 3.6, 0.40),       # Foundation entry
        (-6.2, 4.3, 0.40),       # Wing 1 (Critical Lab load)
        (-3.0, 4.3, 0.40),       # Cross-corridor trunk
        (0.0, 5.2, 0.40),        # Wing 2 (Academic central load)
        (3.5, 4.3, 0.40),        # Cross-corridor East
        (7.0, 4.3, 0.40),        # Wing 3 (Auditorium load)
    ]
    update_spline_curve("Wire_AC", pts_ac, MAT_WIRE_AC, 0.058)

    # Sensor / Data Feedback Line (Green) — ESP32 Sensor Bus (unchanged path)
    pts_data = [
        (-3.5, 13.0, 6.10),      # Solar PV sensor tap
        (-8.0, 13.0, 6.05),      # Conduit
        (-8.6, 11.0, 0.46),      # Service riser
        (-9.0, 2.3, 0.46),       # ESP32 Sensor Port
        (-8.2, 2.3, 0.46),       # Relay switching control interface
    ]
    update_spline_curve("Wire_Data", pts_data, MAT_WIRE_DATA, 0.040)

    # Grid Utility Line (Grey / White) — unchanged path
    pts_grid = [
        (15.8, -14.5, 5.20),     # Grid Transformer output
        (15.5, -14.5, 2.60),     # Down utility pole
        (15.0, -14.0, 0.42),     # Ground junction
        (8.0, -14.0, 0.40),      # Along road boundary conduit
        (0.0, -13.5, 0.40),      # Cross-promenade conduit
        (-7.5, -12.0, 0.40),     # Toward west utility area
        (-7.6, 1.5, 0.42),       # Grid Input into Relay / Control Unit
    ]
    update_spline_curve("Wire_Grid", pts_grid, MAT_WIRE_GRID, 0.050)

    # NEW: Cyan line — ESP32 MCU • MPPT SENSING (Control Unit <-> Inverter/MPPT)
    pts_cyan = [
        (CTRL_X, CTRL_Y, 1.55),          # From Control Enclosure top
        (CTRL_X, CTRL_Y + 0.35, 1.80),   # Rise up
        (INV_X, INV_Y + 0.35, 1.80),     # Across to inverter
        (INV_X, INV_Y, 1.55),            # Into Inverter top
    ]
    update_spline_curve("Wire_Cyan_Ctrl_MPPT", pts_cyan, MAT_WIRE_CYAN, 0.035)

    # Update FX_Pulse objects to use updated curve data
    for key, cname in [("DC", "Wire_DC"), ("AC", "Wire_AC"),
                       ("Data", "Wire_Data"), ("Grid", "Wire_Grid")]:
        p = bpy.data.objects.get(f"FX_Pulse_{key}")
        w = bpy.data.objects.get(cname)
        if p and w:
            p.data = w.data

    print("  Circuit wiring updated.")

# ---------------------------------------------------------------------------
# STEP 4 — Update Callout Cards for New Assets
# ---------------------------------------------------------------------------
def update_callout_cards():
    print("Updating callout cards for new hardware assets...")

    # Card: Control Unit — ESP32
    card_ctrl = create_ui_card("Card_Callout_Control",
                                (-12.8, 1.8, 2.8), (4.8, 1.4, 0.08))
    add_card_text("Txt_Callout_Ctrl_Title", card_ctrl,
                  "CONTROL UNIT — ESP32", (-2.1, 0.28, 0.04), 0.32)
    add_card_text("Txt_Callout_Ctrl_Sub", card_ctrl,
                  "MCU • SENSORS • LCD • RELAY BANK",
                  (-2.1, -0.25, 0.04), 0.22, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Control",
                        (-10.3, 1.8, 2.8), (CTRL_X, CTRL_Y, 1.55))

    # Card: Inverter + MPPT Unit
    card_inv = create_ui_card("Card_Callout_Inverter",
                               (-8.4, 4.8, 2.8), (4.6, 1.4, 0.08))
    add_card_text("Txt_Callout_Inv_Title", card_inv,
                  "INVERTER + MPPT UNIT", (-2.0, 0.28, 0.04), 0.32)
    add_card_text("Txt_Callout_Inv_Sub", card_inv,
                  "DC→AC CONVERTER • GRID SYNC",
                  (-2.0, -0.25, 0.04), 0.22, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Inverter",
                        (-8.4, 4.1, 2.8), (INV_X, INV_Y, 1.33))

    # Add label along the cyan line
    add_label_3d("HW_Lbl_CyanLine",
                 ((CTRL_X + INV_X) / 2, CTRL_Y + 0.55, 2.0),
                 "ESP32 MCU • MPPT SENSING", font_size=0.10,
                 mat=get_mat("HW_CyanLabel", (0.10, 0.82, 0.88), rough=0.2,
                             emit=(0.10, 0.82, 0.88), emit_str=1.8))

    print("  Callout cards updated.")

# ---------------------------------------------------------------------------
# STEP 5 — Re-render Both Camera Views
# ---------------------------------------------------------------------------
def render_views():
    print("Rendering updated views...")

    # Reuse existing scenario application
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
    }

    def apply_scenario(scene, sid):
        cfg = SCENARIO_CONFIGS.get(sid, SCENARIO_CONFIGS[1])
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

    apply_scenario(SCENE, 1)

    # Render settings
    SCENE.render.engine = "BLENDER_EEVEE"
    SCENE.render.resolution_x = 1920
    SCENE.render.resolution_y = 1080
    SCENE.render.resolution_percentage = 100

    for cam_name, tag in [("CAM_TOP_DOWN", "v5_top_down"),
                          ("CAM_ANGLED_VIEW", "v5_angled")]:
        cam = bpy.data.objects.get(cam_name)
        if not cam:
            print(f"  Camera {cam_name} not found!")
            continue
        SCENE.camera = cam
        bpy.context.view_layer.update()
        out_path = os.path.join(OUT_DIR, f"{tag}_hardware_upgrade.png")
        SCENE.render.filepath = out_path
        print(f"  Rendering: {cam_name} -> {out_path}")
        bpy.ops.render.render(write_still=True)
        print(f"  DONE: {out_path}")

    print("  All renders complete.")

# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  VOLT VISION — HARDWARE UNIT UPGRADE")
    print("=" * 60)

    remove_old_placeholders()
    build_control_enclosure()
    build_inverter_mppt_unit()
    update_circuit_wiring()
    update_callout_cards()

    # Save before rendering
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print("Scene saved with hardware upgrades.")

    render_views()

    print("=" * 60)
    print("  HARDWARE UPGRADE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
