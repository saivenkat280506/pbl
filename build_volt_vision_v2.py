"""Volt Vision 3D Campus Simulation Upgrade — Master Builder Script (v2).

Implements Steps 0 through 6 for Volt Vision 3D microgrid simulation in Blender 5.2:
- Replaces disconnected buildings with unified HITAM academic complex
- Adds realistic landscaping, roads, promenade, hedges, and instanced lush trees
- Integrates solar array onto central north rooftop and utility equipment at ground level
- Routes DC, AC, Sensor, and Grid lines along realistic conduits and paved paths
- Eliminates functional building labels
- Builds solid dark-navy rounded-card callout system, HUD, and color-key legend
- Configures 4 microgrid operational scenarios
- Establishes CAM_TOP_DOWN and CAM_ANGLED_VIEW presentation cameras
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")

def get_scene():
    return bpy.context.scene

# ---------------------------------------------------------------------------
# Collections Setup
# ---------------------------------------------------------------------------
def get_or_create_col(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or SCENE.collection).children.link(c)
    return c

COL_CAMPUS = get_or_create_col("CAMPUS_ARCHITECTURE")
COL_LANDSCAPE = get_or_create_col("CAMPUS_LANDSCAPE")
COL_EQUIPMENT = get_or_create_col("CAMPUS_EQUIPMENT")
COL_CIRCUITS = get_or_create_col("CAMPUS_CIRCUITS")
COL_UI = get_or_create_col("CAMPUS_UI_SYSTEM")

def link_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob

# ---------------------------------------------------------------------------
# Material Library
# ---------------------------------------------------------------------------
def get_mat(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, emit=None, emit_str=1.0, alpha=1.0):
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

# Architectural & Environment Materials
MAT_WALL = get_mat("HITAM_Plaster", (0.80, 0.64, 0.44), rough=0.68)       # Warm beige sandstone
MAT_WALL_DARK = get_mat("HITAM_PlasterDark", (0.55, 0.38, 0.22), rough=0.72)
MAT_PARAPET = get_mat("HITAM_Terracotta", (0.52, 0.16, 0.08), rough=0.65)   # Terracotta trim
MAT_ROOF = get_mat("HITAM_RoofDeck", (0.42, 0.40, 0.38), rough=0.82)
MAT_PLINTH = get_mat("HITAM_Plinth", (0.36, 0.32, 0.26), rough=0.75)
MAT_GLASS = get_mat("HITAM_WindowGlass", (0.05, 0.09, 0.14), rough=0.08, emit=(0.85, 0.65, 0.35), emit_str=0.6)
MAT_FRAME = get_mat("HITAM_WinFrame", (0.12, 0.10, 0.08), rough=0.45, metal=0.2)
MAT_ATRIUM = get_mat("HITAM_AtriumGlass", (0.1, 0.25, 0.4), rough=0.05, alpha=0.65)

MAT_GRASS = get_mat("Campus_Lawn", (0.08, 0.22, 0.05), rough=0.88)
MAT_ROAD = get_mat("Campus_Asphalt", (0.04, 0.042, 0.045), rough=0.75)
MAT_PAVER = get_mat("Campus_Pavers", (0.58, 0.55, 0.50), rough=0.70)
MAT_CURB = get_mat("Campus_Curb", (0.75, 0.74, 0.70), rough=0.60)
MAT_MARK = get_mat("Campus_RoadMark", (0.92, 0.92, 0.88), rough=0.40, emit=(0.92, 0.92, 0.88), emit_str=0.2)
MAT_HEDGE = get_mat("Campus_Hedge", (0.04, 0.15, 0.03), rough=0.85)

# Tree Materials
MAT_TRUNK = get_mat("Campus_Trunk", (0.14, 0.08, 0.04), rough=0.92)
MAT_CANOPY_1 = get_mat("Canopy_Emerald", (0.05, 0.18, 0.04), rough=0.85)
MAT_CANOPY_2 = get_mat("Canopy_Forest", (0.03, 0.12, 0.025), rough=0.88)
MAT_CANOPY_3 = get_mat("Canopy_Lime", (0.10, 0.26, 0.06), rough=0.82)

# Circuit Wire Materials
MAT_WIRE_DC = get_mat("Mat_Wire_DC", (0.95, 0.12, 0.05), rough=0.3, emit=(1.0, 0.15, 0.05), emit_str=2.5)
MAT_WIRE_AC = get_mat("Mat_Wire_AC", (1.0, 0.45, 0.02), rough=0.3, emit=(1.0, 0.48, 0.05), emit_str=2.4)
MAT_WIRE_DATA = get_mat("Mat_Wire_Data", (0.08, 0.88, 0.22), rough=0.3, emit=(0.1, 0.92, 0.25), emit_str=2.2)
MAT_WIRE_GRID = get_mat("Mat_Wire_Grid", (0.75, 0.82, 0.90), rough=0.3, emit=(0.75, 0.85, 0.95), emit_str=1.2)

# UI Card Materials
MAT_CARD_BG = get_mat("UI_Card_Navy", (0.05, 0.09, 0.16), rough=0.25, alpha=0.94)
MAT_CARD_BORDER = get_mat("UI_Card_Border", (0.28, 0.58, 0.88), rough=0.2, emit=(0.28, 0.58, 0.88), emit_str=1.2)
MAT_CARD_TEXT = get_mat("UI_Card_Text", (0.96, 0.97, 0.99), rough=0.2, emit=(0.96, 0.97, 0.99), emit_str=0.9)
MAT_CARD_POINTER = get_mat("UI_Pointer_Line", (0.45, 0.72, 0.95), rough=0.3, emit=(0.45, 0.72, 0.95), emit_str=1.5)

# Accent Swatches for Legend
MAT_ACCENT_DC = get_mat("UI_Accent_DC", (0.98, 0.15, 0.08), emit=(0.98, 0.15, 0.08), emit_str=2.0)
MAT_ACCENT_AC = get_mat("UI_Accent_AC", (1.0, 0.52, 0.05), emit=(1.0, 0.52, 0.05), emit_str=2.0)
MAT_ACCENT_DATA = get_mat("UI_Accent_Data", (0.1, 0.92, 0.25), emit=(0.1, 0.92, 0.25), emit_str=2.0)
MAT_ACCENT_GRID = get_mat("UI_Accent_Grid", (0.85, 0.88, 0.95), emit=(0.85, 0.88, 0.95), emit_str=1.5)

# ---------------------------------------------------------------------------
# Mesh Helpers
# ---------------------------------------------------------------------------
def make_box(name, loc, size, mat, col=COL_CAMPUS, bevel=0.0):
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

def make_cyl(name, loc, radius, depth, mat, col=COL_CAMPUS, verts=16, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius, radius2=radius, depth=depth)
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
# Step 3: Remove Old Floating Building Labels & Clutter
# ---------------------------------------------------------------------------
def cleanup_old_elements():
    print("Executing cleanup of old building labels and outdated geometry...")
    to_delete = []
    for ob in bpy.data.objects:
        n = ob.name
        if n in ["Tag_Building_A", "Tag_Building_B", "Tag_Building_C", "Tag_Grid"]:
            to_delete.append(ob)
        elif n.startswith("Pointer_Intro_Text_Buildings_"):
            to_delete.append(ob)
        elif n.startswith("Pointer_Intro_Text_Grid"):
            to_delete.append(ob)
        elif n.startswith("HUD_Line_") or n.startswith("HUD_Block_"):
            to_delete.append(ob)
        elif n.startswith("Banner_Case_"):
            to_delete.append(ob)
        elif n.startswith("Legend_Item_") or n == "Legend_Board":
            to_delete.append(ob)
        elif n.startswith("Inst_") or n.startswith("InstWin_") or n.startswith("InstGlass_") or n.startswith("InstFrame_"):
            to_delete.append(ob)
        elif n.startswith("Wing_") or n.startswith("RoofPV_") or n.startswith("RoofDeck_"):
            to_delete.append(ob)
    
    # Hide the old separate Building A/B/C box meshes
    for tag in ("A", "B", "C"):
        p = bpy.data.objects.get(f"Building_{tag}")
        if p:
            for child in bpy.data.objects:
                if child.parent == p:
                    child.hide_viewport = True
                    child.hide_render = True
            p.hide_viewport = True
            p.hide_render = True

    for ob in to_delete:
        bpy.data.objects.remove(ob, do_unlink=True)
    print("Cleanup complete.")

# ---------------------------------------------------------------------------
# Step 1: Rebuild HITAM Academic Complex Footprint
# ---------------------------------------------------------------------------
def build_hitam_academic_complex():
    print("Building HITAM Academic Complex (H/U-shape, portico, roofline, windows)...")
    
    # 1. Base Plinth / Foundation
    make_box("HITAM_Podium", (0.0, 8.5, 0.15), (28.0, 16.0, 0.30), MAT_PLINTH, COL_CAMPUS, bevel=0.04)

    # 2. North Central Wing (Main 2-story bar with rooftop solar mounting)
    make_box("HITAM_NorthWing", (0.0, 13.0, 2.85), (17.0, 4.0, 5.4), MAT_WALL, COL_CAMPUS, bevel=0.06)
    make_box("HITAM_NorthWing_Roof", (0.0, 13.0, 5.62), (16.8, 3.8, 0.15), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_NorthWing_ParapetN", (0.0, 14.95, 5.75), (17.0, 0.15, 0.25), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_NorthWing_ParapetS", (0.0, 11.05, 5.75), (17.0, 0.15, 0.25), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_NorthWing_ParapetW", (-8.45, 13.0, 5.75), (0.15, 3.8, 0.25), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_NorthWing_ParapetE", (8.45, 13.0, 5.75), (0.15, 3.8, 0.25), MAT_PARAPET, COL_CAMPUS)

    # 3. South Central Entrance Pavilion (Colonnaded Portico & Grand Entry)
    make_box("HITAM_Portico_Base", (0.0, 5.5, 1.8), (6.8, 3.2, 3.6), MAT_WALL, COL_CAMPUS, bevel=0.05)
    make_box("HITAM_Portico_Roof", (0.0, 5.2, 3.7), (7.4, 3.8, 0.18), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_Portico_Parapet", (0.0, 5.2, 3.84), (7.5, 3.9, 0.12), MAT_PARAPET, COL_CAMPUS)
    
    # Grand Entry Stairs & Canopy
    make_box("HITAM_Entry_Plaza", (0.0, 3.0, 0.18), (8.5, 2.4, 0.18), MAT_PAVER, COL_CAMPUS)
    make_box("HITAM_Entry_Stairs1", (0.0, 2.4, 0.10), (7.0, 0.8, 0.12), MAT_PLINTH, COL_CAMPUS)
    make_box("HITAM_Entry_Stairs2", (0.0, 2.8, 0.16), (6.6, 0.8, 0.12), MAT_PLINTH, COL_CAMPUS)
    
    # Portico Colonnade Columns
    for col_x in (-2.6, -0.9, 0.9, 2.6):
        make_cyl(f"HITAM_Portico_Col_{int(col_x*10)}", (col_x, 4.0, 1.8), 0.18, 3.6, MAT_WALL, COL_CAMPUS, 12)
    
    # Roof Atrium Glass Pyramid
    make_box("HITAM_Atrium_Base", (0.0, 5.5, 3.85), (2.4, 2.4, 0.15), MAT_FRAME, COL_CAMPUS)
    make_box("HITAM_Atrium_Glass", (0.0, 5.5, 4.2), (2.0, 2.0, 0.5), MAT_ATRIUM, COL_CAMPUS, bevel=0.2)

    # 4. Central Spine Connecting Portico to North Wing
    make_box("HITAM_CenterSpine", (0.0, 9.2, 2.3), (4.5, 4.6, 4.3), MAT_WALL, COL_CAMPUS, bevel=0.05)
    make_box("HITAM_CenterSpine_Roof", (0.0, 9.2, 4.52), (4.3, 4.4, 0.14), MAT_ROOF, COL_CAMPUS)

    # 5. West Wing (Wing 1 — Lab / Critical Loads)
    make_box("HITAM_WestWing_Main", (-10.5, 8.5, 2.4), (4.4, 10.5, 4.6), MAT_WALL, COL_CAMPUS, bevel=0.06)
    make_box("HITAM_WestWing_Roof", (-10.5, 8.5, 4.78), (4.2, 10.3, 0.14), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_WestWing_ParaS", (-10.5, 3.3, 4.92), (4.4, 0.15, 0.22), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_WestWing_ParaN", (-10.5, 13.7, 4.92), (4.4, 0.15, 0.22), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_WestWing_ParaW", (-12.65, 8.5, 4.92), (0.15, 10.4, 0.22), MAT_PARAPET, COL_CAMPUS)

    # West Front Projection (South Wing)
    make_box("HITAM_WestFront", (-6.2, 5.5, 2.1), (4.2, 3.4, 4.0), MAT_WALL, COL_CAMPUS, bevel=0.05)
    make_box("HITAM_WestFront_Roof", (-6.2, 5.5, 4.18), (4.0, 3.2, 0.14), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_WestFront_ParaS", (-6.2, 3.85, 4.32), (4.2, 0.15, 0.20), MAT_PARAPET, COL_CAMPUS)

    # West Connecting Corridor
    make_box("HITAM_WestLink", (-7.2, 11.2, 2.2), (2.8, 2.4, 4.2), MAT_WALL, COL_CAMPUS)
    make_box("HITAM_WestLink_Roof", (-7.2, 11.2, 4.38), (2.6, 2.2, 0.12), MAT_ROOF, COL_CAMPUS)

    # 6. East Wing (Wing 3 — Auditorium / Non-Critical Loads)
    make_box("HITAM_EastWing_Main", (10.5, 8.5, 2.4), (4.4, 10.5, 4.6), MAT_WALL, COL_CAMPUS, bevel=0.06)
    make_box("HITAM_EastWing_Roof", (10.5, 8.5, 4.78), (4.2, 10.3, 0.14), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_EastWing_ParaS", (10.5, 3.3, 4.92), (4.4, 0.15, 0.22), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_EastWing_ParaN", (10.5, 13.7, 4.92), (4.4, 0.15, 0.22), MAT_PARAPET, COL_CAMPUS)
    make_box("HITAM_EastWing_ParaE", (12.65, 8.5, 4.92), (0.15, 10.4, 0.22), MAT_PARAPET, COL_CAMPUS)

    # East Front Projection (South Wing)
    make_box("HITAM_EastFront", (6.2, 5.5, 2.1), (4.2, 3.4, 4.0), MAT_WALL, COL_CAMPUS, bevel=0.05)
    make_box("HITAM_EastFront_Roof", (6.2, 5.5, 4.18), (4.0, 3.2, 0.14), MAT_ROOF, COL_CAMPUS)
    make_box("HITAM_EastFront_ParaS", (6.2, 3.85, 4.32), (4.2, 0.15, 0.20), MAT_PARAPET, COL_CAMPUS)

    # East Connecting Corridor
    make_box("HITAM_EastLink", (7.2, 11.2, 2.2), (2.8, 2.4, 4.2), MAT_WALL, COL_CAMPUS)
    make_box("HITAM_EastLink_Roof", (7.2, 11.2, 4.38), (2.6, 2.2, 0.12), MAT_ROOF, COL_CAMPUS)

    # 7. Window Bands (South & Front Facades)
    def add_windows_row(prefix, face_y, xs, zs, w=0.58, h=0.78):
        for i, x in enumerate(xs):
            for j, z in enumerate(zs):
                make_box(f"{prefix}_WinRecess_{i}_{j}", (x, face_y, z), (w, 0.08, h), MAT_WALL_DARK, COL_CAMPUS)
                make_box(f"{prefix}_WinGlass_{i}_{j}", (x, face_y - 0.02, z), (w * 0.85, 0.03, h * 0.85), MAT_GLASS, COL_CAMPUS)
    
    # West Wing Front Windows
    add_windows_row("Win_WF", 3.75, [-7.6, -6.6, -5.6, -4.6], [1.2, 2.4])
    # East Wing Front Windows
    add_windows_row("Win_EF", 3.75, [4.6, 5.6, 6.6, 7.6], [1.2, 2.4])
    # West Wing South Face
    add_windows_row("Win_W_South", 3.20, [-11.8, -10.5, -9.2], [1.3, 2.7])
    # East Wing South Face
    add_windows_row("Win_E_South", 3.20, [9.2, 10.5, 11.8], [1.3, 2.7])
    # Portico Entrance Windows
    add_windows_row("Win_Portico", 3.85, [-2.2, 0.0, 2.2], [2.6], w=0.8, h=0.9)

    # 8. Rooftop Ancillary Equipment (Water Tank & Flagpole)
    make_cyl("HITAM_Roof_WaterTank", (4.5, 12.5, 6.3), 0.65, 1.2, MAT_ROOF, COL_CAMPUS, 16)
    make_cyl("HITAM_Roof_FlagPole", (0.0, 14.0, 6.8), 0.04, 2.4, MAT_CURB, COL_CAMPUS, 8)

    print("HITAM Academic Complex constructed.")

# ---------------------------------------------------------------------------
# Step 1 (cont): Landscaping, Roads, Paths, and Instanced Foliage
# ---------------------------------------------------------------------------
def build_landscaping_and_roads():
    print("Building campus landscaping, roads, promenade, and foliage...")
    
    # Main Ground Grass
    ground = bpy.data.objects.get("Ground_Plane")
    if ground:
        ground.data.materials.clear()
        ground.data.materials.append(MAT_GRASS)
        ground.location = (0, 0, 0)
        ground.scale = (45, 45, 1)

    # Front Arterial Road (defined curved road at property edge with lane markings)
    make_box("Road_SouthMain", (0.0, -17.5, 0.04), (56.0, 4.4, 0.06), MAT_ROAD, COL_LANDSCAPE, bevel=0.05)
    make_box("Road_Curb_South", (0.0, -19.75, 0.08), (56.0, 0.25, 0.12), MAT_CURB, COL_LANDSCAPE)
    make_box("Road_Curb_North", (0.0, -15.25, 0.08), (56.0, 0.25, 0.12), MAT_CURB, COL_LANDSCAPE)
    
    # Lane Markings along Road
    for i, rx in enumerate(range(-24, 25, 4)):
        make_box(f"Road_Mark_{i}", (rx, -17.5, 0.075), (1.8, 0.16, 0.01), MAT_MARK, COL_LANDSCAPE)

    # Grand Entrance Promenade (from Road to Central Portico)
    make_box("Path_MainPromenade", (0.0, -6.5, 0.05), (3.6, 17.5, 0.04), MAT_PAVER, COL_LANDSCAPE, bevel=0.03)
    
    # Secondary Paved Paths Connecting Wings & Service Areas
    make_box("Path_CrossWing", (0.0, 2.2, 0.05), (25.0, 1.4, 0.04), MAT_PAVER, COL_LANDSCAPE, bevel=0.02)
    make_box("Path_WestWingService", (-9.5, -2.5, 0.05), (1.6, 9.0, 0.04), MAT_PAVER, COL_LANDSCAPE)
    make_box("Path_EastWingAccess", (9.5, -2.5, 0.05), (1.6, 9.0, 0.04), MAT_PAVER, COL_LANDSCAPE)
    make_box("Path_Perimeter_West", (-14.0, 7.5, 0.05), (1.4, 14.0, 0.04), MAT_PAVER, COL_LANDSCAPE)
    make_box("Path_Perimeter_East", (14.0, 7.5, 0.05), (1.4, 14.0, 0.04), MAT_PAVER, COL_LANDSCAPE)

    # Inner Courtyard Lawns & Hedges
    make_box("Lawn_Courtyard_West", (-4.8, 8.8, 0.06), (4.2, 5.0, 0.02), MAT_GRASS, COL_LANDSCAPE)
    make_box("Lawn_Courtyard_East", (4.8, 8.8, 0.06), (4.2, 5.0, 0.02), MAT_GRASS, COL_LANDSCAPE)
    
    # Hedges Lining the Main Promenade
    make_box("Hedge_Promenade_W", (-2.1, -6.5, 0.35), (0.45, 17.0, 0.55), MAT_HEDGE, COL_LANDSCAPE, bevel=0.08)
    make_box("Hedge_Promenade_E", (2.1, -6.5, 0.35), (0.45, 17.0, 0.55), MAT_HEDGE, COL_LANDSCAPE, bevel=0.08)
    
    # Hedges along Building Wings
    make_box("Hedge_WestFront", (-6.2, 1.8, 0.30), (5.5, 0.40, 0.50), MAT_HEDGE, COL_LANDSCAPE, bevel=0.06)
    make_box("Hedge_EastFront", (6.2, 1.8, 0.30), (5.5, 0.40, 0.50), MAT_HEDGE, COL_LANDSCAPE, bevel=0.06)

    # -----------------------------------------------------------------------
    # Instanced Lush Trees (Performance-Optimized Prototype System)
    # -----------------------------------------------------------------------
    def build_tree_prototype(name, canopy_mat, scale_factor=1.0):
        parts = []
        tr = make_cyl(f"{name}_trunk", (0, 0, 1.0 * scale_factor), 0.18 * scale_factor, 2.0 * scale_factor, MAT_TRUNK, COL_LANDSCAPE, 8)
        parts.append(tr)
        
        # Multi-sphere lush canopy
        blobs = [
            ((0.0, 0.0, 2.6 * scale_factor), 1.25 * scale_factor),
            ((0.55 * scale_factor, 0.2 * scale_factor, 2.8 * scale_factor), 0.95 * scale_factor),
            ((-0.45 * scale_factor, 0.3 * scale_factor, 2.7 * scale_factor), 0.9 * scale_factor),
            ((0.1 * scale_factor, -0.5 * scale_factor, 2.9 * scale_factor), 0.85 * scale_factor),
            ((-0.2 * scale_factor, -0.2 * scale_factor, 3.4 * scale_factor), 0.75 * scale_factor),
        ]
        for idx, (b_loc, b_rad) in enumerate(blobs):
            me = bpy.data.meshes.new(f"{name}_c{idx}")
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=b_rad)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(f"{name}_c{idx}", me)
            ob.location = b_loc
            ob.data.materials.append(canopy_mat)
            for poly in ob.data.polygons:
                poly.use_smooth = True
            link_to(ob, COL_LANDSCAPE)
            parts.append(ob)
            
        bpy.ops.object.select_all(action="DESELECT")
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        tree = bpy.context.object
        tree.name = name
        tree.hide_render = True
        tree.hide_viewport = True
        tree.location = (100, 100, 0)
        return tree

    proto_a = build_tree_prototype("TreeProto_Emerald", MAT_CANOPY_1, 1.1)
    proto_b = build_tree_prototype("TreeProto_Forest", MAT_CANOPY_2, 1.3)
    proto_c = build_tree_prototype("TreeProto_Lime", MAT_CANOPY_3, 0.95)
    protos = [proto_a, proto_b, proto_c]

    # Clean previous tree instances
    for o in list(bpy.data.objects):
        if o.name.startswith("TreeInst_") or o.name.startswith("CampusTree_"):
            bpy.data.objects.remove(o, do_unlink=True)

    # Keepout zones around buildings, paths, and equipment
    keepouts = [
        (-14.0, 1.0, 14.0, 16.0),   # Academic building zone
        (-2.5, -16.0, 2.5, 3.0),    # Main promenade zone
        (-10.5, 0.0, -7.0, 3.0),    # Control & relay zone
        (13.5, -16.5, 17.5, -12.5), # Utility grid pole zone
    ]
    def is_in_keepout(x, y, pad=0.8):
        for x0, y0, x1, y1 in keepouts:
            if (x0 - pad <= x <= x1 + pad) and (y0 - pad <= y <= y1 + pad):
                return True
        return False

    tree_positions = []
    # 1. Trees lining the perimeter of the campus (dense background groves)
    for x in range(-28, 29, 3):
        tree_positions.append((x, 19.5, 1.25))
        tree_positions.append((x, 22.0, 1.45))
        tree_positions.append((x, -21.5, 1.35))
    
    # 2. Side flanks
    for y in range(-18, 20, 3):
        tree_positions.append((-20.0, y, 1.3))
        tree_positions.append((-23.5, y, 1.4))
        tree_positions.append((20.0, y, 1.3))
        tree_positions.append((23.5, y, 1.4))

    # 3. Intermediate lawn clusters
    lawn_points = [
        (-5.5, -4.5), (-7.5, -7.0), (-11.0, -6.5), (-13.5, -11.0),
        (5.5, -4.5), (7.5, -7.0), (11.0, -6.5), (13.5, -11.0),
        (-15.5, 4.0), (-15.5, 10.0), (15.5, 4.0), (15.5, 10.0),
        (-4.5, 8.5), (4.5, 8.5) # Courtyard accent trees
    ]
    for px, py in lawn_points:
        tree_positions.append((px, py, 1.05))

    tree_count = 0
    for idx, (tx, ty, tscale) in enumerate(tree_positions):
        if is_in_keepout(tx, ty, pad=0.4):
            continue
        proto = protos[idx % 3]
        inst = bpy.data.objects.new(f"TreeInst_{tree_count:03d}", proto.data)
        inst.location = (tx, ty, 0.0)
        inst.scale = (tscale, tscale, tscale)
        inst.rotation_euler = (0, 0, (idx * 1.37) % 6.28)
        COL_LANDSCAPE.objects.link(inst)
        tree_count += 1

    print(f"Placed {tree_count} instanced lush trees across campus.")

# ---------------------------------------------------------------------------
# Step 2: Equipment Integration & Realistic Routing Paths
# ---------------------------------------------------------------------------
def setup_equipment_and_circuits():
    print("Integrating equipment and routing 4 energy circuits along realistic conduits...")

    # 1. Move Solar Panel Array to Rooftop of North Central Wing
    # Target location on central roof: X from -6.5 to -1.5, Y from 11.5 to 13.5, Z = 5.70
    solar_panels = [o for o in bpy.data.objects if o.name.startswith("Solar_Panel_") and "Unit" in o.name]
    solar_panels.sort(key=lambda o: o.name)
    
    # 2 rows of 3 panels on rooftop
    roof_slots = [
        (-5.5, 12.0), (-3.5, 12.0), (-1.5, 12.0),
        (-5.5, 13.8), (-3.5, 13.8), (-1.5, 13.8)
    ]
    for idx, panel in enumerate(solar_panels):
        if idx < len(roof_slots):
            rx, ry = roof_slots[idx]
            panel.location = (rx, ry, 5.72)
            panel.rotation_euler = (math.radians(20), 0, 0) # Tilted 20 deg facing south
            panel.scale = (0.95, 0.95, 0.95)

    # 2. Control Unit (ESP32) & Relay Unit at Ground Level near West Wing
    ctrl = bpy.data.objects.get("Control_ESP32")
    if ctrl:
        ctrl.location = (-9.2, 1.8, 0.15)
        link_to(ctrl, COL_EQUIPMENT)
        # Utility concrete pad under units
        make_box("Pad_UtilityEquipment", (-8.4, 1.8, 0.08), (3.2, 1.8, 0.16), MAT_PLINTH, COL_EQUIPMENT)

    relay = bpy.data.objects.get("Relay_Module_1")
    if relay:
        relay.location = (-7.6, 1.8, 0.15)
        link_to(relay, COL_EQUIPMENT)

    # 3. Grid Transformer & Utility Pole at Road Edge
    pole = bpy.data.objects.get("Grid_Pole")
    if pole:
        pole.location = (15.5, -14.5, 4.5)
        link_to(pole, COL_EQUIPMENT)
    
    xformer = bpy.data.objects.get("Grid_Transformer")
    if xformer:
        xformer.location = (15.85, -14.75, 5.4)
        link_to(xformer, COL_EQUIPMENT)

    # -----------------------------------------------------------------------
    # Realistic Circuit Line Routing (Conforms to Parapets, Conduits, Walkways)
    # -----------------------------------------------------------------------
    def build_spline_curve(name, points, mat, bevel_radius=0.038):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        c_data = bpy.data.curves.new(name, "CURVE")
        c_data.dimensions = "3D"
        c_data.bevel_depth = bevel_radius
        c_data.bevel_resolution = 4
        spline = c_data.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for i, pt in enumerate(points):
            bp = spline.bezier_points[i]
            bp.co = Vector(pt)
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
        c_ob = bpy.data.objects.new(name, c_data)
        c_ob.data.materials.append(mat)
        return link_to(c_ob, COL_CIRCUITS)

    # Line 1: DC Solar Line (Red) — Rooftop -> West Parapet -> Vertical Conduit -> Walkway -> Control Unit
    pts_dc = [
        (-3.5, 12.8, 5.85),     # From Solar Array center
        (-6.5, 12.8, 5.80),     # Along North Roof
        (-8.2, 12.8, 5.80),     # Roof parapet corner
        (-8.8, 11.2, 5.00),     # West wing junction
        (-8.8, 11.2, 2.50),     # Vertical building riser down
        (-9.2, 11.2, 0.30),     # Ground foundation trench
        (-9.2, 5.5, 0.30),      # Along west service path
        (-9.2, 2.1, 0.35),      # Into Control Unit ESP32 DC In
    ]
    build_spline_curve("Wire_DC", pts_dc, MAT_WIRE_DC, 0.042)

    # Line 2: AC Distribution Line (Orange) — Relay Unit -> Building Foundation -> Wing Distribution
    pts_ac = [
        (-7.6, 2.1, 0.35),      # Relay Output
        (-7.6, 3.6, 0.28),      # Foundation entrance
        (-6.2, 4.2, 0.28),      # Wing 1 (Critical Lab load)
        (-3.0, 4.2, 0.28),      # Cross-corridor trunk
        (0.0, 5.2, 0.28),       # Wing 2 (Academic central load)
        (3.5, 4.2, 0.28),       # Cross-corridor East
        (7.0, 4.2, 0.28),       # Wing 3 (Auditorium non-critical load)
    ]
    build_spline_curve("Wire_AC", pts_ac, MAT_WIRE_AC, 0.045)

    # Line 3: Sensor / Data Feedback Line (Dashed Green) — Interconnecting ESP32, Solar & Relay
    pts_data = [
        (-3.5, 13.0, 5.88),     # Solar PV temperature / irradiance sensors
        (-7.8, 13.0, 5.82),     # Conduit run down
        (-8.6, 11.0, 0.32),     # Service riser
        (-9.0, 2.2, 0.38),      # ESP32 Sensor Bus Port
        (-8.2, 2.2, 0.38),      # Relay switching control interface
    ]
    build_spline_curve("Wire_Data", pts_data, MAT_WIRE_DATA, 0.032)

    # Line 4: Grid Utility Line (Grey / White) — Road Edge Utility Pole -> Curb Pathway -> Substation
    pts_grid = [
        (15.8, -14.5, 5.10),    # Grid Transformer output
        (15.5, -14.5, 2.50),    # Down utility pole
        (15.0, -14.0, 0.30),    # Ground junction
        (8.0, -14.0, 0.28),     # Along road boundary conduit
        (0.0, -13.5, 0.28),     # Cross-promenade conduit trench
        (-7.5, -12.0, 0.28),    # Toward west utility area
        (-7.6, 1.4, 0.32),      # Grid Input into Relay / Control Unit
    ]
    build_spline_curve("Wire_Grid", pts_grid, MAT_WIRE_GRID, 0.040)

    # Connect/Update Pulse Objects to match updated curve paths
    for key, cname in [("DC", "Wire_DC"), ("AC", "Wire_AC"), ("Data", "Wire_Data"), ("Grid", "Wire_Grid")]:
        p = bpy.data.objects.get(f"FX_Pulse_{key}")
        w = bpy.data.objects.get(cname)
        if p and w:
            p.data = w.data
            link_to(p, COL_CIRCUITS)

    print("Equipment integrated and circuits routed along realistic architectural paths.")

# ---------------------------------------------------------------------------
# Step 4: Solid Dark Navy Card Callout & Value Display System
# ---------------------------------------------------------------------------
def build_card_ui_system():
    print("Building Solid Dark Navy Card Callout & Value Display System...")

    # Helper to create a solid rounded rectangle card in 3D
    def create_ui_card(name, loc, size, rot=(0, 0, 0)):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        old_b = bpy.data.objects.get(f"{name}_Border")
        if old_b:
            bpy.data.objects.remove(old_b, do_unlink=True)
        
        # Outer Border
        b_box = make_box(f"{name}_Border", loc, (size[0] + 0.08, size[1] + 0.08, size[2]), MAT_CARD_BORDER, COL_UI, bevel=0.04)
        b_box.rotation_euler = rot
        
        # Inner Dark Navy Fill
        in_loc = (loc[0], loc[1], loc[2] + 0.015)
        c_box = make_box(name, in_loc, size, MAT_CARD_BG, COL_UI, bevel=0.03)
        c_box.rotation_euler = rot
        c_box.parent = b_box
        c_box.location = (0, 0, 0.01)
        return b_box

    # Helper to add text line on a card
    def add_card_text(name, parent_card, text, local_offset, font_size=0.32, align="LEFT", mat=MAT_CARD_TEXT):
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

    # Helper to create a thin 3D pointer line connecting card to 3D anchor
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

    # -----------------------------------------------------------------------
    # 1. Equipment Callout Cards (with Pointers)
    # -----------------------------------------------------------------------
    # Card A: Solar Panels
    card_pv = create_ui_card("Card_Callout_Solar", (-3.5, 15.5, 7.2), (4.2, 1.4, 0.08))
    add_card_text("Txt_Callout_Solar_Title", card_pv, "SOLAR PANELS", (-1.8, 0.28, 0.04), 0.34)
    add_card_text("Txt_Callout_Solar_Sub", card_pv, "ROOFTOP PV ARRAY", (-1.8, -0.25, 0.04), 0.26, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Solar", (-3.5, 14.7, 7.2), (-3.5, 13.0, 5.8))

    # Card B: Control Unit (ESP32)
    card_ctrl = create_ui_card("Card_Callout_Control", (-12.8, 1.8, 2.4), (4.6, 1.4, 0.08))
    add_card_text("Txt_Callout_Ctrl_Title", card_ctrl, "CONTROL UNIT", (-2.0, 0.28, 0.04), 0.34)
    add_card_text("Txt_Callout_Ctrl_Sub", card_ctrl, "ESP32 MCU • MPPT SENSING", (-2.0, -0.25, 0.04), 0.24, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Control", (-10.4, 1.8, 2.4), (-9.2, 1.8, 0.8))

    # Card C: Relay / Switching Unit
    card_relay = create_ui_card("Card_Callout_Relay", (-7.6, -1.8, 2.2), (4.8, 1.4, 0.08))
    add_card_text("Txt_Callout_Relay_Title", card_relay, "RELAY / SWITCHING UNIT", (-2.1, 0.28, 0.04), 0.32)
    add_card_text("Txt_Callout_Relay_Sub", card_relay, "4-CHANNEL PRIORITY MATRIX", (-2.1, -0.25, 0.04), 0.24, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Relay", (-7.6, -1.0, 2.2), (-7.6, 1.2, 0.8))

    # Card D: Utility Grid
    card_grid = create_ui_card("Card_Callout_Grid", (15.5, -10.5, 6.8), (4.4, 1.4, 0.08))
    add_card_text("Txt_Callout_Grid_Title", card_grid, "UTILITY GRID", (-1.9, 0.28, 0.04), 0.34)
    add_card_text("Txt_Callout_Grid_Sub", card_grid, "11kV / 415V TRANSFORMER", (-1.9, -0.25, 0.04), 0.24, mat=MAT_CARD_BORDER)
    create_pointer_line("Pointer_Callout_Grid", (15.5, -11.3, 6.8), (15.5, -14.2, 5.4))

    # -----------------------------------------------------------------------
    # 2. Main Live Scenario & Value HUD Cards
    # -----------------------------------------------------------------------
    # Scenario Header Card (Top Left)
    card_scenario = create_ui_card("HUD_Scenario_Card", (-15.5, 17.5, 8.5), (9.8, 2.2, 0.08))
    add_card_text("HUD_Scenario_Title", card_scenario, "VOLT VISION  |  SMART MICROGRID", (-4.6, 0.55, 0.04), 0.34)
    add_card_text("HUD_Scenario_Subtitle", card_scenario, "SCENARIO: FULL SOLAR SELF-SUFFICIENCY", (-4.6, -0.05, 0.04), 0.38, mat=MAT_ACCENT_DATA)
    add_card_text("HUD_Scenario_Detail", card_scenario, "HITAM CAMPUS REAL-TIME ENERGY BALANCING", (-4.6, -0.65, 0.04), 0.24, mat=MAT_CARD_BORDER)

    # Power Metrics Dashboard Card (Top Right)
    card_metrics = create_ui_card("HUD_Metrics_Card", (14.5, 16.5, 8.5), (10.4, 4.4, 0.08))
    add_card_text("HUD_Met_Header", card_metrics, "POWER FLOW & VALUE METRICS", (-4.8, 1.65, 0.04), 0.32, mat=MAT_CARD_BORDER)
    add_card_text("HUD_Met_Line_Solar", card_metrics, "SOLAR GEN   :  10.0 kW  (48V / 208A)", (-4.8, 0.95, 0.04), 0.34, mat=MAT_ACCENT_DC)
    add_card_text("HUD_Met_Line_Load", card_metrics, "CAMPUS LOAD :   8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]", (-4.8, 0.25, 0.04), 0.32, mat=MAT_ACCENT_AC)
    add_card_text("HUD_Met_Line_Net", card_metrics, "NET BALANCE :  +1.5 kW  [100% SELF-SUSTAINING]", (-4.8, -0.45, 0.04), 0.32, mat=MAT_ACCENT_DATA)
    add_card_text("HUD_Met_Line_Grid", card_metrics, "GRID IMPORT :   0.0 kW  [STANDBY IDLE]", (-4.8, -1.15, 0.04), 0.32, mat=MAT_ACCENT_GRID)
    add_card_text("HUD_Met_Line_Relay", card_metrics, "RELAYS      :  R1[ON]  R2[ON]  R3[ON]", (-4.8, -1.80, 0.04), 0.30, mat=MAT_CARD_TEXT)

    # -----------------------------------------------------------------------
    # 3. Color-Key Legend Card (Fixed Screen Corner, Bottom Right)
    # -----------------------------------------------------------------------
    card_legend = create_ui_card("HUD_Legend_Card", (15.5, -7.5, 2.5), (7.8, 3.8, 0.08))
    add_card_text("HUD_Legend_Title", card_legend, "CIRCUIT COLOR LEGEND", (-3.5, 1.35, 0.04), 0.32, mat=MAT_CARD_BORDER)
    
    # Legend Rows with Color Accent Stripes
    make_box("Legend_Swatch_DC", (-3.1, 0.70, 0.04), (0.5, 0.12, 0.02), MAT_ACCENT_DC, COL_UI)
    bpy.data.objects["Legend_Swatch_DC"].parent = card_legend
    add_card_text("Legend_Label_DC", card_legend, "DC Power (Solar PV String)", (-2.6, 0.70, 0.04), 0.28)

    make_box("Legend_Swatch_AC", (-3.1, 0.10, 0.04), (0.5, 0.12, 0.02), MAT_ACCENT_AC, COL_UI)
    bpy.data.objects["Legend_Swatch_AC"].parent = card_legend
    add_card_text("Legend_Label_AC", card_legend, "AC Power (Campus Distribution)", (-2.6, 0.10, 0.04), 0.28)

    make_box("Legend_Swatch_Data", (-3.1, -0.50, 0.04), (0.5, 0.12, 0.02), MAT_ACCENT_DATA, COL_UI)
    bpy.data.objects["Legend_Swatch_Data"].parent = card_legend
    add_card_text("Legend_Label_Data", card_legend, "Sensor / Data Feedback (ESP32)", (-2.6, -0.50, 0.04), 0.28)

    make_box("Legend_Swatch_Grid", (-3.1, -1.10, 0.04), (0.5, 0.12, 0.02), MAT_ACCENT_GRID, COL_UI)
    bpy.data.objects["Legend_Swatch_Grid"].parent = card_legend
    add_card_text("Legend_Label_Grid", card_legend, "Utility Grid Connection (11kV)", (-2.6, -1.10, 0.04), 0.28)

    print("Solid dark navy card callout & display system constructed.")

# ---------------------------------------------------------------------------
# Step 5: Scenario Definitions & Dynamic Switcher Function
# ---------------------------------------------------------------------------
SCENARIO_CONFIGS = {
    1: {
        "name": "Full Solar Self-Sufficiency",
        "subtitle": "SCENARIO 1: FULL SOLAR SELF-SUFFICIENCY",
        "solar_txt": "SOLAR GEN   :  10.0 kW  (48V / 208A) [PEAK]",
        "load_txt":  "CAMPUS LOAD :   8.5 kW  [W1:3.5k W2:3.0k W3:2.0k]",
        "net_txt":   "NET BALANCE :  +1.5 kW  [100% SELF-SUSTAINING]",
        "grid_txt":  "GRID IMPORT :   0.0 kW  [STANDBY IDLE]",
        "relay_txt": "RELAYS      :  R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 2.5,
        "ac_glow": 2.4,
        "grid_glow": 0.3,
        "win_dim": False
    },
    2: {
        "name": "Solar Deficit",
        "subtitle": "SCENARIO 2: SOLAR DEFICIT / GRID IMPORT",
        "solar_txt": "SOLAR GEN   :   3.0 kW  (44V / 68A) [OVERCAST]",
        "load_txt":  "CAMPUS LOAD :   7.5 kW  [W1:3.0k W2:2.5k W3:2.0k]",
        "net_txt":   "NET BALANCE :  -4.5 kW  [DEFICIT GAP]",
        "grid_txt":  "GRID IMPORT :  +4.5 kW  [ACTIVE UTILITY DRAW]",
        "relay_txt": "RELAYS      :  R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 1.2,
        "ac_glow": 2.4,
        "grid_glow": 3.0,
        "win_dim": False
    },
    3: {
        "name": "Solar Surplus / Export",
        "subtitle": "SCENARIO 3: SOLAR SURPLUS / GRID EXPORT",
        "solar_txt": "SOLAR GEN   :  12.0 kW  (48V / 250A) [MAX SUN]",
        "load_txt":  "CAMPUS LOAD :   6.0 kW  [W1:2.5k W2:2.0k W3:1.5k]",
        "net_txt":   "NET BALANCE :  +6.0 kW  [SURPLUS EXPORT TO GRID]",
        "grid_txt":  "GRID EXPORT :  +6.0 kW  [REVERSE POWER FLOW]",
        "relay_txt": "RELAYS      :  R1[ON]  R2[ON]  R3[ON]",
        "dc_glow": 3.0,
        "ac_glow": 2.4,
        "grid_glow": 2.6,
        "win_dim": False
    },
    4: {
        "name": "Night / Low-Light Mode",
        "subtitle": "SCENARIO 4: NIGHT / PRIORITY LOAD SHEDDING",
        "solar_txt": "SOLAR GEN   :   0.0 kW  (0V / 0A) [NIGHT INACTIVE]",
        "load_txt":  "CAMPUS LOAD :   4.5 kW  [W1:2.8k W2:1.7k W3:SHED]",
        "net_txt":   "NET BALANCE :  -4.5 kW  [ESP32 SHEDS NON-CRITICAL]",
        "grid_txt":  "GRID IMPORT :  +4.5 kW  [FULL GRID BACKUP]",
        "relay_txt": "RELAYS      :  R1[ON]  R2[ON]  R3[OFF: AUDITORIUM SHED]",
        "dc_glow": 0.1,
        "ac_glow": 1.8,
        "grid_glow": 3.2,
        "win_dim": True
    }
}

def apply_scenario(scene, scenario_id):
    cfg = SCENARIO_CONFIGS.get(scenario_id, SCENARIO_CONFIGS[1])
    print(f"Applying Scenario {scenario_id}: {cfg['name']}")

    # Update Text Objects
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

    # Update Circuit Glow Shaders
    for mat_name, glow in [
        ("Mat_Wire_DC", cfg["dc_glow"]),
        ("Mat_Wire_AC", cfg["ac_glow"]),
        ("Mat_Wire_Grid", cfg["grid_glow"])
    ]:
        m = bpy.data.materials.get(mat_name)
        if m and m.use_nodes:
            bs = m.node_tree.nodes.get("Principled BSDF")
            if bs and "Emission Strength" in bs.inputs:
                bs.inputs["Emission Strength"].default_value = glow

    # Dim non-critical wing windows if load shed
    glass_mat = bpy.data.materials.get("HITAM_WindowGlass")
    if glass_mat and glass_mat.use_nodes:
        bs = glass_mat.node_tree.nodes.get("Principled BSDF")
        if bs and "Emission Strength" in bs.inputs:
            bs.inputs["Emission Strength"].default_value = 0.25 if cfg["win_dim"] else 0.60

    scene["active_scenario"] = scenario_id
    scene["scenario_name"] = cfg["name"]

# ---------------------------------------------------------------------------
# Step 6: Establish Presentation Camera Views
# ---------------------------------------------------------------------------
def setup_presentation_cameras():
    print("Setting up fixed presentation cameras: CAM_TOP_DOWN and CAM_ANGLED_VIEW...")
    
    # 1. Top-Down Aerial View (matching reference diagram)
    cam_top = bpy.data.objects.get("CAM_TOP_DOWN")
    if not cam_top:
        c_data = bpy.data.cameras.new("CAM_TOP_DOWN")
        cam_top = bpy.data.objects.new("CAM_TOP_DOWN", c_data)
        SCENE.collection.objects.link(cam_top)
    
    cam_top.location = (0.0, -1.0, 48.0)
    cam_top.rotation_euler = (0.0, 0.0, 0.0) # True vertical aerial view
    cam_top.data.lens = 35
    cam_top.data.clip_end = 500

    # 2. Angled 3/4 Aerial View (matching reference photo)
    cam_ang = bpy.data.objects.get("CAM_ANGLED_VIEW")
    if not cam_ang:
        c_data = bpy.data.cameras.new("CAM_ANGLED_VIEW")
        cam_ang = bpy.data.objects.new("CAM_ANGLED_VIEW", c_data)
        SCENE.collection.objects.link(cam_ang)

    cam_ang.location = (25.0, -32.0, 24.0)
    # Track to campus center
    target = Vector((0.0, 6.0, 2.5))
    cam_ang.rotation_euler = (target - Vector(cam_ang.location)).to_track_quat("-Z", "Y").to_euler()
    cam_ang.data.lens = 34
    cam_ang.data.clip_end = 500

    # Default to Top Down
    SCENE.camera = cam_top

    # Render settings for presentation
    SCENE.render.engine = "BLENDER_EEVEE"
    SCENE.render.resolution_x = 1920
    SCENE.render.resolution_y = 1080
    SCENE.render.resolution_percentage = 100
    if hasattr(SCENE.eevee, "taa_render_samples"):
        SCENE.eevee.taa_render_samples = 32
    if hasattr(SCENE.eevee, "use_gtao"):
        SCENE.eevee.use_gtao = True

    print("Presentation cameras configured.")

# ---------------------------------------------------------------------------
# Execution Pipeline
# ---------------------------------------------------------------------------
def main():
    print("=== Starting Volt Vision v2 Scene Construction ===")
    cleanup_old_elements()
    build_hitam_academic_complex()
    build_landscaping_and_roads()
    setup_equipment_and_circuits()
    build_card_ui_system()
    setup_presentation_cameras()
    apply_scenario(SCENE, 1)
    
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print(f"=== Successfully Saved VoltVision v2 Scene: {BLEND_PATH} ===")

if __name__ == "__main__":
    main()
