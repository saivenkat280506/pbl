"""Toon/CAD style pass — restyle Volt Vision in place to match reference look:
flat saturated colors, bright midday light, dense panel grid, detailed
transformer + pylon, bold top-corner label bars (burned in video step).
Run: blender --background volt_vision_blender/volt_vision.blend --python volt_vision_blender/toon_style.py
Keeps: layout, cameras, timeline, wire color code, case presets.
"""
import bpy, math, os

def mat(n):
    m = bpy.data.materials.get(n)
    if m is None:
        print("  MISSING", n)
    return m

def princ(m, color=None, metallic=None, roughness=None):
    if m is None:
        return
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None:
        return
    if color is not None:
        b.inputs["Base Color"].default_value = (*color[:3], 1.0)
    if metallic is not None and "Metallic" in b.inputs:
        b.inputs["Metallic"].default_value = metallic
    if roughness is not None and "Roughness" in b.inputs:
        b.inputs["Roughness"].default_value = roughness

def emis(m, color=None, strength=None):
    if m is None:
        return
    n = m.node_tree.nodes.get("Emission")
    if n is None:
        return
    if color is not None:
        n.inputs["Color"].default_value = (*color[:3], 1.0)
    if strength is not None:
        n.inputs["Strength"].default_value = strength

def link_to(o, coll="Assets"):
    c = bpy.data.collections.get(coll)
    if c is None:
        c = bpy.data.collections.new(coll)
        bpy.context.scene.collection.children.link(c)
    try:
        c.objects.link(o)
    except RuntimeError:
        pass
    try:
        bpy.context.scene.collection.objects.unlink(o)
    except Exception:
        pass
    return o

# ---- render: punchy Standard look, bright flat midday ----
s = bpy.context.scene
try:
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    s.view_settings.exposure = 0.3
except Exception as e:
    print("  view:", e)
sun = bpy.data.objects.get("Key_Sun")
if sun:
    sun.rotation_euler = (math.radians(25), 0, math.radians(35))  # high noon
    try:
        sun.data.energy = 4.5
        sun.data.color = (1.0, 0.99, 0.96)
    except Exception:
        pass
if s.world and s.world.use_nodes:
    for n in s.world.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs["Strength"].default_value = 1.0
            n.inputs["Color"].default_value = (0.55, 0.75, 1.0, 1.0)
print("== light: high-noon flat bright ==")

# ---- flat saturated materials ----
princ(mat("PVGlass"), color=(0.10, 0.35, 0.85), metallic=0.0, roughness=0.4)
princ(mat("Busbar"), color=(0.92, 0.93, 0.95), metallic=0.6, roughness=0.35)
princ(mat("AnodizedAlu"), color=(0.80, 0.82, 0.85), metallic=0.8, roughness=0.4)
princ(mat("Concrete"), color=(0.85, 0.76, 0.60), roughness=1.0)   # warm sandy pavement
princ(mat("TileLine"), color=(0.62, 0.54, 0.42), roughness=1.0)
princ(mat("Bldg"), color=(0.95, 0.90, 0.80), roughness=0.9)
princ(mat("Rooftop"), color=(0.55, 0.62, 0.70), roughness=0.9)
princ(mat("Wood"), color=(0.50, 0.35, 0.20), roughness=0.9)
teal = mat("TealMetal")
princ(teal, color=(0.15, 0.60, 0.75), metallic=0.3, roughness=0.5)
emis(mat("WinLit"), color=(1.0, 0.62, 0.18), strength=8.0)
emis(mat("WinC"), color=(1.0, 0.62, 0.18), strength=6.0)
emis(mat("WireDC_Red"), strength=7.0)
emis(mat("WireAC_Orange"), strength=7.0)
emis(mat("WireAC_Orange_C"), strength=7.0)
emis(mat("WireDATA_Green"), strength=6.0)
print("== materials flattened/saturated ==")

# ---- denser cell grid: horizontal fingers on every cell ----
holder = bpy.data.objects.get("PV_PanelHolder")
busbar = mat("Busbar")
added = 0
if holder and busbar:
    for cx in range(4):
        for cy in range(3):
            x = -1.2 + cx * 0.8
            y = -0.75 + cy * 0.75
            for fy in (-0.16, 0.0, 0.16):
                try:
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
                    o = bpy.context.active_object
                    o.name = f"PV_GridH_{cx}_{cy}_{fy}"
                    o.dimensions = (0.7, 0.015, 0.005)
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    o.data.materials.append(busbar)
                    o.parent = holder
                    o.location = (x, y + fy, 0.058)
                    link_to(o)
                    added += 1
                except Exception as e:
                    print("  grid fail:", e)
print(f"  grid lines added: {added}")

# ---- transformer detail: black insulator stacks + fins ----
try:
    for i, dx in enumerate((-0.2, 0.0, 0.2)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.55, location=(11.5 + dx, 8.0, 4.85))
        ins = bpy.context.active_object
        ins.name = f"Transformer_Stack_{i}"
        link_to(ins)
    for i in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(11.5, 8.35 - i * 0.3, 4.2))
        f = bpy.context.active_object
        f.name = f"Transformer_FinExtra_{i}"
        f.dimensions = (0.9, 0.06, 0.8)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        try:
            f.data.materials.append(teal)
        except Exception:
            pass
        link_to(f)
    print("  transformer stacks+fins added")
except Exception as e:
    print("  transformer detail fail:", e)

# ---- background pylon silhouette (simple steel tower) ----
steel = mat("AnodizedAlu")
try:
    px, py = 14.5, 13.0
    legs = []
    for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(px + dx, py + dy, 4.0))
        l = bpy.context.active_object
        l.name = f"Pylon_Leg_{dx}_{dy}"
        l.dimensions = (0.18, 0.18, 8.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        l.data.materials.append(steel)
        link_to(l)
        legs.append(l)
    for i, z in enumerate((6.5, 7.5, 8.5)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(px, py, z))
        a = bpy.context.active_object
        a.name = f"Pylon_Arm_{i}"
        a.dimensions = (3.2 - i * 0.5, 0.15, 0.15)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        a.data.materials.append(steel)
        link_to(a)
    print("  pylon added")
except Exception as e:
    print("  pylon fail:", e)

# ---- orange cable bundle: transformer -> meter ----
def cable(name, p0, p1, sag, radius, material):
    cd = bpy.data.curves.new(name + "_data", type='CURVE')
    cd.dimensions = '3D'
    cd.bevel_depth = radius
    cd.bevel_resolution = 2
    sp = cd.splines.new('BEZIER')
    sp.bezier_points.add(2)
    mx = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, min(p0[2], p1[2]) - sag)
    for bp, p in zip(sp.bezier_points, [p0, mx, p1]):
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(o)
    link_to(o)
    o.data.materials.append(material)
    return o

ac = mat("WireAC_Orange")
try:
    for i in range(3):
        off = (i - 1) * 0.15
        cable(f"TX_Drop_{i}", (11.5 + off, 8.0, 4.4), (6.6, 5.0 + off, 2.2), 0.7, 0.022, ac)
    print("  transformer orange drops added")
except Exception as e:
    print("  drops fail:", e)

bpy.context.view_layer.update()
print("Objects now:", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(
    os.path.dirname(os.path.abspath(bpy.data.filepath)), "volt_vision.blend"))
print("Saved toon style")
