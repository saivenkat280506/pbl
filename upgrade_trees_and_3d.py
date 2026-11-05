"""Volt Vision v2 — Tree Asset Upgrade + 3D Element Enhancement.
Safe version: all material creation deferred inside main(), crash-proof tree placement.
"""

import os, sys, math, random
import bpy, bmesh
from mathutils import Vector

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
ASSET_DIR  = os.path.abspath("main_render/assets/trees")

random.seed(42)

SCENE = bpy.context.scene

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_or_create_col(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or SCENE.collection).children.link(c)
    return c

def link_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob

def get_mat(name, color=(0.5,0.5,0.5), rough=0.5, metal=0.0,
            emit=None, emit_str=1.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs  = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1.0)
    bs.inputs["Roughness"].default_value   = rough
    bs.inputs["Metallic"].default_value    = metal
    if alpha < 1.0:
        bs.inputs["Alpha"].default_value = alpha
        try: m.blend_method = "BLEND"
        except Exception: pass
        if hasattr(m, "surface_render_method"):
            try: m.surface_render_method = "BLENDED"
            except Exception: pass
    if emit:
        bs.inputs["Emission Color"].default_value    = (*emit, 1.0)
        bs.inputs["Emission Strength"].default_value = emit_str
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return m

def make_box(name, loc, size, mat, col, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc; ob.scale = size
    if mat: ob.data.materials.append(mat)
    if bevel > 0.0:
        md = ob.modifiers.new("Bevel","BEVEL")
        md.width = bevel; md.segments = 3
    return link_to(ob, col)

def make_cyl(name, loc, r, d, mat, col, verts=16, rot=(0,0,0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=r, radius2=r, depth=d)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc; ob.rotation_euler = rot
    if mat: ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth = True
    return link_to(ob, col)

def make_cone_obj(name, loc, r1, r2, d, mat, col, verts=16):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=r1, radius2=r2, depth=d)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if mat: ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth = True
    return link_to(ob, col)

# ---------------------------------------------------------------------------
# Import a mesh object from a .blend file via append
# ---------------------------------------------------------------------------
def import_obj_from_blend(blend_path, obj_name):
    if not os.path.exists(blend_path):
        print(f"  [SKIP] Not found: {blend_path}")
        return None
    pre_keys = set(bpy.data.objects.keys())
    try:
        bpy.ops.wm.append(
            filepath  = os.path.join(blend_path, "Object", obj_name),
            directory = os.path.join(blend_path, "Object"),
            filename  = obj_name,
            link      = False,
        )
    except Exception as e:
        print(f"  [ERROR] append {obj_name}: {e}")
        return None
    new_keys = set(bpy.data.objects.keys()) - pre_keys
    if not new_keys:
        print(f"  [WARN] No object appended for {obj_name}")
        return None
    ob = bpy.data.objects.get(next(iter(new_keys)))
    if ob is None:
        return None
    print(f"  Imported: {ob.name}  type={ob.type}  data={ob.data}")
    return ob

# ---------------------------------------------------------------------------
# STEP 1 — Replace simple trees with real .blend assets
# ---------------------------------------------------------------------------
def build_asset_trees():
    print("\n=== STEP 1: Replace trees with real assets ===")

    COL_LAND = get_or_create_col("CAMPUS_LANDSCAPE")

    # --- Remove old simple trees ---
    remove_tags = ("TreeInst_", "CampusTree_", "TreeProto_")
    for ob in list(bpy.data.objects):
        if any(ob.name.startswith(t) for t in remove_tags):
            bpy.data.objects.remove(ob, do_unlink=True)
    print("  Removed old simple tree objects.")

    # --- Import real tree assets ---
    TREE_01_BLEND = os.path.join(ASSET_DIR, "island_tree_01", "island_tree_01_1k.blend")
    TREE_03_BLEND = os.path.join(ASSET_DIR, "island_tree_03", "island_tree_03_1k.blend")

    proto_big = import_obj_from_blend(TREE_01_BLEND, "island_tree_01_LOD0")
    proto_med = import_obj_from_blend(TREE_03_BLEND, "island_tree_03_LOD0")

    # Validate prototypes — they must be MESH with valid mesh data
    def valid_proto(ob):
        return ob is not None and ob.type == "MESH" and ob.data is not None

    protos = []
    if valid_proto(proto_big):
        proto_big.location     = (500, 500, 500)
        proto_big.hide_render  = True
        proto_big.hide_viewport= True
        for c in list(proto_big.users_collection): c.objects.unlink(proto_big)
        COL_LAND.objects.link(proto_big)
        protos.append(("big", proto_big))
    if valid_proto(proto_med):
        proto_med.location     = (520, 500, 500)
        proto_med.hide_render  = True
        proto_med.hide_viewport= True
        for c in list(proto_med.users_collection): c.objects.unlink(proto_med)
        COL_LAND.objects.link(proto_med)
        protos.append(("med", proto_med))

    if not protos:
        print("  [WARN] No valid tree prototypes — using built-in improved trees.")
        _fallback_trees(COL_LAND)
        return

    print(f"  Valid prototypes: {[k for k,_ in protos]}")

    p_map = {k: ob for k, ob in protos}
    def pick(pref):
        for k in ({"big":["big","med"],"med":["med","big"],"small":["med","big"]}.get(pref,["big","med"])):
            if k in p_map: return p_map[k]
        return list(p_map.values())[0]

    def place(idx, tx, ty, sc, rz, pref="big"):
        proto = pick(pref)
        if proto is None or proto.data is None:
            return
        # Share mesh data — materials are already on the mesh, do NOT modify shared data
        inst  = bpy.data.objects.new(f"TreeInst_{idx:04d}", proto.data)
        inst.location       = (tx, ty, 0.0)
        inst.scale          = (sc, sc, sc)
        inst.rotation_euler = (0.0, 0.0, rz)
        COL_LAND.objects.link(inst)

    # Keepouts
    keepouts = [
        (-14.0,1.0,14.0,16.0),(-2.5,-16.0,2.5,3.0),
        (-10.5,0.0,-7.0,3.0),(13.5,-16.5,17.5,-12.5),
    ]
    def in_ko(x,y,pad=1.2):
        return any((x0-pad<=x<=x1+pad and y0-pad<=y<=y1+pad) for x0,y0,x1,y1 in keepouts)

    spots = []
    for x in range(-28,29,4):
        spots += [(x,19.5,1.40,"big"),(x+1.5,22.5,1.60,"big")]
    for x in range(-28,29,4):
        spots += [(x,-21.5,1.35,"big"),(x+2.0,-24.0,1.55,"big")]
    for y in range(-18,20,4):
        spots += [(-20.0,y,1.30,"med"),(-24.0,y+1.5,1.50,"big"),
                   (20.0,y,1.30,"med"),( 24.0,y+1.5,1.50,"big")]
    for tx,ty,sc,pref in [
        (-5.5,-4.5,1.0,"med"),(-7.5,-7.0,1.0,"med"),(-11.0,-6.5,1.1,"med"),
        (-13.5,-11.0,1.1,"med"),(5.5,-4.5,1.0,"med"),(7.5,-7.0,1.0,"med"),
        (11.0,-6.5,1.1,"med"),(13.5,-11.0,1.1,"med"),
        (-15.5,4.0,1.1,"med"),(-15.5,10.0,1.1,"med"),
        (15.5,4.0,1.1,"med"),(15.5,10.0,1.1,"med"),
        (-4.5,8.5,0.95,"med"),(4.5,8.5,0.95,"med"),
        (-8.0,14.5,1.1,"med"),(8.0,14.5,1.1,"med"),
        (-4.0,15.5,0.9,"med"),(4.0,15.5,0.9,"med"),
    ]:
        spots.append((tx,ty,sc,pref))

    count = 0
    for idx,(tx,ty,sc,pref) in enumerate(spots):
        if in_ko(tx,ty): continue
        jx=random.uniform(-0.5,0.5); jy=random.uniform(-0.5,0.5)
        js=sc*random.uniform(0.90,1.10); rz=random.uniform(0,math.pi*2)
        place(count, tx+jx, ty+jy, js, rz, pref)
        count += 1
    print(f"  Placed {count} real-asset tree instances.")


def _fallback_trees(COL_LAND):
    """Improved built-in trees as fallback."""
    MCAN = get_mat("Canopy_Emerald",(0.06,0.20,0.04),rough=0.85)
    MTRK = get_mat("Campus_Trunk",  (0.14,0.08,0.04),rough=0.92)
    spots = [
        (-20,18,1.5),(-10,20,1.4),(0,21,1.6),(10,20,1.4),(20,18,1.5),
        (-22,-18,1.4),(-11,-20,1.3),(0,-22,1.5),(11,-20,1.3),(22,-18,1.4),
        (-20,0,1.3),(20,0,1.3),(-20,8,1.2),(20,8,1.2),
    ]
    for i,(tx,ty,sc) in enumerate(spots):
        make_cyl(f"FBTree_T_{i}",(tx,ty,1.0*sc),0.20*sc,2.0*sc,MTRK,COL_LAND,8)
        blobs=[(0,0,2.6,1.3),(0.5,0.2,2.9,1.0),(-0.5,0.3,2.8,0.9),(0,-0.5,3.3,0.85),(-0.2,-0.2,3.7,0.75)]
        for bi,(bx,by,bz,br) in enumerate(blobs):
            me=bpy.data.meshes.new(f"FBCan_{i}_{bi}")
            bm_=bmesh.new(); bmesh.ops.create_icosphere(bm_,subdivisions=3,radius=br*sc)
            bm_.to_mesh(me); bm_.free()
            ob=bpy.data.objects.new(f"FBCan_{i}_{bi}",me)
            ob.location=(tx+bx*sc,ty+by*sc,bz*sc)
            ob.data.materials.append(MCAN)
            for p in ob.data.polygons: p.use_smooth=True
            link_to(ob,COL_LAND)
    print(f"  Fallback: placed {len(spots)} improved built-in trees.")


# ---------------------------------------------------------------------------
# STEP 2 — Enhance 3D building + detail elements
# ---------------------------------------------------------------------------
def enhance_3d_elements():
    print("\n=== STEP 2: Enhance 3D building elements ===")

    COL_CAM  = get_or_create_col("CAMPUS_ARCHITECTURE")
    COL_DET  = get_or_create_col("CAMPUS_DETAIL")

    # Materials
    MAT_STONE    = get_mat("Detail_Stone",   (0.72,0.68,0.60),rough=0.80)
    MAT_METAL    = get_mat("Detail_Metal",   (0.60,0.60,0.58),rough=0.35,metal=0.85)
    MAT_LAMP     = get_mat("Detail_LampHead",(0.95,0.90,0.75),rough=0.2,
                            emit=(1.0,0.90,0.70),emit_str=3.5)
    MAT_LAMPPOST = get_mat("Detail_LampPost",(0.12,0.12,0.14),rough=0.30,metal=0.80)
    MAT_PLANTER  = get_mat("Detail_Planter", (0.38,0.26,0.16),rough=0.78)
    MAT_SOIL     = get_mat("Detail_Soil",    (0.10,0.07,0.04),rough=0.92)
    MAT_HEDGE    = bpy.data.materials.get("Campus_Hedge") or \
                   get_mat("Campus_Hedge",   (0.04,0.15,0.03),rough=0.85)
    MAT_BOLLARD  = get_mat("Detail_Bollard", (0.20,0.20,0.22),rough=0.40,metal=0.70)
    MAT_CONCRETE = get_mat("Detail_Concrete",(0.55,0.53,0.50),rough=0.85)
    MAT_WALL     = bpy.data.materials.get("HITAM_Plaster") or \
                   get_mat("HITAM_Plaster",  (0.80,0.64,0.44),rough=0.68)
    MAT_PARAPET  = bpy.data.materials.get("HITAM_Terracotta") or \
                   get_mat("HITAM_Terracotta",(0.52,0.16,0.08),rough=0.65)
    MAT_GLASS    = bpy.data.materials.get("HITAM_WindowGlass") or \
                   get_mat("HITAM_WindowGlass",(0.05,0.09,0.14),rough=0.08,
                            emit=(0.85,0.65,0.35),emit_str=0.6)
    MAT_FLAG_R   = get_mat("Flag_Red",  (0.95,0.10,0.10),rough=0.6)
    MAT_FLAG_G   = get_mat("Flag_Green",(0.10,0.72,0.10),rough=0.6)

    # 2a. Window reveals – south facade
    for wi,wx in enumerate([-11.0,-8.5,-6.0,-3.5,3.5,6.0,8.5,11.0]):
        for wz,row in [(2.0,"G"),(4.6,"F1")]:
            make_box(f"WinFrame_S_{row}_{wi}",(wx,2.05,wz),(1.10,0.12,1.30),MAT_WALL,COL_CAM)
            make_box(f"WinGlass_S_{row}_{wi}",(wx,2.09,wz),(0.80,0.04,1.00),MAT_GLASS,COL_CAM)
    # West wing
    for wi,wy in enumerate([-1.0,1.0,3.5,6.5,9.5,12.0]):
        for wz,row in [(2.0,"G"),(4.6,"F1")]:
            make_box(f"WinFrame_W_{row}_{wi}",(-13.95,wy,wz),(0.10,1.10,1.30),MAT_WALL,COL_CAM)
            make_box(f"WinGlass_W_{row}_{wi}",(-13.99,wy,wz),(0.04,0.82,1.00),MAT_GLASS,COL_CAM)
    # East wing
    for wi,wy in enumerate([-1.0,1.0,3.5,6.5,9.5,12.0]):
        for wz,row in [(2.0,"G"),(4.6,"F1")]:
            make_box(f"WinFrame_E_{row}_{wi}",(13.95,wy,wz),(0.10,1.10,1.30),MAT_WALL,COL_CAM)
            make_box(f"WinGlass_E_{row}_{wi}",(13.99,wy,wz),(0.04,0.82,1.00),MAT_GLASS,COL_CAM)

    # 2b. Pilasters on south facade
    for pi,px in enumerate([-12.5,-7.5,-2.5,2.5,7.5,12.5]):
        make_box(f"Pilaster_{pi}",(px,2.10,3.0),(0.55,0.35,6.0),MAT_STONE,COL_CAM,bevel=0.04)
        make_box(f"Pilaster_Cap_{pi}",(px,2.10,6.15),(0.70,0.40,0.30),MAT_STONE,COL_CAM)
        make_box(f"Pilaster_Base_{pi}",(px,2.10,0.15),(0.70,0.40,0.30),MAT_STONE,COL_CAM)

    # 2c. Portico round columns
    for ci,cx in enumerate([-4.2,-1.4,1.4,4.2]):
        make_cyl(f"PorticoCol_{ci}",(cx,0.6,2.8),0.28,5.6,MAT_STONE,COL_CAM,verts=16)
        make_box(f"PorticoCol_Cap_{ci}",(cx,0.6,5.80),(0.70,0.70,0.28),MAT_STONE,COL_CAM)
        make_box(f"PorticoCol_Base_{ci}",(cx,0.6,0.14),(0.70,0.70,0.28),MAT_STONE,COL_CAM)

    # 2d. Cornice / lintel bands
    make_box("Cornice_South_Main",(0.0,2.12,3.45),(27.5,0.38,0.22),MAT_PARAPET,COL_CAM)
    make_box("Cornice_West_Wing", (-14.05,5.5,3.45),(0.38,15.0,0.22),MAT_PARAPET,COL_CAM)
    make_box("Cornice_East_Wing", (14.05,5.5,3.45), (0.38,15.0,0.22),MAT_PARAPET,COL_CAM)
    make_box("Cornice_South_Upper",(0.0,2.12,5.88),(27.5,0.42,0.20),MAT_PARAPET,COL_CAM)

    # 2e. Parapet crenellation
    for bi,bx in enumerate(range(-13,14,2)):
        make_box(f"ParaCren_{bi}",(bx,2.08,6.32),(1.2,0.20,0.32),MAT_PARAPET,COL_CAM)

    # 2f. Flagpole + flag
    make_cyl("Flagpole_Shaft",(1.0,12.8,8.5),0.045,7.0,MAT_METAL,COL_DET,verts=8)
    make_box("Flag_Panel",(1.55,12.8,11.5),(1.1,0.04,0.65),MAT_FLAG_R,COL_DET)
    make_box("Flag_Stripe",(1.55,12.79,11.1),(1.1,0.04,0.20),MAT_FLAG_G,COL_DET)

    # 2g. Rooftop water tank
    make_cyl("RoofTank_Body",(3.5,13.0,7.1),0.70,1.40,MAT_CONCRETE,COL_DET,verts=20)
    make_cone_obj("RoofTank_Dome",(3.5,13.0,7.9),0.70,0.05,0.50,MAT_METAL,COL_DET,verts=20)
    for lx,ly in [(-0.5,-0.5),(0.5,-0.5),(-0.5,0.5),(0.5,0.5)]:
        make_cyl(f"TankLeg_{lx}_{ly}",(3.5+lx*0.55,13.0+ly*0.55,6.4),
                 0.06,0.85,MAT_METAL,COL_DET,verts=6)

    # 2h. HVAC roof units
    for hi,(hx,hy) in enumerate([(-5.5,11.5),(-3.5,11.5),(-1.5,11.5)]):
        make_box(f"HVAC_Unit_{hi}",(hx,hy,6.25),(0.90,0.65,0.42),MAT_CONCRETE,COL_DET,bevel=0.04)
        make_cyl(f"HVAC_Fan_{hi}",(hx,hy,6.50),0.30,0.10,MAT_METAL,COL_DET,verts=16)

    # 2i. Lamp-posts along front promenade
    for li,(lx,ly) in enumerate([(-6.0,-3.5),(6.0,-3.5),(-6.0,-8.0),
                                   (6.0,-8.0),(-6.0,-12.5),(6.0,-12.5)]):
        make_cyl(f"LampPost_Shaft_{li}",(lx,ly,2.5),0.07,5.0,MAT_LAMPPOST,COL_DET,verts=8)
        make_box(f"LampPost_Arm_{li}",(lx,ly-0.4,5.15),(0.12,0.85,0.07),MAT_LAMPPOST,COL_DET)
        make_cyl(f"LampPost_Head_{li}",(lx,ly-0.85,5.05),0.20,0.18,MAT_LAMP,COL_DET,verts=12)

    # 2j. Bollards along path
    for bi,by in enumerate([-4.5,-7.0,-9.5,-12.0]):
        for bx in [-1.4,1.4]:
            make_cyl(f"Bollard_{bi}_{bx}",(bx,by,0.5),0.10,1.0,MAT_BOLLARD,COL_DET,verts=10)
            make_cyl(f"BollardCap_{bi}_{bx}",(bx,by,1.05),0.13,0.08,MAT_BOLLARD,COL_DET,verts=10)

    # 2k. Entrance steps
    for si,(sd,sh,sw) in enumerate([(0.50,0.15,10.5),(1.10,0.30,11.2),(1.70,0.45,11.9)]):
        make_box(f"EntranceStep_{si}",(0.0,1.35-sd,sh*0.5),(sw,sd*2,sh),MAT_STONE,COL_CAM)

    # 2l. Entrance planters with shrubs
    for side,px in [("L",-5.5),("R",5.5)]:
        make_box(f"Planter_Box_{side}",(px,0.8,0.38),(1.40,0.72,0.76),MAT_PLANTER,COL_DET,bevel=0.06)
        make_box(f"Planter_Soil_{side}",(px,0.8,0.72),(1.20,0.60,0.20),MAT_SOIL,COL_DET)
        for ic in range(3):
            sx=px+random.uniform(-0.35,0.35); sy=0.8+random.uniform(-0.18,0.18)
            me2=bpy.data.meshes.new(f"Shrub_{side}_{ic}")
            bm2=bmesh.new()
            bmesh.ops.create_icosphere(bm2,subdivisions=2,radius=random.uniform(0.22,0.30))
            bm2.to_mesh(me2); bm2.free()
            ob2=bpy.data.objects.new(f"Shrub_{side}_{ic}",me2)
            ob2.location=(sx,sy,0.88); ob2.data.materials.append(MAT_HEDGE)
            for p in ob2.data.polygons: p.use_smooth=True
            link_to(ob2,COL_DET)

    # 2m. Gate pillars at campus entrance road
    for side,gx in [("L",-3.5),("R",3.5)]:
        make_box(f"GatePillar_{side}",(gx,-16.5,1.5),(0.80,0.80,3.00),MAT_STONE,COL_DET,bevel=0.05)
        make_box(f"GatePillar_Cap_{side}",(gx,-16.5,3.08),(0.96,0.96,0.22),MAT_STONE,COL_DET)

    print("  3D element enhancement complete.")


# ---------------------------------------------------------------------------
# STEP 3 — Richer ground materials
# ---------------------------------------------------------------------------
def upgrade_ground_materials():
    print("\n=== STEP 3: Upgrade ground materials ===")
    for mname,col,rough in [
        ("Campus_Lawn",   (0.06,0.19,0.04),0.92),
        ("Campus_Asphalt",(0.035,0.038,0.042),0.78),
        ("Campus_Pavers", (0.65,0.62,0.56),0.68),
    ]:
        m=bpy.data.materials.get(mname)
        if m and m.use_nodes:
            bs=m.node_tree.nodes.get("Principled BSDF")
            if bs:
                bs.inputs["Base Color"].default_value=(*col,1.0)
                bs.inputs["Roughness"].default_value=rough
    print("  Done.")


# ---------------------------------------------------------------------------
# STEP 4 — Better render settings
# ---------------------------------------------------------------------------
def upgrade_render_settings():
    print("\n=== STEP 4: Upgrade render settings ===")
    sc=SCENE
    sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=1920; sc.render.resolution_y=1080
    sc.render.resolution_percentage=100
    eevee=sc.eevee
    for attr,val in [("taa_render_samples",64),("use_gtao",True),
                     ("gtao_distance",0.6),("gtao_factor",1.4),
                     ("use_bloom",True),("bloom_threshold",0.8),("bloom_intensity",0.25),
                     ("shadow_cube_size","2048"),("shadow_cascade_size","2048")]:
        if hasattr(eevee,attr):
            try: setattr(eevee,attr,val)
            except Exception: pass
    world=sc.world or bpy.data.worlds.new("World"); sc.world=world
    world.use_nodes=True
    bg=(world.node_tree.nodes.get("Background") or
        world.node_tree.nodes.new("ShaderNodeBackground"))
    bg.inputs["Color"].default_value=(0.42,0.52,0.65,1.0)
    bg.inputs["Strength"].default_value=0.90
    print("  Done.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n====== Volt Vision v2 — Tree & 3D Enhancement ======\n")
    build_asset_trees()
    enhance_3d_elements()
    upgrade_ground_materials()
    upgrade_render_settings()
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print(f"\n=== Saved enhanced scene -> {BLEND_PATH} ===\n")

if __name__ == "__main__":
    main()
