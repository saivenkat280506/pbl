"""Replace the two placeholder utility boxes in the original Volt Vision scene.

This script targets VoltVision_v1_ORIGINAL_BACKUP.blend, the scene used by the
three-building screenshots.  It keeps the existing animated camera, HUD,
buildings, solar array, transformer, and circuit curves, and only replaces the
two physical utility assemblies plus their local labels.
"""

import math
import os
import bpy
import bmesh
from mathutils import Vector


BLEND_PATH = "/Users/saivenkat/Projects/pbl/VoltVision_v1_ORIGINAL_BACKUP.blend"
PROJECT_ROOT = "/Users/saivenkat/Projects/pbl"
PREVIEW_DIR = os.path.join(PROJECT_ROOT, "renders", "hardware_upgrade")
os.makedirs(PREVIEW_DIR, exist_ok=True)


bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
SCENE = bpy.context.scene
ORIGINAL_FRAME = SCENE.frame_current


def get_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        SCENE.collection.children.link(col)
    return col


COL_HW = get_collection("HARDWARE_UPGRADE")
COL_WIRES = bpy.data.collections.get("WIRES") or get_collection("WIRES")


def link_only(obj, col):
    for old_col in list(obj.users_collection):
        old_col.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def material(name, color, roughness=0.5, metallic=0.0, emission=None,
             emission_strength=1.0, alpha=1.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    if emission is not None:
        shader = nodes.new("ShaderNodeEmission")
        shader.inputs["Color"].default_value = (*emission, 1.0)
        shader.inputs["Strength"].default_value = emission_strength
    else:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        if alpha < 1.0:
            shader.inputs["Alpha"].default_value = alpha
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "DITHERED"
    links.new(shader.outputs[0], out.inputs["Surface"])
    return mat


# Scene-matched schematic palette.
M_BODY = material("HW2_Enclosure", (0.62, 0.65, 0.67), 0.52, 0.15)
M_BODY_EDGE = material("HW2_Enclosure_Edge", (0.80, 0.83, 0.84), 0.40, 0.20)
M_INTERIOR = material("HW2_Interior", (0.045, 0.075, 0.105), 0.60)
M_WHITE = material("HW2_Inverter_White", (0.88, 0.89, 0.88), 0.38, 0.10)
M_DARK = material("HW2_Inverter_Dark", (0.055, 0.065, 0.08), 0.42, 0.25)
M_PCB_GREEN = material("HW2_PCB_Green", (0.035, 0.26, 0.10), 0.66)
M_PCB_BLUE = material("HW2_PCB_Blue", (0.035, 0.13, 0.48), 0.58)
M_PCB_TEAL = material("HW2_PCB_Teal", (0.03, 0.33, 0.31), 0.60)
M_CHIP = material("HW2_Chip", (0.025, 0.03, 0.04), 0.34, 0.25)
M_METAL = material("HW2_Metal", (0.55, 0.58, 0.60), 0.30, 0.85)
M_SILVER = material("HW2_Silver", (0.78, 0.80, 0.82), 0.25, 0.80)
M_LCD = material("HW2_LCD", (0.35, 0.85, 0.15), 0.12,
                 emission=(0.25, 0.85, 0.10), emission_strength=2.0)
M_INV_SCREEN = material("HW2_Inverter_Screen", (0.10, 0.52, 0.88), 0.12,
                        emission=(0.10, 0.52, 0.95), emission_strength=1.8)
M_RELAY = material("HW2_Relay_Blue", (0.05, 0.18, 0.68), 0.48)
M_TERMINAL = material("HW2_Terminal", (0.06, 0.48, 0.16), 0.52)
M_TERMINAL_BLUE = material("HW2_Terminal_Blue", (0.05, 0.28, 0.72), 0.52)
M_PSU = material("HW2_PSU", (0.66, 0.52, 0.18), 0.42, 0.60)
M_CAUTION = material("HW2_Caution", (0.95, 0.70, 0.05), 0.35,
                     emission=(1.0, 0.65, 0.02), emission_strength=1.3)
M_RED = material("HW2_Wire_Red", (0.85, 0.04, 0.02), 0.4,
                 emission=(1.0, 0.05, 0.02), emission_strength=1.2)
M_BLUE = material("HW2_Wire_Blue", (0.04, 0.10, 0.78), 0.4,
                  emission=(0.05, 0.12, 0.95), emission_strength=1.2)
M_YELLOW = material("HW2_Wire_Yellow", (0.92, 0.68, 0.02), 0.4,
                    emission=(1.0, 0.72, 0.03), emission_strength=1.2)
M_ORANGE = material("HW2_Wire_Orange", (0.92, 0.28, 0.02), 0.4,
                    emission=(1.0, 0.32, 0.02), emission_strength=1.2)
M_BLACK = material("HW2_Cable", (0.025, 0.025, 0.03), 0.36, 0.65)
M_GREEN_LED = material("HW2_LED_Active", (0.04, 0.95, 0.12), 0.18,
                       emission=(0.05, 1.0, 0.15), emission_strength=4.0)
M_RED_LED = material("HW2_LED_Fault", (0.95, 0.04, 0.03), 0.18,
                     emission=(1.0, 0.04, 0.02), emission_strength=3.0)
M_CARD = material("HW2_Label_Navy", (0.025, 0.055, 0.11), 0.30,
                  emission=(0.025, 0.055, 0.11), emission_strength=0.55)
M_CARD_EDGE = material("HW2_Label_Edge", (0.22, 0.55, 0.86), 0.25,
                       emission=(0.22, 0.55, 0.86), emission_strength=1.0)
M_CARD_TEXT = material("HW2_Label_Text", (0.95, 0.98, 1.0), 0.25,
                       emission=(0.95, 0.98, 1.0), emission_strength=0.9)
M_CARD_SUB = material("HW2_Label_Sub", (0.35, 0.82, 0.96), 0.25,
                      emission=(0.35, 0.82, 0.96), emission_strength=1.0)
M_CYAN = material("HW2_Cyan_Feedback", (0.05, 0.80, 0.86), 0.3,
                  emission=(0.05, 0.90, 0.95), emission_strength=2.4)
M_DARK_TEXT = material("HW2_DarkText", (0.015, 0.04, 0.02), 0.3)


def mesh_box(name, location, size, mat, bevel=0.0, collection=COL_HW):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.scale = size
    mesh.materials.append(mat)
    collection.objects.link(obj)
    if bevel:
        mod = obj.modifiers.new("Soft schematic edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), verts=12,
             collection=COL_HW):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    mesh.materials.append(mat)
    collection.objects.link(obj)
    return obj


def curve(name, points, mat, bevel=0.012, collection=COL_HW, bezier=False):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel
    data.bevel_resolution = 2
    spline = data.splines.new("BEZIER" if bezier else "POLY")
    if bezier:
        spline.bezier_points.add(len(points) - 1)
        for bp, point in zip(spline.bezier_points, points):
            bp.co = Vector(point)
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
    else:
        spline.points.add(len(points) - 1)
        for p, point in zip(spline.points, points):
            p.co = (*point, 1.0)
    obj = bpy.data.objects.new(name, data)
    data.materials.append(mat)
    collection.objects.link(obj)
    return obj


def text(name, body, location, size=0.06, mat=M_CARD_TEXT, align="CENTER",
         rotation=(0, 0, 0), collection=COL_HW):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.curves.new(name + "_Font", "FONT")
    data.body = body
    data.size = size
    data.align_x = align
    data.align_y = "CENTER"
    data.extrude = 0.002
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = rotation
    data.materials.append(mat)
    collection.objects.link(obj)
    return obj


def card(name, center, width, height, title, subtitle):
    x, y, z = center
    mesh_box(name + "_Border", (x, y, z), (width + 0.06, height + 0.06, 0.035),
             M_CARD_EDGE, bevel=0.035)
    mesh_box(name + "_Face", (x, y, z + 0.022), (width, height, 0.035),
             M_CARD, bevel=0.028)
    title_size = min(0.095, width * 0.055)
    sub_size = min(0.047, width * 0.028)
    text(name + "_Title", title, (x, y + height * 0.22, z + 0.052),
         size=title_size, mat=M_CARD_TEXT)
    text(name + "_Sub", subtitle, (x, y - height * 0.25, z + 0.052),
         size=sub_size, mat=M_CARD_SUB)


def remove_old_hardware():
    prefixes = (
        "Control_ESP32", "Control_Post", "Control_LED", "Control_Terminal",
        "Relay_Unit", "Relay_Post", "Relay_Module", "Relay_Terminal",
        "Relay_Contactor", "Relay_InternalWire", "Relay_LED",
        "HW2_", "HW_Ctrl_", "HW_Inv_", "HW_MPPT_",
    )
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def build_control_enclosure():
    x, y = -3.0, -2.0
    base = 0.38
    floor_z = base + 0.025
    # Preserve the original mounting footprint.
    cylinder("HW2_Control_Post", (x, y, 0.18), 0.06, 0.36, M_METAL, verts=12)
    mesh_box("HW2_Control_Floor", (x, y, floor_z), (0.98, 0.60, 0.05),
             M_BODY, bevel=0.025)
    mesh_box("HW2_Control_BackWall", (x, y + 0.27, 0.63), (0.98, 0.055, 0.46),
             M_BODY_EDGE, bevel=0.018)
    mesh_box("HW2_Control_LeftWall", (x - 0.46, y, 0.61), (0.055, 0.60, 0.42),
             M_BODY_EDGE, bevel=0.018)
    mesh_box("HW2_Control_RightWall", (x + 0.46, y, 0.61), (0.055, 0.60, 0.42),
             M_BODY_EDGE, bevel=0.018)
    # Low front lip makes the enclosure visibly open while keeping the LEDs external.
    mesh_box("HW2_Control_FrontLip", (x, y - 0.27, 0.48), (0.98, 0.055, 0.14),
             M_BODY_EDGE, bevel=0.018)
    mesh_box("HW2_Control_Backplate", (x, y, base + 0.06), (0.86, 0.48, 0.018),
             M_INTERIOR, bevel=0.006)
    for dx in (-0.41, 0.41):
        for dy in (-0.23, 0.23):
            cylinder("HW2_Control_Screw_%s_%s" % (dx, dy),
                     (x + dx, y + dy, 0.93), 0.018, 0.035, M_SILVER, verts=8)

    z = 0.49
    # Current sensor, top-left.
    cx, cy = x - 0.32, y + 0.18
    mesh_box("HW2_Current_PCB", (cx, cy, z), (0.22, 0.14, 0.022), M_PCB_BLUE, bevel=0.008)
    cylinder("HW2_Current_Toroid", (cx - 0.035, cy, z + 0.04), 0.045, 0.035,
             M_PCB_BLUE, rotation=(math.pi / 2, 0, 0), verts=12)
    mesh_box("HW2_Current_Terminal", (cx + 0.075, cy, z + 0.032),
             (0.045, 0.095, 0.035), M_TERMINAL, bevel=0.004)
    text("HW2_Current_Label", "AC I", (cx, cy, z + 0.055), 0.036, M_CARD_TEXT)

    # ESP32 center board with shield and antenna.
    ex, ey = x, y + 0.08
    mesh_box("HW2_ESP32_PCB", (ex, ey, z + 0.015), (0.28, 0.20, 0.022), M_PCB_GREEN, bevel=0.006)
    mesh_box("HW2_ESP32_Shield", (ex, ey + 0.02, z + 0.052), (0.13, 0.10, 0.025), M_SILVER, bevel=0.004)
    mesh_box("HW2_ESP32_Chip", (ex - 0.09, ey - 0.035, z + 0.047), (0.05, 0.05, 0.018), M_CHIP)
    mesh_box("HW2_ESP32_Antenna", (ex + 0.105, ey + 0.07, z + 0.045), (0.10, 0.028, 0.016), M_CHIP)
    text("HW2_ESP32_Label", "ESP32", (ex, ey - 0.12, z + 0.055), 0.042, M_CARD_TEXT)

    # LCD top-right with the requested telemetry format.
    lx, ly = x + 0.31, y + 0.18
    mesh_box("HW2_LCD_PCB", (lx, ly, z), (0.28, 0.16, 0.022), M_PCB_GREEN, bevel=0.006)
    mesh_box("HW2_LCD_Bezel", (lx, ly, z + 0.026), (0.25, 0.13, 0.022), M_DARK, bevel=0.005)
    mesh_box("HW2_LCD_Screen", (lx, ly, z + 0.042), (0.22, 0.095, 0.008), M_LCD, bevel=0.002)
    text("HW2_LCD_Line1", "Solar: 48V 3.1A", (lx - 0.095, ly + 0.027, z + 0.052),
         0.020, M_DARK_TEXT, align="LEFT")
    text("HW2_LCD_Line2", "Load: 8.5 kW", (lx - 0.095, ly, z + 0.052),
         0.020, M_DARK_TEXT, align="LEFT")
    text("HW2_LCD_Line3", "Grid: ON Auto", (lx - 0.095, ly - 0.027, z + 0.052),
         0.020, M_DARK_TEXT, align="LEFT")

    # Voltage sensor below current sensor.
    vx, vy = x - 0.32, y - 0.03
    mesh_box("HW2_Voltage_PCB", (vx, vy, z), (0.22, 0.14, 0.022), M_PCB_BLUE, bevel=0.006)
    mesh_box("HW2_Voltage_Terminal", (vx - 0.07, vy, z + 0.035),
             (0.05, 0.10, 0.035), M_TERMINAL, bevel=0.004)
    mesh_box("HW2_Voltage_Chip", (vx + 0.035, vy, z + 0.033), (0.07, 0.06, 0.018), M_CHIP)
    text("HW2_Voltage_Label", "V GRID/PV", (vx, vy - 0.09, z + 0.048), 0.034, M_CARD_TEXT)

    # PV voltage/current sensor, right side.
    sx, sy = x + 0.31, y - 0.02
    mesh_box("HW2_Solar_PCB", (sx, sy, z), (0.27, 0.12, 0.022), M_PCB_BLUE, bevel=0.006)
    mesh_box("HW2_Solar_Terminal", (sx + 0.095, sy, z + 0.034),
             (0.045, 0.09, 0.035), M_TERMINAL_BLUE, bevel=0.004)
    mesh_box("HW2_Solar_Shunt", (sx - 0.04, sy, z + 0.034), (0.07, 0.04, 0.016), M_METAL)
    text("HW2_Solar_Label", "PV V/I", (sx, sy - 0.08, z + 0.048), 0.034, M_CARD_TEXT)

    # Environmental sensor below the PV sensor.
    ex2, ey2 = x + 0.31, y - 0.17
    mesh_box("HW2_Env_PCB", (ex2, ey2, z), (0.25, 0.10, 0.022), M_PCB_TEAL, bevel=0.006)
    mesh_box("HW2_Env_Housing", (ex2 + 0.035, ey2, z + 0.035), (0.09, 0.07, 0.035), M_PCB_BLUE, bevel=0.006)
    for i in range(3):
        mesh_box("HW2_Env_Slot_%d" % i, (ex2 + 0.035, ey2 - 0.025 + i * 0.025, z + 0.056),
                 (0.055, 0.006, 0.004), M_SILVER)
    text("HW2_Env_Label", "TEMP / IRR", (ex2, ey2 - 0.07, z + 0.048), 0.030, M_CARD_TEXT)

    # PSU bottom-left.
    px, py = x - 0.31, y - 0.18
    mesh_box("HW2_PSU_Case", (px, py, z + 0.055), (0.25, 0.15, 0.10), M_PSU, bevel=0.008)
    mesh_box("HW2_PSU_Vent", (px - 0.02, py, z + 0.108), (0.14, 0.11, 0.008), M_METAL)
    for i in range(4):
        for j in range(3):
            cylinder("HW2_PSU_Hole_%d_%d" % (i, j),
                     (px - 0.075 + i * 0.05, py - 0.04 + j * 0.04, z + 0.118),
                     0.006, 0.004, M_CHIP, verts=8)
    mesh_box("HW2_PSU_Caution", (px + 0.015, py - 0.078, z + 0.04),
             (0.11, 0.008, 0.035), M_CAUTION)
    text("HW2_PSU_Label", "12V / 5V PSU", (px, py - 0.115, z + 0.05), 0.032, M_CARD_TEXT)

    # Four-channel relay bank, bottom-right.
    rx, ry = x + 0.20, y - 0.18
    mesh_box("HW2_Relay_PCB", (rx, ry, z), (0.36, 0.15, 0.022), M_PCB_GREEN, bevel=0.006)
    for i in range(4):
        relay_x = rx - 0.135 + i * 0.09
        mesh_box("HW2_Relay_%d" % (i + 1), (relay_x, ry, z + 0.048),
                 (0.065, 0.10, 0.065), M_RELAY, bevel=0.006)
        cylinder("HW2_Relay_LED_%d" % (i + 1), (relay_x, ry - 0.055, z + 0.087),
                 0.009, 0.008, M_GREEN_LED, rotation=(math.pi / 2, 0, 0), verts=8)
    mesh_box("HW2_Relay_Terminals", (rx, ry - 0.068, z + 0.022),
             (0.33, 0.025, 0.028), M_TERMINAL, bevel=0.004)
    text("HW2_Relay_Label", "R1  R2  R3  R4", (rx, ry + 0.09, z + 0.058), 0.034, M_CARD_TEXT)

    # Internal colored signal/power harness.
    curve("HW2_Internal_Power", [(px + 0.12, py, z + 0.08),
                                  (x - 0.10, y - 0.07, z + 0.09),
                                  (ex - 0.10, ey - 0.03, z + 0.06)], M_RED, 0.009)
    curve("HW2_Internal_Sensors", [(cx + 0.08, cy, z + 0.055),
                                    (vx + 0.08, vy, z + 0.055),
                                    (ex - 0.11, ey, z + 0.055)], M_BLUE, 0.007)
    curve("HW2_Internal_LCD", [(ex + 0.11, ey + 0.02, z + 0.058),
                                (lx - 0.11, ly, z + 0.058)], M_YELLOW, 0.007)
    curve("HW2_Internal_Relays", [(ex + 0.06, ey - 0.08, z + 0.058),
                                   (rx - 0.10, ry + 0.04, z + 0.058)], M_ORANGE, 0.008)
    curve("HW2_Internal_PV", [(sx - 0.08, sy, z + 0.058),
                               (ex + 0.11, ey - 0.02, z + 0.058)], M_RED, 0.007)

    # External cable glands and stubs at the enclosure base.
    glands = [
        ("SOLAR INPUT", -0.36, M_RED),
        ("BATTERY INPUT", -0.12, M_RED),
        ("AC LOAD OUTPUT", 0.12, M_BLACK),
        ("GRID INPUT", 0.36, M_BLUE),
    ]
    for i, (label, dx, wire_mat) in enumerate(glands):
        gx = x + dx
        cylinder("HW2_Gland_%d" % i, (gx, y - 0.31, 0.43), 0.032, 0.07,
                 M_BLACK, rotation=(math.pi / 2, 0, 0), verts=12)
        cylinder("HW2_Gland_Cable_%d" % i, (gx, y - 0.37, 0.43), 0.015, 0.12,
                 wire_mat, rotation=(math.pi / 2, 0, 0), verts=8)
        text("HW2_Gland_Label_%d" % i, label, (gx, y - 0.47, 0.13),
             size=0.036, mat=M_CARD_SUB)

    # Exterior status LEDs on the front face.
    for name, dx, mat in (("Active", -0.10, M_GREEN_LED), ("Fault", 0.10, M_RED_LED)):
        cylinder("HW2_Control_LED_" + name, (x + dx, y - 0.315, 0.72), 0.023, 0.022,
                 mat, rotation=(math.pi / 2, 0, 0), verts=12)

    # The scene's existing animated intro label already names this asset as
    # "CONTROL UNIT — ESP32" in the same floating-text style as the buildings
    # and transformer.  Do not add a board/card callout here.


def build_inverter():
    x, y = -1.0, -2.0
    base = 0.40
    cylinder("HW2_Inverter_Post", (x, y, 0.18), 0.055, 0.36, M_METAL, verts=12)
    # Rear heatsink body plus white front shell, same footprint as the old box.
    mesh_box("HW2_Inverter_Rear", (x, y + 0.045, 0.82), (0.58, 0.30, 0.84), M_DARK, bevel=0.035)
    mesh_box("HW2_Inverter_Front", (x, y - 0.065, 0.82), (0.58, 0.22, 0.84), M_WHITE, bevel=0.035)
    # Side cooling ribs.
    for i in range(6):
        z = 0.53 + i * 0.115
        mesh_box("HW2_Inverter_Vent_L_%d" % i, (x - 0.305, y + 0.04, z),
                 (0.018, 0.20, 0.035), M_SILVER)
        mesh_box("HW2_Inverter_Vent_R_%d" % i, (x + 0.305, y + 0.04, z),
                 (0.018, 0.20, 0.035), M_SILVER)
    # Reference-style green status stripe and display.
    mesh_box("HW2_Inverter_Stripe", (x, y - 0.181, 0.70), (0.51, 0.014, 0.028),
             M_GREEN_LED, bevel=0.006)
    mesh_box("HW2_Inverter_Bezel", (x, y - 0.181, 1.02), (0.25, 0.014, 0.19),
             M_DARK, bevel=0.008)
    mesh_box("HW2_Inverter_Screen", (x, y - 0.193, 1.045), (0.18, 0.008, 0.095),
             M_INV_SCREEN, bevel=0.003)
    text("HW2_Inverter_Readout", "MPPT  DC→AC", (x, y - 0.205, 1.045),
         0.026, M_CARD_TEXT)
    for i, dx in enumerate((-0.07, -0.023, 0.023, 0.07)):
        cylinder("HW2_Inverter_Button_%d" % i, (x + dx, y - 0.198, 0.91),
                 0.012, 0.012, M_SILVER, rotation=(math.pi / 2, 0, 0), verts=8)
    for dx in (-0.23, 0.23):
        cylinder("HW2_Inverter_Bolt_%s" % dx, (x + dx, y - 0.20, 0.48),
                 0.014, 0.012, M_SILVER, rotation=(math.pi / 2, 0, 0), verts=8)

    # Keep the exact existing DC and AC curve endpoints as the connector locations.
    cylinder("HW2_Inverter_DC_Port", (x, y - 0.105, 0.43), 0.031, 0.08,
             M_BLACK, rotation=(math.pi / 2, 0, 0), verts=10)
    cylinder("HW2_Inverter_AC_Port", (x + 0.10, y + 0.195, 0.43), 0.031, 0.08,
             M_BLACK, rotation=(math.pi / 2, 0, 0), verts=10)
    text("HW2_Inverter_DC", "DC IN", (x - 0.13, y - 0.23, 0.16), 0.042, M_CARD_SUB)
    text("HW2_Inverter_AC", "AC OUT", (x + 0.15, y + 0.22, 0.16), 0.042, M_CARD_SUB)

    # Match the scene's other equipment labels: the existing animated pointer
    # supplies the floating "INVERTER + MPPT UNIT" name, while the functions
    # remain plain floating text instead of a board/card callout.
    text("HW2_Inverter_Functions",
         "MPPT CONTROL  •  DC→AC  •  GRID SYNC  •  POWER QUALITY",
         (x + 0.28, y + 0.44, 1.64), 0.048, M_CARD_SUB)


def update_existing_pointer_lines():
    # Existing intro pointers are part of the animated scene style. Reuse them
    # so the local assembly labels continue to appear at the same shot times.
    line = bpy.data.objects.get("Pointer_Intro_Line_ESP32")
    if line and line.type == "CURVE":
        line.data.splines.clear()
        sp = line.data.splines.new("POLY")
        pts = [(-3.0, -1.90, 0.72), (-3.0, -1.90, 1.02),
               (-2.0, -1.90, 1.10), (-1.0, -1.90, 1.02), (-1.0, -1.90, 1.12)]
        sp.points.add(len(pts) - 1)
        for p, point in zip(sp.points, pts):
            p.co = (*point, 1.0)
        line.data.bevel_depth = 0.018
        line.data.materials.clear()
        line.data.materials.append(M_CYAN)
    label = bpy.data.objects.get("Pointer_Intro_Text_ESP32")
    if label and label.type == "FONT":
        label.data.body = "ESP32 MCU • MPPT SENSING"
        label.data.size = 0.075
        label.location = (-2.0, -1.90, 1.12)
        label.data.materials.clear()
        label.data.materials.append(M_CYAN)

    relay_line = bpy.data.objects.get("Pointer_Intro_Line_Relay")
    if relay_line and relay_line.type == "CURVE":
        relay_line.data.materials.clear()
        relay_line.data.materials.append(M_CARD_SUB)
    relay_label = bpy.data.objects.get("Pointer_Intro_Text_Relay")
    if relay_label and relay_label.type == "FONT":
        relay_label.data.body = "INVERTER + MPPT UNIT"
        relay_label.data.size = 0.075


def adjust_circuit_endpoints():
    # Only move the first/last control point to the matching connector; the
    # route and all other control points remain unchanged.
    dc = bpy.data.objects.get("Wire_DC")
    if dc and dc.type == "CURVE" and dc.data.splines:
        sp = dc.data.splines[0]
        if sp.type == "BEZIER":
            sp.bezier_points[-1].co = (-1.0, -2.105, 0.43)
    ac = bpy.data.objects.get("Wire_AC")
    if ac and ac.type == "CURVE" and ac.data.splines:
        sp = ac.data.splines[0]
        if sp.type == "BEZIER":
            sp.bezier_points[0].co = (-0.90, -1.80, 0.43)


def main():
    remove_old_hardware()
    build_control_enclosure()
    build_inverter()
    update_existing_pointer_lines()
    adjust_circuit_endpoints()
    SCENE["hardware_upgrade"] = "Detailed control enclosure + inverter MPPT replacement"
    SCENE["hardware_upgrade_assets"] = "Control Unit — ESP32; Inverter + MPPT Unit"
    SCENE.frame_set(ORIGINAL_FRAME)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    # Render the two existing scene views for visual QA without changing the
    # saved camera or frame state.
    for frame, filename in ((600, "angled_frame600.png"), (2400, "top_down_frame2400.png"),
                            (4781, "top_down_frame4781.png")):
        SCENE.frame_set(frame)
        SCENE.render.resolution_percentage = 100
        SCENE.render.filepath = os.path.join(PREVIEW_DIR, filename)
        bpy.ops.render.render(write_still=True)
    SCENE.frame_set(ORIGINAL_FRAME)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("HARDWARE_UPGRADE_DONE", BLEND_PATH, PREVIEW_DIR)


if __name__ == "__main__":
    main()
