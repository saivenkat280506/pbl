"""Volt Vision RESTRUCTURE patch — modifies volt_vision.blend IN PLACE.
Run: blender --background volt_vision_blender/volt_vision.blend --python volt_vision_blender/restructure.py
Covers: lighting fix, material recolor, wire rebuild + legend, relay conversion,
        transformer can, case presets (scene['volt_case'] + apply_case()).
Does NOT touch: geometry (except small added parts), cameras, timeline.
"""
import bpy, math, os

BLEND_DIR = os.path.dirname(os.path.abspath(bpy.data.filepath))

def mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        print("  MISSING MAT:", name)
    return m

def set_principled(m, color=None, metallic=None, roughness=None):
    if m is None:
        return
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    try:
        if color is not None:
            bsdf.inputs["Base Color"].default_value = (*color[:3], 1.0)
        if metallic is not None and "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if roughness is not None and "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
    except Exception as e:
        print("  set_principled", m.name, e)

def set_emission(m, color=None, strength=None):
    if m is None:
        return
    try:
        n = m.node_tree.nodes.get("Emission")
        if n is not None:
            if color is not None:
                n.inputs["Color"].default_value = (*color[:3], 1.0)
            if strength is not None:
                n.inputs["Strength"].default_value = strength
            return
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None and "Emission Strength" in bsdf.inputs:
            if strength is not None:
                bsdf.inputs["Emission Strength"].default_value = strength
    except Exception as e:
        print("  set_emission", m.name, e)

def link_to(obj, coll_name):
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)
    try:
        coll.objects.link(obj)
    except RuntimeError:
        pass
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except Exception:
        pass
    return obj

def new_box(name, loc, dims, material=None):
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception:
        pass
    if material is not None:
        o.data.materials.append(material)
    return link_to(o, "Assets")

def new_text(name, text, loc, size=0.14, rgb=(1, 1, 1)):
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.text_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.body = text
    o.data.size = size
    o.data.align_x = 'LEFT'
    m = bpy.data.materials.new(name + "_Mat")
    m.use_nodes = True
    nn = m.node_tree.nodes
    ll = m.node_tree.links
    nn.clear()
    out = nn.new("ShaderNodeOutputMaterial")
    em = nn.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1.0)
    em.inputs["Strength"].default_value = 3.0
    ll.new(em.outputs["Emission"], out.inputs["Surface"])
    o.data.materials.append(m)
    return link_to(o, "Assets")

def new_cable(name, p0, p1, sag=0.3, radius=0.03, material=None, lift=0.0):
    mx = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, min(p0[2], p1[2]) - sag + lift)
    cd = bpy.data.curves.new(name + "_data", type='CURVE')
    cd.dimensions = '3D'
    try:
        cd.bevel_depth = radius
        cd.bevel_resolution = 2
    except Exception:
        pass
    sp = cd.splines.new('BEZIER')
    sp.bezier_points.add(2)
    for bp, p in zip(sp.bezier_points, [p0, mx, p1]):
        bp.co = p
        try:
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
        except Exception:
            pass
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    link_to(o, "Assets")
    if material is not None:
        o.data.materials.append(material)
    return o

# ================================================================ 1. LIGHTING
print("== lighting ==")
sun = bpy.data.objects.get("Key_Sun")
if sun:
    sun.rotation_euler = (math.radians(45), 0, math.radians(35))  # ~45 deg altitude
    try:
        sun.data.energy = 3.0
        sun.data.color = (1.0, 0.95, 0.87)  # ~5500K warm
    except Exception as e:
        print("  sun:", e)
for dead in ("Soft_Key", "Fill"):
    o = bpy.data.objects.get(dead)
    if o:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
            print("  removed area light:", dead)
        except Exception as e:
            print("  remove light failed:", e)
world = bpy.context.scene.world
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type == 'BACKGROUND':
            try:
                n.inputs["Strength"].default_value = 0.75  # soft sky fill
            except Exception:
                pass
        if n.type == 'TEX_SKY':
            try:
                if "Turbidity" in n.inputs:
                    n.inputs["Turbidity"].default_value = 2.2  # bluer sky gradient
            except Exception:
                pass
print("  sun 45deg warm + sky fill 0.75, areas removed")

# ================================================================ 2. GROUND
print("== ground ==")
set_principled(mat("Concrete"), color=(0.78, 0.78, 0.79), roughness=0.95)
set_principled(mat("TileLine"), color=(0.45, 0.45, 0.46), roughness=0.9)

# ================================================================ 3. MATERIALS
print("== materials ==")
set_principled(mat("PVGlass"), color=(0.015, 0.07, 0.30), metallic=0.35, roughness=0.18)
set_principled(mat("Busbar"), color=(0.85, 0.87, 0.90), metallic=1.0, roughness=0.30)
set_principled(mat("AnodizedAlu"), color=(0.82, 0.84, 0.87), metallic=1.0, roughness=0.35)
# Dark solder-mask base ONLY on the controller base plate (ACS712 sensors keep green).
base_obj = bpy.data.objects.get("CTRL_BasePlate")
if base_obj:
    dark = bpy.data.materials.new("PCB_DarkBase")
    dark.use_nodes = True
    _db = dark.node_tree.nodes.get("Principled BSDF")
    _db.inputs["Base Color"].default_value = (0.02, 0.10, 0.05, 1.0)
    try:
        _db.inputs["Metallic"].default_value = 0.2
        _db.inputs["Roughness"].default_value = 0.5
    except Exception:
        pass
    try:
        base_obj.data.materials.clear()
        base_obj.data.materials.append(dark)
    except Exception as e:
        print("  base assign:", e)
# NOTE: no procedural copper-trace texture exists on this board; dark solder-mask
# green-black approximates the requested black-PCB/green-mask look without new geo.
set_principled(mat("ABS_Trans"), color=(0.75, 0.76, 0.78), roughness=0.6)  # vented-plastic grey
m_trans = mat("ABS_Trans")
if m_trans:
    try:
        m_trans.blend_method = 'OPAQUE'
        bsdf = m_trans.node_tree.nodes.get("Principled BSDF")
        if bsdf and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 1.0
    except Exception as e:
        print("  abs_trans opaque:", e)
# transparent window face on controller front
win_face = new_box("CTRL_Window", (-3.6, 1.48, 1.55), (0.9, 0.02, 0.5), mat("Glass"))
print("  controller window:", win_face.name)
# blue status LED next to red one
led_blue_mat = bpy.data.materials.new("LED_Blue")
led_blue_mat.use_nodes = True
_nn = led_blue_mat.node_tree.nodes
_ll = led_blue_mat.node_tree.links
_nn.clear()
_o = _nn.new("ShaderNodeOutputMaterial")
_e = _nn.new("ShaderNodeEmission")
_e.inputs["Color"].default_value = (0.15, 0.4, 1.0, 1.0)
_e.inputs["Strength"].default_value = 10.0
_ll.new(_e.outputs["Emission"], _o.inputs["Surface"])
try:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(-3.1, 1.55, 1.7))
    led2 = bpy.context.active_object
    led2.name = "Status_LED_Blue"
    led2.data.materials.append(led_blue_mat)
    link_to(led2, "Assets")
    print("  added blue status LED")
except Exception as e:
    print("  blue LED failed:", e)

# ---- relay/switching unit conversion (was Battery_Cabinet) ----
cab = bpy.data.objects.get("Battery_Cabinet")
if cab:
    cab.name = "RelayUnit_Cabinet"
    print("  renamed Battery_Cabinet -> RelayUnit_Cabinet")
set_principled(mat("ABS_Grey"), color=(0.72, 0.73, 0.75), metallic=0.85, roughness=0.4)
# copper busbars + black relay coils inside (visible: lid lifted aside)
lid = bpy.data.objects.get("ChargeController_Lid")
relay_lid = bpy.data.objects.get("RelayUnit_Cabinet")
copper = mat("PinGold")
if copper:
    # reuse gold as copper base then tint orange-copper on dedicated mat
    pass
bus_mat = bpy.data.materials.new("BusCopper")
bus_mat.use_nodes = True
_b = bus_mat.node_tree.nodes.get("Principled BSDF")
_b.inputs["Base Color"].default_value = (1.0, 0.42, 0.10, 1.0)
_b.inputs["Metallic"].default_value = 1.0
_b.inputs["Roughness"].default_value = 0.35
for i in range(3):
    new_box(f"Relay_Busbar_{i}", (-3.65 + i * 0.25, -1.2, 1.55), (0.12, 0.7, 0.06), bus_mat)
for i in range(2):
    new_box(f"Relay_Coil_{i}", (-3.55 + i * 0.35, -1.0, 1.25), (0.22, 0.22, 0.3), mat("ABS_Black"))
# open face: shift cabinet lid piece off (was Battery_Handle) + relabel
h = bpy.data.objects.get("Battery_Handle")
if h:
    h.location = (-3.4, -1.75, 1.9)  # lid propped open beside unit
lbl = bpy.data.objects.get("Label_12V")
if lbl:
    try:
        lbl.data.body = "RELAY / SWITCHING"
        print("  relabeled grey box -> RELAY / SWITCHING")
    except Exception as e:
        print("  relabel:", e)
# relocate battery pack + charge LEDs + handle label as separate battery station
for oname, dx in (("Battery_12V", 1.8), ("BAT_LED_0", 1.8), ("BAT_LED_1", 1.8),
                  ("BAT_LED_2", 1.8), ("BAT_LED_3", 1.8)):
    o = bpy.data.objects.get(oname)
    if o:
        o.location.x += dx
new_text("Label_Battery", "12V BATTERY", (-2.0, -1.68, 1.62), size=0.13, rgb=(0.7, 1.0, 0.8))
print("  battery station shifted +X to sit beside relay unit")

# ---- buildings ----
set_principled(mat("Bldg"), color=(0.93, 0.88, 0.78), roughness=0.9)      # warm cream
set_principled(mat("Rooftop"), color=(0.45, 0.53, 0.62), roughness=0.85)  # blue-grey
set_emission(mat("WinLit"), color=(1.0, 0.55, 0.15), strength=14.0)
set_emission(mat("WinC"), color=(1.0, 0.55, 0.15), strength=10.0)
print("  buildings cream/blue-grey, windows brighter warm (critical > non-critical)")

# ---- grid: teal meter, silver conductors, wood pole, ceramic insulators ----
teal = bpy.data.materials.new("TealMetal")
teal.use_nodes = True
_tb = teal.node_tree.nodes.get("Principled BSDF")
_tb.inputs["Base Color"].default_value = (0.10, 0.45, 0.55, 1.0)
_tb.inputs["Metallic"].default_value = 0.6
_tb.inputs["Roughness"].default_value = 0.45
gm = bpy.data.objects.get("Grid_Meter")
if gm:
    try:
        gm.data.materials.clear()
        gm.data.materials.append(teal)
    except Exception as e:
        print("  meter assign:", e)
set_principled(mat("Wood"), color=(0.42, 0.28, 0.15), roughness=0.9)
cer = bpy.data.materials.new("CeramicGrey")
cer.use_nodes = True
_cb = cer.node_tree.nodes.get("Principled BSDF")
_cb.inputs["Base Color"].default_value = (0.60, 0.60, 0.62, 1.0)
_cb.inputs["Roughness"].default_value = 0.4
for iname in ("Insulator_-0.6", "Insulator_0.6"):
    io = bpy.data.objects.get(iname)
    if io:
        try:
            io.data.materials.clear()
            io.data.materials.append(cer)
        except Exception:
            pass
# transformer can on the pole (teal body + fins + bushings)
try:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.0, location=(11.5, 8.0, 4.2))
    tr = bpy.context.active_object
    tr.name = "Transformer_Can"
    tr.data.materials.append(teal)
    link_to(tr, "Assets")
    for i in range(3):
        new_box(f"Transformer_Fin_{i}", (11.5 + (i - 1) * 0.25, 7.62, 4.2), (0.06, 0.12, 0.8), teal)
    for dx in (-0.15, 0.15):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.25, location=(11.5 + dx, 8.0, 4.85))
        bu = bpy.context.active_object
        bu.name = f"Transformer_Bushing_{dx}"
        bu.data.materials.append(cer)
        link_to(bu, "Assets")
    print("  transformer can added on pole")
except Exception as e:
    print("  transformer failed:", e)

# ================================================================ 4. WIRES
print("== wires ==")
deleted, kept = 0, 0
for o in list(bpy.data.objects):
    if o.type != 'CURVE':
        continue
    if o.name.startswith(("W_", "Cable_Ctrl_to_", "Cable_Batt_to_Ctrl", "Cable_Ctrl_to_Grid",
                          "Flow_", "DropLine_")):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
            deleted += 1
        except Exception as e:
            print("  del wire failed:", e)
    elif o.name == "Conduit_Wall_to_Pole":
        kept += 1
print(f"  deleted {deleted} tangled curves, kept {kept} physical conduit")

def emis_mat(name, rgb, s):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nn = m.node_tree.nodes
    ll = m.node_tree.links
    nn.clear()
    o = nn.new("ShaderNodeOutputMaterial")
    e = nn.new("ShaderNodeEmission")
    e.name = "Emission"
    e.inputs["Color"].default_value = (*rgb, 1.0)
    e.inputs["Strength"].default_value = s
    ll.new(e.outputs["Emission"], o.inputs["Surface"])
    return m

matDC = emis_mat("WireDC_Red", (1.0, 0.08, 0.08), 6.0)
matAC = emis_mat("WireAC_Orange", (1.0, 0.45, 0.05), 6.0)
matAC_C = emis_mat("WireAC_Orange_C", (1.0, 0.45, 0.05), 6.0)
matDATA = emis_mat("WireDATA_Green", (0.10, 1.0, 0.35), 5.0)
# grey dashed grid line: wave bands along curve UV -> mix emission/transparent
matGRID = bpy.data.materials.new("WireGRID_Dashed")
matGRID.use_nodes = True
try:
    matGRID.blend_method = 'BLEND'
except Exception:
    pass
gn = matGRID.node_tree.nodes
gl = matGRID.node_tree.links
gn.clear()
gout = gn.new("ShaderNodeOutputMaterial")
gmix = gn.new("ShaderNodeMixShader")
gem = gn.new("ShaderNodeEmission")
gem.inputs["Color"].default_value = (0.55, 0.55, 0.58, 1.0)
gem.inputs["Strength"].default_value = 5.0
gtr = gn.new("ShaderNodeBsdfTransparent")
gtex = gn.new("ShaderNodeTexCoord")
gmap = gn.new("ShaderNodeMapping")
gmap.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
gwave = gn.new("ShaderNodeTexWave")
try:
    gwave.bands_direction = 'X'
    gwave.wave_type = 'BANDS'
except Exception:
    pass
gramp = gn.new("ShaderNodeValToRGB")
try:
    gramp.color_ramp.elements[0].position = 0.45
    gramp.color_ramp.elements[1].position = 0.55
except Exception:
    pass
gl.new(gtex.outputs["UV"], gmap.inputs["Vector"])
gl.new(gmap.outputs["Vector"], gwave.inputs["Vector"])
gl.new(gwave.outputs["Color"], gramp.inputs["Fac"])
gl.new(gramp.outputs["Color"], gmix.inputs["Fac"])
gl.new(gtr.outputs["BSDF"], gmix.inputs[1])
gl.new(gem.outputs["Emission"], gmix.inputs[2])
gl.new(gmix.outputs["Shader"], gout.inputs["Surface"])

PV_TOP = (-6.5, 2.5, 2.6)
CTRL = (-3.6, 1.9, 1.6)
CTRL_TOP = (-3.6, 1.9, 2.1)
METER = (6.25, 4.5, 1.8)
new_cable("DC_Panel_to_Ctrl", PV_TOP, CTRL_TOP, sag=-0.1, radius=0.03, material=matDC, lift=0.35)
new_cable("AC_Ctrl_to_A", CTRL, (-1.0, 6.2, 0.5), sag=0.5, radius=0.028, material=matAC, lift=0.55)
new_cable("AC_Ctrl_to_B", CTRL, (2.5, 6.4, 0.5), sag=0.4, radius=0.028, material=matAC, lift=0.85)
new_cable("AC_Ctrl_to_C", CTRL, (6.0, 6.0, 0.5), sag=0.5, radius=0.028, material=matAC_C, lift=0.35)
new_cable("DATA_Ctrl_to_Relay", CTRL, (-3.4, -1.0, 1.5), sag=0.2, radius=0.012, material=matDATA)
new_cable("DATA_Ctrl_to_Meter", CTRL, METER, sag=0.5, radius=0.012, material=matDATA, lift=0.3)
new_cable("GRID_Ctrl_to_Meter", CTRL, METER, sag=0.6, radius=0.02, material=matGRID, lift=0.15)
new_cable("GRID_Meter_to_Pole", METER, (11.5, 8.5, 5.0), sag=0.8, radius=0.02, material=matGRID)
print("  rebuilt: 1xDC red, 3xAC orange, 2xDATA green, 2xGRID grey-dashed")

# outage X marker at meter (hidden unless grid-outage case)
redx = emis_mat("OutageX_Red", (1.0, 0.1, 0.1), 8.0)
x1 = new_box("GridOutage_X1", METER, (0.5, 0.05, 0.08), redx)
x1.rotation_euler = (0, 0, math.radians(45))
x2 = new_box("GridOutage_X2", METER, (0.5, 0.05, 0.08), redx)
x2.rotation_euler = (0, 0, math.radians(-45))
for x in (x1, x2):
    try:
        x.hide_viewport = True
        x.hide_render = True
    except Exception:
        pass

# ---- legend board, bottom-right of final view ----
lx, ly, lz = 8.5, -1.5, 0.6
board = new_box("Legend_Board", (lx, ly, lz), (2.2, 0.08, 1.1), mat("ABS_White"))
swatches = [("DC power", matDC), ("AC power", matAC), ("Sensor/data", matDATA), ("Grid tie", matGRID)]
for i, (label, m) in enumerate(swatches):
    y = lz + 0.32 - i * 0.22
    new_box(f"Legend_SW_{i}", (lx - 0.8, ly - 0.06, y), (0.4, 0.02, 0.1), m)
    new_text(f"Legend_TX_{i}", label, (lx - 0.5, ly - 0.06, y - 0.06), size=0.11, rgb=(0.1, 0.1, 0.1))
board.rotation_euler = (math.radians(60), 0, math.radians(-15))
print("  legend board placed for final camera")

# ================================================================ 5. CASES
print("== case presets ==")

def apply_case(name):
    s = bpy.context.scene
    s["volt_case"] = name
    grid_objs = [bpy.data.objects.get(n) for n in ("GRID_Ctrl_to_Meter", "GRID_Meter_to_Pole")]
    x_objs = [bpy.data.objects.get(n) for n in ("GridOutage_X1", "GridOutage_X2")]
    cfg = {
        "high_solar": dict(dc=8, ac=8, acc=8, data=6, grid=0.6, wab=14, wc=10, gridvis=True, xvis=False),
        "low_solar": dict(dc=1.5, ac=6, acc=6, data=5, grid=8, wab=10, wc=8, gridvis=True, xvis=False),
        "balanced": dict(dc=5, ac=5, acc=5, data=5, grid=5, wab=12, wc=8, gridvis=True, xvis=False),
        "outage": dict(dc=6, ac=7, acc=0.5, data=5, grid=0, wab=12, wc=0.05, gridvis=False, xvis=True),
    }[name]
    set_emission(matDC, strength=cfg["dc"])
    set_emission(matAC, strength=cfg["ac"])
    set_emission(matAC_C, strength=cfg["acc"])
    set_emission(matDATA, strength=cfg["data"])
    set_emission(matGRID, strength=cfg["grid"] if cfg["gridvis"] else 0)
    set_emission(mat("WinLit"), strength=cfg["wab"])
    # WinC has load-shed keyframes; strip them so preset value holds for case stills
    wc = mat("WinC")
    try:
        if wc and wc.node_tree.animation_data and wc.node_tree.animation_data.action:
            wc.node_tree.animation_data.action.fcurves.clear()
    except Exception as e:
        print("  winc fcurve clear:", e)
    set_emission(wc, strength=cfg["wc"])
    for o in grid_objs:
        if o:
            try:
                o.hide_viewport = not cfg["gridvis"]
                o.hide_render = not cfg["gridvis"]
            except Exception:
                pass
    for o in x_objs:
        if o:
            try:
                o.hide_viewport = not cfg["xvis"]
                o.hide_render = not cfg["xvis"]
            except Exception:
                pass
    print("  case applied:", name)
    return cfg

# expose for ad-hoc toggling: `blender --background volt_vision.blend --python-expr "import bpy; ..."`
apply_case("balanced")

bpy.context.view_layer.update()
print("Objects now:", len(bpy.data.objects))
try:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, "volt_vision.blend"))
    print("Saved volt_vision.blend")
except Exception as e:
    print("Save failed:", e)
