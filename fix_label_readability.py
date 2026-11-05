"""Keep value readouts white on a tight dark plate.

Legend, building tags, the scenario banner, and pointer labels keep
their original colors and have no plate.
"""
import os
import bpy
from mathutils import Vector

BLEND_PATH = os.path.abspath("solar_management.blend")

LABEL_PREFIXES = (
    "HUD_Line_",
    "Banner_Case_",
    "Legend_Item_",
    "Tag_",
    "Pointer_Intro_Text_",
)

CASES = ("HIGH_SOLAR", "LOW_SOLAR", "BALANCED", "GRID_OUTAGE", "NORMAL")
ROW_STEP = 0.050
HUD_TITLE_SIZE = 0.036
HUD_VALUE_SIZE = 0.032
HUD_ORIGIN = (-0.98, 0.22, -1.80)
BANNER_SIZE = 0.048
BANNER_GAP = 0.064
LEGEND_X = 0.28
LEGEND_Y0 = -0.22
LEGEND_STEP = 0.062
LEGEND_SIZE = 0.034
LENS_MM = 30.0
# Absolute wide-shot placement so the panels, pole, and transformer stay in frame.
WIDE_LOC = (0.2, -35.0, 22.5)

# Above each roof, centered, tilted to the main camera so the plate stays off the building.
TAG_LOCS = {
    "Tag_Building_A": (-5.00, 8.02, 3.15),
    "Tag_Building_B": (0.00, 8.98, 6.05),
    "Tag_Building_C": (5.20, 8.32, 3.15),
    "Tag_Grid": (10.40, -0.40, 6.40),
}
TAG_ROT_X = 1.05
TAG_SIZE = 0.40
TAG_TEXT = {
    "Tag_Building_A": "BLOCK A",
    "Tag_Building_B": "BLOCK B",
    "Tag_Building_C": "BLOCK C",
}


def emission(name, color, strength):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (*color, 1.0)
    return mat


def load_font():
    path = "/System/Library/Fonts/Supplemental/Courier New.ttf"
    for f in bpy.data.fonts:
        if f.filepath == path:
            return f
    return bpy.data.fonts.load(path)


def is_label(ob):
    return ob.type == "FONT" and ob.name.startswith(LABEL_PREFIXES)


def clear_old_plates():
    for ob in list(bpy.data.objects):
        if ob.name.startswith("LblBG_"):
            bpy.data.objects.remove(ob, do_unlink=True)


def assign_slot(ob, mat, font=None):
    if font is not None:
        ob.data.font = font
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.data.extrude = 0.0
    ob.data.resolution_u = 8


def measure(ob):
    bb = [Vector(c) for c in ob.bound_box]
    xs = [v.x for v in bb]
    ys = [v.y for v in bb]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    if (maxx - minx) > 1e-5 and (maxy - miny) > 1e-5:
        return minx, maxx, miny, maxy

    size = ob.data.size
    width = max(len(ob.data.body), 1) * size * 0.60
    height = size * 1.15
    ax = ob.data.align_x
    ay = ob.data.align_y
    if ax == "CENTER":
        minx, maxx = -width / 2, width / 2
    elif ax == "RIGHT":
        minx, maxx = -width, 0.0
    else:
        minx, maxx = 0.0, width
    if ay == "CENTER":
        miny, maxy = -height / 2, height / 2
    elif ay == "TOP":
        miny, maxy = -height, 0.0
    else:
        miny, maxy = 0.0, height
    return minx, maxx, miny, maxy


def add_plate(ob, mat):
    minx, maxx, miny, maxy = measure(ob)
    pad_x = ob.data.size * 0.42
    pad_y = ob.data.size * 0.38
    z = -max(0.004, ob.data.size * 0.06)
    verts = [
        (minx - pad_x, miny - pad_y, z),
        (maxx + pad_x, miny - pad_y, z),
        (maxx + pad_x, maxy + pad_y, z),
        (minx - pad_x, maxy + pad_y, z),
    ]
    faces = [(0, 1, 2, 3)]
    me = bpy.data.meshes.new(f"LblBG_{ob.name}")
    me.from_pydata(verts, [], faces)
    me.update()
    plate = bpy.data.objects.new(f"LblBG_{ob.name}", me)
    plate.data.materials.append(mat)
    for coll in ob.users_collection:
        coll.objects.link(plate)
    if not plate.users_collection:
        bpy.context.scene.collection.objects.link(plate)
    plate.parent = ob
    plate.matrix_parent_inverse.identity()
    plate.location = (0.0, 0.0, 0.0)
    plate.rotation_euler = (0.0, 0.0, 0.0)
    plate.scale = (1.0, 1.0, 1.0)
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(plate, attr):
            setattr(plate, attr, False)
    return plate


def place_blocks():
    for case in CASES:
        block = bpy.data.objects.get(f"HUD_Block_{case}")
        if block:
            block.location = HUD_ORIGIN
        for i in range(8):
            line = bpy.data.objects.get(f"HUD_Line_{case}_{i}")
            if not line:
                continue
            line.location = (0.0, -i * ROW_STEP, 0.012)
            line.data.align_x = "LEFT"
            line.data.align_y = "TOP"
            line.data.size = HUD_TITLE_SIZE if i == 0 else HUD_VALUE_SIZE
            if i == 1 and set(line.data.body) <= set("─—-_ "):
                line.data.body = "-" * 36

    banner_loc = (HUD_ORIGIN[0], HUD_ORIGIN[1] + BANNER_GAP, HUD_ORIGIN[2])
    for i in range(1, 6):
        banner = bpy.data.objects.get(f"Banner_Case_{i}")
        if not banner:
            continue
        banner.location = banner_loc
        banner.data.size = BANNER_SIZE
        banner.data.align_x = "LEFT"
        banner.data.align_y = "TOP"

    for i in range(1, 8):
        item = bpy.data.objects.get(f"Legend_Item_{i}")
        if not item:
            continue
        item.location = (LEGEND_X, LEGEND_Y0 - (i - 1) * LEGEND_STEP, -1.80)
        item.data.size = LEGEND_SIZE
        item.data.align_x = "LEFT"
        item.data.align_y = "CENTER"

    for name, loc in TAG_LOCS.items():
        tag = bpy.data.objects.get(name)
        if not tag:
            continue
        tag.location = loc
        tag.rotation_euler = (TAG_ROT_X, 0.0, 0.0)
        tag.data.size = TAG_SIZE
        if name in TAG_TEXT:
            tag.data.body = TAG_TEXT[name]
        tag.data.align_x = "CENTER"
        tag.data.align_y = "CENTER"


# Original colors for everything that is not a value readout.
# (object name, material name, rgb, emission strength)
COLORED_LABELS = (
    ("Banner_Case_1", "Mat_Banner_Case_1", (0.20, 0.85, 1.00), 3.0),
    ("Banner_Case_2", "Mat_Banner_Case_2", (1.00, 0.55, 0.10), 3.0),
    ("Banner_Case_3", "Mat_Banner_Case_3", (0.20, 1.00, 0.45), 3.0),
    ("Banner_Case_4", "Mat_Banner_Case_4", (1.00, 0.15, 0.10), 3.0),
    ("Legend_Item_1", "Mat_Legend_1", (1.00, 0.20, 0.10), 3.0),
    ("Legend_Item_2", "Mat_Legend_2", (1.00, 0.50, 0.05), 3.0),
    ("Legend_Item_3", "Mat_Legend_3", (0.10, 1.00, 0.30), 3.0),
    ("Legend_Item_4", "Mat_Legend_4", (0.75, 0.80, 0.88), 3.0),
    ("Tag_Building_A", "Mat_Tag_Building_A", (0.20, 1.00, 0.40), 3.0),
    ("Tag_Building_B", "Mat_Tag_Building_B", (1.00, 0.60, 0.10), 3.0),
    ("Tag_Building_C", "Mat_Tag_Building_C", (1.00, 0.40, 0.20), 3.0),
    ("Tag_Grid", "Mat_Tag_Grid", (0.70, 0.80, 0.90), 3.0),
)


def add_value_panel(block, lines, banner, mat):
    xs = []
    ys = []
    for line in lines:
        minx, maxx, miny, maxy = measure(line)
        xs.extend((line.location.x + minx, line.location.x + maxx))
        ys.extend((line.location.y + miny, line.location.y + maxy))
    if banner is not None:
        minx, maxx, miny, maxy = measure(banner)
        rel = Vector(banner.location) - Vector(block.location)
        xs.extend((rel.x + minx, rel.x + maxx))
        ys.extend((rel.y + miny, rel.y + maxy))
    pad = 0.03
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad
    z = -0.008
    verts = [
        (minx, miny, z),
        (maxx, miny, z),
        (maxx, maxy, z),
        (minx, maxy, z),
    ]
    me = bpy.data.meshes.new(f"LblBG_{block.name}")
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.update()
    plate = bpy.data.objects.new(f"LblBG_{block.name}", me)
    plate.data.materials.append(mat)
    for coll in block.users_collection:
        coll.objects.link(plate)
    if not plate.users_collection:
        bpy.context.scene.collection.objects.link(plate)
    plate.parent = block
    plate.matrix_parent_inverse.identity()
    plate.location = (0.0, 0.0, 0.0)
    plate.rotation_euler = (0.0, 0.0, 0.0)
    plate.scale = (1.0, 1.0, 1.0)
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(plate, attr):
            setattr(plate, attr, False)
    return plate


def zoom_camera():
    cam = bpy.data.objects.get("Main_Camera")
    if cam is None:
        return
    cam.data.lens = LENS_MM
    if hasattr(cam.data, "dof"):
        cam.data.dof.use_dof = False
    wide_frames = {2250, 3150, 4050, 4650, 5850, 6300}
    act = cam.animation_data.action if cam.animation_data else None
    data_act = cam.data.animation_data.action if cam.data.animation_data else None
    if data_act:
        for bag in data_act.layers[0].strips[0].channelbags:
            for fc in bag.fcurves:
                if fc.data_path == "lens":
                    for key in fc.keyframe_points:
                        key.co[1] = LENS_MM
                        key.handle_left[1] = LENS_MM
                        key.handle_right[1] = LENS_MM
                elif fc.data_path == "dof.aperture_fstop":
                    for key in fc.keyframe_points:
                        key.co[1] = 16.0
                        key.handle_left[1] = 16.0
                        key.handle_right[1] = 16.0
    if not act:
        return
    curves = {}
    for bag in act.layers[0].strips[0].channelbags:
        for fc in bag.fcurves:
            if fc.data_path == "location":
                curves[fc.array_index] = fc
    if len(curves) < 3:
        return
    for axis, value in enumerate(WIDE_LOC):
        for sample in curves[axis].keyframe_points:
            if int(sample.co[0]) in wide_frames:
                sample.co[1] = value
                sample.handle_left[1] = value
                sample.handle_right[1] = value


def main():
    mat_text = emission("UI_Label_Text", (1.0, 1.0, 1.0), 1.6)
    mat_bg = emission("UI_Label_BG", (0.05, 0.07, 0.10), 1.0)
    font = load_font()
    clear_old_plates()
    place_blocks()
    zoom_camera()

    plated = 0
    for ob in bpy.data.objects:
        if ob.type == "FONT" and ob.name.startswith("HUD_Line_"):
            assign_slot(ob, mat_text, font)
            plated += 1

    restored = 0
    pointer_white = emission("Mat_Pointer_White", (0.95, 0.98, 1.0), 4.0)
    for name, mat_name, color, strength in COLORED_LABELS:
        ob = bpy.data.objects.get(name)
        if not ob or ob.type != "FONT":
            continue
        assign_slot(ob, emission(mat_name, color, strength))
        restored += 1
    for ob in bpy.data.objects:
        if ob.type == "FONT" and ob.name.startswith("Pointer_Intro_Text_"):
            assign_slot(ob, pointer_white)

    bpy.context.view_layer.update()
    for case in CASES:
        block = bpy.data.objects.get(f"HUD_Block_{case}")
        if block is None:
            continue
        lines = []
        for i in range(8):
            line = bpy.data.objects.get(f"HUD_Line_{case}_{i}")
            if line:
                lines.append(line)
        banner = None
        if case == "HIGH_SOLAR":
            banner = bpy.data.objects.get("Banner_Case_1")
        elif case == "LOW_SOLAR":
            banner = bpy.data.objects.get("Banner_Case_2")
        elif case == "BALANCED":
            banner = bpy.data.objects.get("Banner_Case_3")
        elif case == "GRID_OUTAGE":
            banner = bpy.data.objects.get("Banner_Case_4")
        if lines:
            add_value_panel(block, lines, banner, mat_bg)
    for ob in bpy.data.objects:
        if ob.type == "FONT" and ob.name.startswith(("Legend_Item_", "Tag_")):
            add_plate(ob, mat_bg)

    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print(f"Plates on {plated} value lines, restored {restored} colored labels -> {BLEND_PATH}")


if __name__ == "__main__":
    main()
