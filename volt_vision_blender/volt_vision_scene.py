"""
Volt Vision — Campus Solar Priority System
Blender scene builder (Blender 3.6+ / 4.x / 5.x, GUI or --background)

Run:
  blender --background --python volt_vision_scene.py
  # saves volt_vision.blend next to this script, prints render info
GUI:
  Scripting tab > Open > Run Script, then Render > Render Animation.
"""

import bpy
import math
import os
import sys

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
RES_X, RES_Y = 1920, 1080
FPS = 24
SHOT_RANGES = {
    "SHOT1_Solar": (1, 100),
    "SHOT2_Controller": (101, 200),
    "SHOT3_Battery": (201, 300),
    "SHOT4_Grid": (301, 400),
    "SHOT5_Buildings": (401, 500),
    "SHOT6_Final": (501, 600),
}
FRAME_END = 600

CAPTIONS = {
    "SHOT1_Solar": "Solar Panel - Rooftop PV Array",
    "SHOT2_Controller": "ESP32 Controller - Real-Time Monitoring and MPPT",
    "SHOT3_Battery": "12V Battery - Backup Storage",
    "SHOT4_Grid": "Grid - Backup Supply",
    "SHOT5_Buildings": "A-Critical / B-Critical / C Non-Critical Auto Load-Shed",
    "SHOT6_Final": "VOLT VISION - Campus Solar Priority System",
}

def script_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # __file__ undefined when pasted into Text editor; fall back
        if bpy.data.filepath:
            return os.path.dirname(os.path.abspath(bpy.data.filepath))
        return os.getcwd()

OUT_DIR = os.path.join(script_dir(), "renders")
os.makedirs(OUT_DIR, exist_ok=True)
BLEND_PATH = os.path.join(script_dir(), "volt_vision.blend")

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def ensure_object_mode():
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        pass

def clear_scene():
    ensure_object_mode()
    try:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    except Exception as e:
        print("clear_scene ops failed:", e)
        for o in list(bpy.data.objects):
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass
    for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                 bpy.data.images, bpy.data.lights, bpy.data.cameras,
                 bpy.data.curves if hasattr(bpy.data, "curves") else None]:
        if coll is None:
            continue
        for x in list(coll):
            if getattr(x, "users", 1) == 0:
                try:
                    coll.remove(x)
                except Exception:
                    pass

def new_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c

def link(obj, coll_name="Assets"):
    coll = new_collection(coll_name)
    try:
        coll.objects.link(obj)
    except RuntimeError:
        pass
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except RuntimeError:
        pass
    except Exception:
        pass
    return obj

def mat_principled(name, base_color=(0.8, 0.8, 0.8, 1.0), metallic=0.0,
                   roughness=0.6, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        try:
            bsdf.inputs["Base Color"].default_value = (*base_color[:3], 1.0)
        except Exception:
            pass
        for key, val in (("Metallic", metallic), ("Roughness", roughness)):
            try:
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = val
            except Exception:
                pass
        try:
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = transmission
        except Exception:
            pass
        if alpha < 1.0:
            try:
                m.blend_method = 'BLEND'
            except Exception:
                pass
            try:
                if "Alpha" in bsdf.inputs:
                    bsdf.inputs["Alpha"].default_value = alpha
            except Exception:
                pass
    return m

def mat_emissive(name, color=(1.0, 0.6, 0.15, 1.0), strength=8.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emis = nodes.new("ShaderNodeEmission")
    emis.name = "Emission"
    try:
        emis.inputs["Color"].default_value = (*color[:3], 1.0)
        emis.inputs["Strength"].default_value = strength
    except Exception:
        pass
    links.new(emis.outputs["Emission"], out.inputs["Surface"])
    return m

def box(name, loc, dims, material=None):
    ensure_object_mode()
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception:
        pass
    if material:
        try:
            o.data.materials.append(material)
        except Exception:
            pass
    return link(o)

def cylinder(name, loc, radius, depth, material=None):
    ensure_object_mode()
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    if material:
        o.data.materials.append(material)
    return link(o)

def sphere(name, loc, radius, material=None):
    ensure_object_mode()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    if material:
        o.data.materials.append(material)
    return link(o)

def plane_text(name, text, loc, size=0.35, color=(1, 1, 1, 1)):
    ensure_object_mode()
    bpy.ops.object.text_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    try:
        o.data.body = text
        o.data.size = size
        o.data.align_x = 'LEFT'
    except Exception as e:
        print("text setup failed:", e)
    m = mat_emissive(name + "_Mat", color=color, strength=3.0)
    try:
        o.data.materials.append(m)
    except Exception:
        pass
    return link(o)

def make_cable(name, p0, p1, sag=0.25, radius=0.02, material=None, flow=False):
    mx = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, min(p0[2], p1[2]) - sag)
    curve_data = bpy.data.curves.new(name + "_data", type='CURVE')
    curve_data.dimensions = '3D'
    try:
        curve_data.bevel_depth = radius
        curve_data.bevel_resolution = 2
    except Exception:
        pass
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    pts = [p0, mx, p1]
    for bp, p in zip(spline.bezier_points, pts):
        bp.co = p
        try:
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
        except Exception:
            pass
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    link(obj)
    if material:
        try:
            obj.data.materials.append(material)
        except Exception:
            pass
    if flow:
        for attr, val in (("bevel_factor_mapping_start", 'SPLINE'),
                          ("bevel_factor_mapping_end", 'SPLINE'),
                          ("use_fill_caps", True)):
            try:
                setattr(obj.data, attr, val)
            except Exception:
                pass
    return obj

# ----------------------------------------------------------------------------
# Render / world / lighting
# ----------------------------------------------------------------------------
def setup_render():
    s = bpy.context.scene
    # Engine: prefer Eevee Next on 4.2+/5.x, fall back gracefully
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        try:
            s.render.engine = eng
            break
        except Exception:
            continue
    print("Render engine:", s.render.engine)
    s.render.resolution_x = RES_X
    s.render.resolution_y = RES_Y
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    # PNG image sequence (reliable on 3.x/4.x/5.x); stitch to MP4 with ffmpeg later.
    try:
        s.render.image_settings.file_format = 'PNG'
        s.render.image_settings.color_mode = 'RGB'
        s.render.image_settings.color_depth = '8'
    except Exception as e:
        print("image_settings:", e)
    s.render.filepath = os.path.join(OUT_DIR, "volt_vision_")
    s.render.fps = FPS
    s.frame_start = 1
    s.frame_end = FRAME_END
    s.frame_current = 1
    try:
        s.view_settings.view_transform = 'Filmic'
    except Exception:
        pass
    try:
        s.view_settings.look = 'Medium Contrast'
    except Exception:
        pass
    try:
        s.view_settings.exposure = -0.4
    except Exception:
        pass
    eevee = getattr(s, "eevee", None)
    if eevee is not None:
        for attr, val in (("taa_render_samples", 64), ("taa_samples", 1),
                          ("use_gtao", True), ("use_bloom", True)):
            try:
                setattr(eevee, attr, val)
            except Exception:
                pass
    print("Output:", s.render.filepath)
    print("NOTE: For max glass/metal realism switch to Cycles, GPU, 128+ samples, Denoise ON.")

def setup_world_daylight():
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("Daylight")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputWorld")
    out.location = (300, 0)
    bg = nodes.new("ShaderNodeBackground")
    bg.location = (100, 0)
    try:
        bg.inputs["Color"].default_value = (0.68, 0.78, 0.90, 1.0)
        bg.inputs["Strength"].default_value = 0.55
    except Exception:
        pass
    sky = nodes.new("ShaderNodeTexSky")
    sky.location = (-100, 0)
    for attr, val in (("sky_type", 'PREETHAM'),):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
    try:
        if "Turbidity" in sky.inputs:
            sky.inputs["Turbidity"].default_value = 3.0
    except Exception:
        pass
    try:
        links.new(sky.outputs["Color"], bg.inputs["Color"])
        links.new(bg.outputs["Background"], out.inputs["Surface"])
    except Exception as e:
        print("world link failed:", e)

def setup_lights():
    ensure_object_mode()
    bpy.ops.object.light_add(type='SUN', location=(8, -6, 10))
    sun = bpy.context.active_object
    sun.name = "Key_Sun"
    try:
        sun.data.energy = 2.6
    except Exception:
        pass
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    link(sun, "Lighting")
    bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
    key = bpy.context.active_object
    key.name = "Soft_Key"
    try:
        key.data.energy = 450
        key.data.size = 4.0
        key.data.color = (1.0, 0.96, 0.9)
    except Exception as e:
        print("key light:", e)
    link(key, "Lighting")
    bpy.ops.object.light_add(type='AREA', location=(-5, 4, 4))
    fill = bpy.context.active_object
    fill.name = "Fill"
    try:
        fill.data.energy = 160
        fill.data.size = 5.0
        fill.data.color = (0.85, 0.9, 1.0)
    except Exception as e:
        print("fill light:", e)
    link(fill, "Lighting")

# ----------------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------------
def build_courtyard(mats):
    g = box("Courtyard_Ground", (0, 0, -0.05), (26, 20, 0.1), mats["concrete"])
    for i in range(-5, 6):
        box(f"TileStrip_{i}", (i * 2.2, 0, 0.005), (0.04, 20, 0.012), mats["tile_line"])
    roof = box("Rooftop_Slab", (-6.5, 2.5, 1.0), (7, 6, 0.3), mats["rooftop"])
    box("Parapet_N", (-6.5, 5.4, 1.35), (7, 0.15, 0.5), mats["parapet"])
    box("Parapet_S", (-6.5, -0.4, 1.35), (7, 0.15, 0.5), mats["parapet"])
    wall = box("Grid_Wall", (6.5, 5.5, 1.5), (0.3, 6, 3.0), mats["parapet"])
    return {"ground": g, "roof": roof, "wall": wall}

def build_solar_panel(mats):
    grp = bpy.data.objects.new("PV_Group", None)
    bpy.context.scene.collection.objects.link(grp)
    link(grp)
    grp.location = (-6.5, 2.5, 1.15)
    rail_mat = mats["aluminum"]
    for dx in (-1.4, 1.4):
        leg_f = box(f"PV_Leg_F_{dx}", (0, 0, 0), (0.08, 0.08, 1.0), rail_mat)
        leg_f.parent = grp
        leg_f.location = (dx, 0.7, 0.5)
        leg_b = box(f"PV_Leg_B_{dx}", (0, 0, 0), (0.08, 0.08, 1.6), rail_mat)
        leg_b.parent = grp
        leg_b.location = (dx, -0.7, 0.8)
    panel_holder = bpy.data.objects.new("PV_PanelHolder", None)
    bpy.context.scene.collection.objects.link(panel_holder)
    link(panel_holder)
    panel_holder.parent = grp
    panel_holder.location = (0, 0, 1.15)
    panel_holder.rotation_euler = (math.radians(30), 0, 0)  # ~30deg tilt, cells face south/courtyard cameras
    back = box("PV_Backsheet", (0, 0, 0), (3.4, 2.4, 0.06), mats["pv_back"])
    back.parent = panel_holder
    back.location = (0, 0, 0)
    for name, loc, dim in [
        ("PV_Border_N", (0, 1.2, 0), (3.5, 0.08, 0.1)),
        ("PV_Border_S", (0, -1.2, 0), (3.5, 0.08, 0.1)),
        ("PV_Border_E", (1.7, 0, 0), (0.08, 2.5, 0.1)),
        ("PV_Border_W", (-1.7, 0, 0), (0.08, 2.5, 0.1)),
    ]:
        b = box(name, (0, 0, 0), dim, rail_mat)
        b.parent = panel_holder
        b.location = loc
    for cx in range(4):
        for cy in range(3):
            x = -1.2 + cx * 0.8
            y = -0.75 + cy * 0.75
            cell = box(f"PV_Cell_{cx}_{cy}", (0, 0, 0), (0.7, 0.65, 0.02), mats["pv_glass"])
            cell.parent = panel_holder
            cell.location = (x, y, 0.045)
            for f in (-0.2, 0.0, 0.2):
                finger = box(f"PV_Finger_{cx}_{cy}_{f}", (0, 0, 0), (0.015, 0.65, 0.005), mats["busbar"])
                finger.parent = panel_holder
                finger.location = (x + f, y, 0.058)
    ctrl = box("ChargeController_Box", (0, 0, 0), (1.2, 0.8, 1.0), mats["abs_white"])
    ctrl.parent = grp
    ctrl.location = (2.9, -0.6, 0.5)
    lid = box("ChargeController_Lid", (0, 0, 0), (1.24, 0.84, 0.06), mats["abs_grey"])
    lid.parent = grp
    lid.location = (2.9, -0.6, 1.02)
    return {"group": grp, "panel_holder": panel_holder,
            "pv_top": (-6.5, 2.5, 2.6), "ctrl_top": (-3.6, 1.9, 2.1),
            "ctrl_pos": (-3.6, 1.9, 1.65)}

def build_controller_interior(mats, ctrl_pos):
    cx, cy, cz = ctrl_pos
    enclosure = bpy.data.objects.get("ChargeController_Box")
    if enclosure:
        try:
            enclosure.data.materials.clear()
            enclosure.data.materials.append(mats["abs_translucent"])
        except Exception:
            pass
    box("CTRL_BasePlate", (cx, cy, cz - 0.3), (1.0, 0.6, 0.04), mats["pcb_green"])
    box("ESP32_Board", (cx - 0.22, cy + 0.05, cz - 0.2), (0.32, 0.5, 0.04), mats["pcb_blue"])
    box("ESP32_USB", (cx - 0.22, cy + 0.32, cz - 0.17), (0.08, 0.08, 0.05), mats["aluminum"])
    for side in (-0.14, 0.14):
        box(f"ESP32_Pins_{side}", (cx - 0.22 + side, cy + 0.05, cz - 0.17), (0.03, 0.44, 0.05), mats["pin_gold"])
    plane_text("Label_ESP32", "ESP32", (cx - 0.42, cy - 0.28, cz - 0.1), size=0.12)
    box("CN3791_MPPT", (cx + 0.22, cy + 0.1, cz - 0.2), (0.28, 0.34, 0.05), mats["pcb_red"])
    cylinder("MPPT_Inductor", (cx + 0.22, cy + 0.1, cz - 0.14), 0.06, 0.08, mats["pin_gold"])
    box("MPPT_Terminal", (cx + 0.22, cy + 0.28, cz - 0.15), (0.2, 0.08, 0.08), mats["abs_grey"])
    plane_text("Label_MPPT", "CN3791 MPPT", (cx + 0.02, cy - 0.28, cz - 0.1), size=0.1)
    for i, dx in enumerate((-0.3, 0.3)):
        box(f"ACS712_{i}", (cx + dx, cy - 0.2, cz - 0.2), (0.14, 0.1, 0.06), mats["pcb_green"])
        plane_text(f"Label_ACS{i}", "ACS712", (cx + dx - 0.1, cy - 0.32, cz - 0.12), size=0.08)
    for i, dx in enumerate((-0.12, 0.12)):
        box(f"ZMPT101B_{i}", (cx + dx, cy - 0.05, cz - 0.16), (0.1, 0.12, 0.12), mats["zmpt_blue"])
        plane_text(f"Label_ZMPT{i}", "ZMPT101B", (cx + dx - 0.1, cy - 0.13, cz - 0.05), size=0.06)
    box("LCD_Bezel", (cx, cy - 0.42, cz - 0.1), (0.7, 0.04, 0.3), mats["abs_black"])
    box("LCD_Screen", (cx, cy - 0.44, cz - 0.1), (0.6, 0.02, 0.22), mats["lcd"])
    plane_text("LCD_Text1", "13.8V  4.2A", (cx - 0.27, cy - 0.46, cz - 0.05), size=0.09, color=(0.1, 1.0, 0.4, 1))
    plane_text("LCD_Text2", "MPPT  SOLAR", (cx - 0.27, cy - 0.46, cz - 0.16), size=0.09, color=(0.1, 1.0, 0.4, 1))
    led = sphere("Status_LED", (cx + 0.4, cy - 0.35, cz + 0.05), 0.045, mats["led_red"])
    try:
        emis_node = led.data.materials[0].node_tree.nodes.get("Emission")
        if emis_node is None:
            raise AttributeError("no Emission node")
        for f in range(1, FRAME_END + 1, 12):
            emis_node.inputs["Strength"].default_value = 12.0
            emis_node.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f)
            emis_node.inputs["Strength"].default_value = 0.5
            emis_node.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f + 6)
    except Exception as e:
        print("LED blink fallback (scale):", e)
        for f in range(1, FRAME_END + 1, 12):
            led.scale = (1.0, 1.0, 1.0)
            led.keyframe_insert(data_path="scale", frame=f)
            led.scale = (0.6, 0.6, 0.6)
            led.keyframe_insert(data_path="scale", frame=f + 6)
    make_cable("W_PV_to_MPPT", (cx + 0.22, cy + 0.25, cz - 0.15), (cx - 0.22, cy + 0.25, cz - 0.15), sag=-0.08, radius=0.012, material=mats["wire_red"])
    make_cable("W_MPPT_to_ESP", (cx + 0.1, cy + 0.1, cz - 0.15), (cx - 0.08, cy + 0.05, cz - 0.15), sag=-0.06, radius=0.01, material=mats["wire_yellow"])
    make_cable("W_ESP_to_LCD", (cx - 0.22, cy - 0.15, cz - 0.18), (cx, cy - 0.4, cz - 0.15), sag=-0.05, radius=0.01, material=mats["wire_black"])
    return {"led": led}

def build_battery(mats, ctrl_top):
    bx, by = -3.4, -1.2
    box("Battery_Cabinet", (bx, by, 1.35), (1.4, 0.9, 1.1), mats["abs_grey"])
    box("Battery_12V", (bx, by, 1.3), (1.0, 0.6, 0.6), mats["battery_green"])
    plane_text("Label_12V", "12V BACKUP", (bx - 0.4, by - 0.48, 1.6), size=0.14)
    for i in range(4):
        box(f"BAT_LED_{i}", (bx - 0.3 + i * 0.2, by - 0.46, 1.55), (0.1, 0.03, 0.08), mats["led_green"])
    box("Battery_Handle", (bx, by, 1.65), (0.6, 0.1, 0.05), mats["abs_black"])
    make_cable("Cable_Batt_to_Ctrl", (bx, by + 0.45, 1.5), ctrl_top, sag=0.35, radius=0.025, material=mats["flow_green"])
    return {"pos": (bx, by, 1.5)}

def build_grid(mats, wall_obj=None):
    wx = 6.5
    box("Grid_Meter", (wx - 0.25, 4.5, 1.8), (0.35, 0.7, 0.9), mats["abs_white"])
    box("Meter_Glass", (wx - 0.44, 4.5, 1.9), (0.02, 0.4, 0.4), mats["glass"])
    box("Meter_Dial", (wx - 0.42, 4.5, 1.75), (0.03, 0.3, 0.15), mats["lcd"])
    plane_text("Label_Meter", "GRID METER", (wx - 0.5, 4.1, 2.4), size=0.14)
    box("Breaker_Panel", (wx - 0.25, 6.0, 1.7), (0.35, 0.8, 1.0), mats["abs_grey"])
    for i in range(3):
        box(f"Breaker_SW_{i}", (wx - 0.44, 5.8 + i * 0.2, 1.7), (0.04, 0.1, 0.12), mats["abs_black"])
    plane_text("Label_Breaker", "BREAKER", (wx - 0.5, 5.6, 2.35), size=0.14)
    cylinder("Power_Pole", (11.5, 8.5, 3.0), 0.14, 6.0, mats["wood"])
    box("Pole_Crossarm", (11.5, 8.5, 5.2), (1.6, 0.12, 0.12), mats["wood"])
    for dx in (-0.6, 0.6):
        cylinder(f"Insulator_{dx}", (11.5 + dx, 8.5, 5.3), 0.06, 0.15, mats["abs_black"])
    make_cable("Conduit_Wall_to_Pole", (wx + 0.1, 6.5, 2.2), (11.5, 8.5, 5.0), sag=0.8, radius=0.045, material=mats["conduit"])
    make_cable("DropLine_1", (10.9, 8.5, 5.2), (wx + 0.1, 5.5, 2.4), sag=0.9, radius=0.018, material=mats["flow_purple"])
    make_cable("Cable_Ctrl_to_Grid", (-3.6, 1.9, 1.6), (wx - 0.3, 5.2, 1.4), sag=0.6, radius=0.025, material=mats["flow_purple"])
    return {"meter_pos": (wx - 0.25, 4.5, 1.8), "pole_pos": (11.5, 8.5, 3.0)}

def build_buildings(mats):
    positions = {"A": (-1.0, 7.5), "B": (2.5, 7.8), "C": (6.0, 7.2)}
    sizes = {"A": (3.2, 2.6, 2.6), "B": (3.6, 2.8, 3.2), "C": (3.0, 2.4, 2.2)}
    ctrl = (-3.6, 1.9, 1.6)
    for tag, (px, py) in positions.items():
        sx, sy, sz = sizes[tag]
        box(f"Building_{tag}", (px, py, sz / 2), (sx, sy, sz), mats["bldg"])
        box(f"Building_{tag}_Roof", (px, py, sz + 0.08), (sx + 0.2, sy + 0.2, 0.16), mats["rooftop"])
        plane_text(f"Label_Bldg_{tag}", tag, (px - 0.3, py - sy / 2 - 0.35, sz + 0.6), size=0.6)
        is_critical = tag in ("A", "B")
        base_mat = mats["win_lit"] if is_critical else mats["win_c"]
        for r in range(2):
            for c in range(4):
                wx = px - sx / 2 + 0.5 + c * 0.7
                wy = py - sy / 2 - 0.012
                wz = 0.9 + r * 0.9
                box(f"Win_{tag}_{r}_{c}", (wx, wy, wz), (0.45, 0.03, 0.55), base_mat)
        flow = mats["flow_amber"] if is_critical else mats["flow_amber_c"]
        make_cable(f"Cable_Ctrl_to_{tag}", ctrl, (px, py - sy / 2, 0.4), sag=0.3, radius=0.022, material=flow)
    mat_c = mats["win_c"]
    try:
        node = mat_c.node_tree.nodes.get("Emission")
        if node is not None:
            for f, s in [(401, 10.0), (440, 10.0), (480, 0.15), (500, 0.15)]:
                node.inputs["Strength"].default_value = s
                node.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f)
    except Exception as e:
        print("Building-C dimming failed:", e)

def build_power_flow(mats, pts):
    flows = [
        ("Flow_Solar", pts["pv_top"], pts["ctrl_top"], mats["flow_amber_glow"], 0.022),
        ("Flow_Batt", pts["batt"], pts["ctrl"], mats["flow_green_glow"], 0.022),
        ("Flow_Grid", pts["meter"], pts["ctrl"], mats["flow_purple_glow"], 0.022),
        ("Flow_A", pts["ctrl"], (-1.0, 6.0, 0.6), mats["flow_amber_glow"], 0.022),
        ("Flow_B", pts["ctrl"], (2.5, 6.2, 0.6), mats["flow_amber_glow"], 0.022),
        ("Flow_C", pts["ctrl"], (6.0, 5.8, 0.6), mats["flow_amber_glow"], 0.022),
    ]
    for name, a, b, m, r in flows:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, max(a[2], b[2]) + 0.25)
        make_cable(name, a, mid, sag=-0.25, radius=r, material=m, flow=True)
        make_cable(name + "_b", mid, b, sag=0.1, radius=r, material=m, flow=True)
    for o in bpy.data.objects:
        if o.name.startswith("Flow_") and o.type == 'CURVE':
            try:
                o.data.bevel_factor_end = 0.0
                o.data.keyframe_insert(data_path="bevel_factor_end", frame=501)
                o.data.bevel_factor_end = 1.0
                o.data.keyframe_insert(data_path="bevel_factor_end", frame=600)
            except Exception:
                pass
    # NOTE: title card + corner captions are burned in post (ffmpeg drawtext)
    # so the 3D scene stays clean from every angle. See make_video.py.

# ----------------------------------------------------------------------------
# Cameras + captions
# ----------------------------------------------------------------------------
def make_camera(name, loc, rot_euler_deg, focal_mm, dof=False, focus_obj=None):
    cam_data = bpy.data.cameras.new(name)
    try:
        cam_data.lens = focal_mm
    except Exception:
        pass
    cam_obj = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    link(cam_obj, "Cameras")
    cam_obj.location = loc
    cam_obj.rotation_euler = tuple(math.radians(a) for a in rot_euler_deg)
    if dof:
        try:
            cam_data.dof.use_dof = True
            if focus_obj is not None:
                cam_data.dof.focus_object = focus_obj
            cam_data.dof.aperture_fstop = 2.8
        except Exception as e:
            print("DoF setup failed:", e)
    return cam_obj

def add_caption_rig(cam_obj, text):
    ensure_object_mode()
    bpy.ops.mesh.primitive_plane_add(size=1)
    bg = bpy.context.active_object
    bg.name = f"CaptionBG_{cam_obj.name}"
    try:
        bg.scale = (1.6, 0.22, 1)
    except Exception:
        pass
    bg.location = (-1.15, -0.72, -2.0)
    m = mat_principled(f"CapBG_{cam_obj.name}", base_color=(0, 0, 0, 1), roughness=0.9)
    try:
        bg.data.materials.append(m)
    except Exception:
        pass
    bg.parent = cam_obj
    link(bg, "Captions")
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.active_object
    t.name = f"Caption_{cam_obj.name}"
    try:
        t.data.body = text
        t.data.size = 0.075
        t.data.align_x = 'LEFT'
    except Exception:
        pass
    t.location = (-1.85, -0.68, -1.99)
    t.data.materials.append(mat_emissive(f"CapTx_{cam_obj.name}", color=(1, 1, 1, 1), strength=4.0))
    t.parent = cam_obj
    link(t, "Captions")
    return bg, t

def _track_to(cam_obj, target_obj):
    try:
        con = cam_obj.constraints.new(type='TRACK_TO')
        con.target = target_obj
        con.track_axis = 'TRACK_NEGATIVE_Z'
        con.up_axis = 'UP_Y'
    except Exception as e:
        print("track_to failed:", e)

def _empty_at(name, loc):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    link(e, "Cameras")
    e.location = loc
    return e

def setup_cameras_and_markers(esp_obj):
    scene = bpy.context.scene
    # Focus targets (world-space POIs)
    tgt_solar = _empty_at("Focus_Solar", (-6.5, 2.5, 2.1))
    tgt_ctrl = _empty_at("Focus_Ctrl", (-3.6, 1.9, 1.5))
    tgt_batt = _empty_at("Focus_Batt", (-3.4, -1.2, 1.4))
    tgt_grid = _empty_at("Focus_Grid", (6.25, 5.2, 1.8))
    tgt_bldg = _empty_at("Focus_Bldg", (2.5, 7.5, 1.6))
    tgt_final = _empty_at("Focus_Final", (1.0, 4.0, 1.2))
    cams = {}
    focus_pv = bpy.data.objects.get("PV_Cell_1_1")
    # Pulled-back positions so nothing clips; TRACK_TO keeps framing exact.
    cams["SHOT1_Solar"] = make_camera("CAM_Solar", (-3.4, -1.8, 3.4), (68, 0, 8), 45, dof=True, focus_obj=focus_pv)
    cams["SHOT2_Controller"] = make_camera("CAM_Controller", (-1.9, 0.0, 2.5), (72, 0, -18), 40, dof=True, focus_obj=esp_obj)
    cams["SHOT3_Battery"] = make_camera("CAM_Battery", (-1.4, -3.0, 2.5), (65, 0, 12), 38, dof=True)
    cams["SHOT4_Grid"] = make_camera("CAM_Grid", (3.6, 2.6, 2.5), (66, 0, 55), 35, dof=True)
    cams["SHOT5_Buildings"] = make_camera("CAM_Buildings", (2.5, 0.8, 4.8), (62, 0, 0), 26, dof=False)
    cams["SHOT6_Final"] = make_camera("CAM_Final", (2.5, -8.5, 9.0), (58, 0, 0), 24, dof=False)
    _track_to(cams["SHOT1_Solar"], tgt_solar)
    _track_to(cams["SHOT2_Controller"], tgt_ctrl)
    _track_to(cams["SHOT3_Battery"], tgt_batt)
    _track_to(cams["SHOT4_Grid"], tgt_grid)
    _track_to(cams["SHOT5_Buildings"], tgt_bldg)
    _track_to(cams["SHOT6_Final"], tgt_final)
    moves = {
        # lateral glide: start -> end (TRACK_TO keeps subject centered)
        "SHOT1_Solar": [(1, (-3.4, -1.8, 3.4)), (100, (-1.8, -1.8, 3.2))],
        "SHOT2_Controller": [(101, (-1.9, 0.0, 2.5)), (200, (-1.3, 0.5, 2.3))],
        "SHOT3_Battery": [(201, (-1.4, -3.0, 2.5)), (300, (-2.0, -2.4, 2.3))],
        "SHOT4_Grid": [(301, (3.6, 2.6, 2.5)), (400, (4.6, 3.2, 2.7))],
        "SHOT5_Buildings": [(401, (2.5, 0.8, 4.8)), (500, (2.5, -0.2, 5.2))],
        "SHOT6_Final": [(501, (2.5, -8.5, 9.0)), (600, (2.5, -12.0, 11.0))],
    }
    for shot, cam in cams.items():
        for f, loc in moves[shot]:
            cam.location = loc
            try:
                cam.keyframe_insert(data_path="location", frame=f)
            except Exception as e:
                print("cam keyframe failed:", e)
        try:
            if cam.animation_data and cam.animation_data.action:
                for fc in cam.animation_data.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'BEZIER'
        except Exception:
            pass
    for shot, (f0, f1) in SHOT_RANGES.items():
        try:
            mk = scene.timeline_markers.new(shot, frame=f0)
            # Blender <=4.x: camera_data, Blender 5.x: camera
            try:
                mk.camera_data = cams[shot]
            except AttributeError:
                mk.camera = cams[shot]
        except Exception as e:
            print("marker failed:", e)
    # bind_camera operator needs GUI context; markers already carry camera_data
    if not bpy.app.background:
        for shot, (f0, f1) in SHOT_RANGES.items():
            try:
                scene.frame_current = f0
                bpy.context.view_layer.objects.active = cams[shot]
                bpy.ops.marker.bind_camera()
            except Exception:
                pass
    scene.frame_current = 1
    try:
        scene.camera = cams["SHOT1_Solar"]
    except Exception:
        pass
    # Corner captions + title card are added in post (ffmpeg) for crisp text.
    return cams

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    print("Blender", bpy.app.version_string, "background:", bpy.app.background)
    clear_scene()
    setup_render()
    setup_world_daylight()
    setup_lights()
    mats = {
        "concrete": mat_principled("Concrete", (0.62, 0.62, 0.6), roughness=0.95),
        "tile_line": mat_principled("TileLine", (0.3, 0.3, 0.3), roughness=0.9),
        "rooftop": mat_principled("Rooftop", (0.55, 0.55, 0.57), roughness=0.85),
        "parapet": mat_principled("Parapet", (0.82, 0.8, 0.76), roughness=0.9),
        "aluminum": mat_principled("AnodizedAlu", (0.75, 0.77, 0.8), metallic=0.9, roughness=0.35),
        "pv_back": mat_principled("PVBack", (0.12, 0.13, 0.15), roughness=0.6),
        "pv_glass": mat_principled("PVGlass", (0.02, 0.10, 0.38), metallic=0.35, roughness=0.18, transmission=0.0),
        "busbar": mat_principled("Busbar", (0.85, 0.85, 0.88), metallic=1.0, roughness=0.25),
        "abs_white": mat_principled("ABS_White", (0.92, 0.92, 0.93), roughness=0.55),
        "abs_grey": mat_principled("ABS_Grey", (0.45, 0.46, 0.48), roughness=0.6),
        "abs_black": mat_principled("ABS_Black", (0.05, 0.05, 0.06), roughness=0.5),
        "abs_translucent": mat_principled("ABS_Trans", (0.9, 0.9, 0.92), roughness=0.4, alpha=0.45),
        "glass": mat_principled("Glass", (0.8, 0.9, 0.95), roughness=0.05, transmission=0.9),
        "pcb_blue": mat_principled("PCB_Blue", (0.08, 0.2, 0.65), roughness=0.5),
        "pcb_red": mat_principled("PCB_Red", (0.6, 0.08, 0.08), roughness=0.5),
        "pcb_green": mat_principled("PCB_Green", (0.05, 0.35, 0.12), roughness=0.5),
        "pin_gold": mat_principled("PinGold", (0.85, 0.65, 0.2), metallic=1.0, roughness=0.3),
        "zmpt_blue": mat_principled("ZMPT_Blue", (0.1, 0.25, 0.7), roughness=0.45),
        "battery_green": mat_principled("BattGreen", (0.1, 0.4, 0.15), roughness=0.55),
        "bldg": mat_principled("Bldg", (0.86, 0.82, 0.74), roughness=0.9),
        "wood": mat_principled("Wood", (0.35, 0.22, 0.12), roughness=0.9),
        "conduit": mat_principled("Conduit", (0.3, 0.3, 0.32), metallic=0.6, roughness=0.5),
        "wire_red": mat_emissive("WireRed", (0.9, 0.1, 0.1), 1.2),
        "wire_black": mat_principled("WireBlack", (0.04, 0.04, 0.04), roughness=0.7),
        "wire_yellow": mat_emissive("WireYel", (1.0, 0.85, 0.1), 1.2),
        "lcd": mat_emissive("LCD", (0.05, 0.5, 0.2), 2.5),
        "led_red": mat_emissive("LED_Red", (1.0, 0.08, 0.08), 12.0),
        "led_green": mat_emissive("LED_Green", (0.1, 1.0, 0.3), 8.0),
        "win_lit": mat_emissive("WinLit", (1.0, 0.62, 0.18), 10.0),
        "win_c": mat_emissive("WinC", (1.0, 0.62, 0.18), 10.0),
        "flow_amber": mat_principled("CableAmber", (0.25, 0.18, 0.1), roughness=0.6),
        "flow_amber_c": mat_principled("CableAmberC", (0.25, 0.18, 0.1), roughness=0.6),
        "flow_green": mat_principled("CableGreen", (0.1, 0.25, 0.12), roughness=0.6),
        "flow_purple": mat_principled("CablePurple", (0.2, 0.12, 0.3), roughness=0.6),
        "flow_amber_glow": mat_emissive("FlowAmber", (1.0, 0.55, 0.1), 6.0),
        "flow_green_glow": mat_emissive("FlowGreen", (0.15, 1.0, 0.4), 6.0),
        "flow_purple_glow": mat_emissive("FlowPurple", (0.65, 0.3, 1.0), 6.0),
    }
    env = build_courtyard(mats)
    solar = build_solar_panel(mats)
    build_controller_interior(mats, solar["ctrl_pos"])
    batt = build_battery(mats, solar["ctrl_top"])
    grid = build_grid(mats, env["wall"])
    build_buildings(mats)
    build_power_flow(mats, {
        "pv_top": solar["pv_top"],
        "ctrl_top": solar["ctrl_top"],
        "ctrl": (-3.6, 1.9, 1.6),
        "batt": batt["pos"],
        "meter": grid["meter_pos"],
    })
    esp_obj = bpy.data.objects.get("ESP32_Board")
    setup_cameras_and_markers(esp_obj)
    bpy.context.view_layer.update()
    print("Objects:", len(bpy.data.objects))
    try:
        bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
        print("Saved:", BLEND_PATH)
    except Exception as e:
        print("Save failed:", e)
    print("=" * 60)
    print("Volt Vision scene built OK.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
