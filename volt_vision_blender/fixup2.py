"""Fixup-2: relay cutaway visibility, label placement, focus, bigger legend.
Run: blender --background volt_vision_blender/volt_vision.blend --python volt_vision_blender/fixup2.py
"""
import bpy, math, os

def link_to(obj, coll_name="Assets"):
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

# 1. Relay cabinet -> low open tub so busbars/coils show above rim
cab = bpy.data.objects.get("RelayUnit_Cabinet")
if cab:
    cab.dimensions = (1.4, 0.9, 0.55)
    cab.location = (-3.4, -1.2, 1.10)
    print("  relay tub:", tuple(round(v, 2) for v in cab.location))
# busbars/coils nudge up to sit visibly in tub
for n, z in (("Relay_Busbar_0", 1.42), ("Relay_Busbar_1", 1.42), ("Relay_Busbar_2", 1.42),
             ("Relay_Coil_0", 1.30), ("Relay_Coil_1", 1.30)):
    o = bpy.data.objects.get(n)
    if o:
        o.location.z = z

# 2. Relay label -> front face, outside the box
lbl = bpy.data.objects.get("Label_12V")
if lbl:
    lbl.location = (-4.05, -1.67, 1.15)
    try:
        lbl.data.size = 0.15
    except Exception:
        pass
    print("  relay label moved to front face")

# 3. Battery focus -> midpoint relay+battery so both in frame
fb = bpy.data.objects.get("Focus_Batt")
if fb:
    fb.location = (-2.45, -1.30, 1.30)

# 4. Rebuild legend bigger + facing final camera
for o in list(bpy.data.objects):
    if o.name.startswith(("Legend_Board", "Legend_SW_", "Legend_TX_")):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
lx, ly, lz = 8.0, -2.2, 0.75
try:
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
except Exception:
    pass
bpy.ops.mesh.primitive_cube_add(size=1, location=(lx, ly, lz))
board = bpy.context.active_object
board.name = "Legend_Board"
board.dimensions = (3.0, 0.10, 1.6)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
board.rotation_euler = (math.radians(55), 0, math.radians(-12))
link_to(board)
try:
    board.data.materials.append(bpy.data.materials.get("ABS_White"))
except Exception:
    pass
items = [("RED - DC power", "WireDC_Red"), ("ORANGE - AC power", "WireAC_Orange"),
         ("GREEN - sensor/data", "WireDATA_Green"), ("GREY DASH - grid tie", "WireGRID_Dashed")]
for i, (label, mname) in enumerate(items):
    y = lz + 0.50 - i * 0.33
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lx - 1.0, ly - 0.08, y))
    sw = bpy.context.active_object
    sw.name = f"Legend_SW_{i}"
    sw.dimensions = (0.55, 0.03, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    try:
        sw.data.materials.append(bpy.data.materials.get(mname))
    except Exception:
        pass
    link_to(sw)
    bpy.ops.object.text_add(location=(lx - 0.6, ly - 0.08, y - 0.09))
    tx = bpy.context.active_object
    tx.name = f"Legend_TX_{i}"
    tx.data.body = label
    tx.data.size = 0.17
    tx.data.align_x = 'LEFT'
    link_to(tx)
print("  legend rebuilt bigger")

bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(
    os.path.dirname(os.path.abspath(bpy.data.filepath)), "volt_vision.blend"))
print("Saved fixup-2")
