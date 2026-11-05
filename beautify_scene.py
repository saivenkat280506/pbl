"""Volt Vision v2 — Comprehensive Beautification Pass.

Fixes identified by comparing current render vs HITAM reference photos:
1. Building walls too white/pale → warm sandy beige (#D4A050 ish)
2. Terracotta/parapet too dull → vivid orange-terracotta
3. Tree LOD0 asset materials are grey (0.8,0.8,0.8) → override with lush green
4. Lighting too flat → warm golden-hour sun, deeper shadows
5. Sky too green-cyan → warm sunset gradient
6. Grass too dark → lush tropical green
7. Building wing labels missing from top-down → add Building A/B/C labels
8. Roof needs distinct terracotta coloring on central wing (matching reference orange roof)
9. All 4 scenarios need proper data & all renders regenerated
10. Pilasters/columns too white → warm stone color
"""

import os, sys, math
import bpy

BLEND_PATH = os.path.abspath("VoltVision_v2_WORKING.blend")
SCENE = bpy.context.scene

# =====================================================================
# 1. FIX BUILDING WALL COLORS — Warm sandy beige
# =====================================================================
def fix_materials():
    print("=== Fixing materials for reference-accurate colors ===")

    color_fixes = {
        # BUILDING WALLS — warm sandy/golden beige (matching HITAM photo)
        "HITAM_Plaster":      {"base": (0.83, 0.62, 0.35), "rough": 0.72},
        "HITAM_PlasterDark":  {"base": (0.60, 0.42, 0.25), "rough": 0.74},
        "Mat_Campus_Wall":    {"base": (0.85, 0.65, 0.38), "rough": 0.70},

        # TERRACOTTA — vivid orange-red (matching reference parapet/trim)
        "HITAM_Terracotta":   {"base": (0.75, 0.28, 0.10), "rough": 0.60},
        "Mat_Campus_Trim":    {"base": (0.78, 0.30, 0.12), "rough": 0.58},

        # ROOF — warm concrete grey with slight warmth
        "HITAM_RoofDeck":     {"base": (0.52, 0.48, 0.42), "rough": 0.78},
        "Mat_Campus_Roof":    {"base": (0.50, 0.46, 0.40), "rough": 0.80},

        # PLINTH — dark warm grey-brown
        "HITAM_Plinth":       {"base": (0.42, 0.36, 0.28), "rough": 0.78},
        "Mat_Campus_Steps":   {"base": (0.75, 0.72, 0.66), "rough": 0.65},

        # GRASS — lush tropical green (matching the vibrant foliage reference)
        "Campus_Lawn":        {"base": (0.10, 0.28, 0.06), "rough": 0.88},
        "Mat_Campus_Lawn":    {"base": (0.15, 0.42, 0.12), "rough": 0.85},

        # HEDGES — rich dark green
        "Campus_Hedge":       {"base": (0.06, 0.20, 0.04), "rough": 0.85},

        # ROAD — dark warm asphalt
        "Campus_Asphalt":     {"base": (0.05, 0.048, 0.045), "rough": 0.82},

        # PAVERS — warm sandy walkway
        "Campus_Pavers":      {"base": (0.68, 0.62, 0.52), "rough": 0.72},

        # STONE details — warm sandstone
        "Detail_Stone":       {"base": (0.76, 0.68, 0.50), "rough": 0.75},
        "Detail_Concrete":    {"base": (0.58, 0.54, 0.48), "rough": 0.82},

        # WINDOW GLASS — darker with warmer interior glow
        "HITAM_WindowGlass":  {"base": (0.04, 0.07, 0.12), "rough": 0.08,
                               "emit": (0.90, 0.70, 0.40), "emit_str": 0.8},
        "HITAM_WinFrame":     {"base": (0.10, 0.08, 0.06), "rough": 0.50, "metal": 0.3},

        # ===  TREE ASSET MATERIAL OVERRIDES  ===
        # The imported LOD0 tree assets have grey (0.8) base — override to green
        "island_tree_01":          {"base": (0.14, 0.08, 0.04), "rough": 0.90},  # bark
        "island_tree_01_branches": {"base": (0.12, 0.07, 0.03), "rough": 0.88},  # branches
        "island_tree_03":          {"base": (0.14, 0.08, 0.04), "rough": 0.90},  # bark
        "island_tree_03_branches": {"base": (0.12, 0.07, 0.03), "rough": 0.88},  # branches

        # TRUNK material
        "Campus_Trunk":       {"base": (0.16, 0.10, 0.05), "rough": 0.90},
    }

    for mat_name, props in color_fixes.items():
        m = bpy.data.materials.get(mat_name)
        if not m:
            continue
        if not m.use_nodes:
            continue
        bs = m.node_tree.nodes.get("Principled BSDF")
        if not bs:
            # If no BSDF, rebuild the shader
            nt = m.node_tree
            nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
            nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
        bc = props.get("base")
        if bc: bs.inputs["Base Color"].default_value = (*bc, 1.0)
        r = props.get("rough")
        if r is not None: bs.inputs["Roughness"].default_value = r
        mt = props.get("metal")
        if mt is not None: bs.inputs["Metallic"].default_value = mt
        em = props.get("emit")
        if em: bs.inputs["Emission Color"].default_value = (*em, 1.0)
        es = props.get("emit_str")
        if es is not None: bs.inputs["Emission Strength"].default_value = es

    # Fix tree LEAF materials — these use image textures but need green override
    for leaf_name in ["island_tree_01_leaves", "island_tree_03_leaves"]:
        m = bpy.data.materials.get(leaf_name)
        if not m:
            continue
        m.use_nodes = True
        nt = m.node_tree
        # Check if it has a BSDF
        bs = nt.nodes.get("Principled BSDF")
        if not bs:
            # Clear and rebuild with green foliage color
            nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
            nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
        # Set to lush green
        bs.inputs["Base Color"].default_value = (0.08, 0.22, 0.04, 1.0)
        bs.inputs["Roughness"].default_value = 0.85
        # Subtle subsurface for leaf translucency
        if "Subsurface Weight" in bs.inputs:
            bs.inputs["Subsurface Weight"].default_value = 0.08

    print(f"  Fixed {len(color_fixes)} materials + leaf overrides.")


# =====================================================================
# 2. FIX LIGHTING — Golden hour warm sun
# =====================================================================
def fix_lighting():
    print("=== Fixing lighting for golden-hour warmth ===")

    # Key Sun Light — warm golden hour
    sun = bpy.data.objects.get("Light_Sun_Key")
    if sun and sun.data:
        sun.data.energy = 8.0
        sun.data.color = (1.0, 0.88, 0.68)  # Warm golden
        sun.rotation_euler = (0.82, -0.15, -0.55)  # Lower angle for golden hour
        if hasattr(sun.data, 'angle'):
            sun.data.angle = 0.04  # Softer shadow edge

    # Fill Light — cool blue skylight bounce
    fill = bpy.data.objects.get("Light_Fill")
    if fill and fill.data:
        fill.data.energy = 180.0
        fill.data.color = (0.60, 0.72, 0.90)  # Cool blue sky bounce

    # Rim Light — warm backlight  
    rim = bpy.data.objects.get("Light_Rim")
    if rim and rim.data:
        rim.data.energy = 120.0
        rim.data.color = (1.0, 0.85, 0.60)  # Warm rim

    print("  Lighting fixed to golden-hour setup.")


# =====================================================================
# 3. FIX WORLD/SKY — Warm sky gradient instead of green
# =====================================================================
def fix_world():
    print("=== Fixing world/sky color ===")
    world = SCENE.world
    if not world:
        world = bpy.data.worlds.new("World")
        SCENE.world = world
    world.use_nodes = True
    nt = world.node_tree

    # Remove all existing nodes
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")

    # Use gradient for sky
    grad = nt.nodes.new("ShaderNodeTexGradient")
    mapping = nt.nodes.new("ShaderNodeMapping")
    texcoord = nt.nodes.new("ShaderNodeTexCoord")

    # Color ramp for sky gradient
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.52, 0.65, 0.78, 1.0)   # Horizon warm blue
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.35, 0.50, 0.72, 1.0)   # Zenith deeper blue

    # Connect nodes
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.2
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    print("  Sky set to warm blue gradient.")


# =====================================================================
# 4. ADD BUILDING WING LABELS (for top-down view)
# =====================================================================
def add_building_wing_labels():
    print("=== Adding Building A/B/C wing labels ===")
    import bmesh

    # Get or create UI collection
    col = None
    for c in bpy.data.collections:
        if c.name == "CAMPUS_UI_SYSTEM":
            col = c; break
    if not col:
        col = bpy.data.collections.new("CAMPUS_UI_SYSTEM")
        SCENE.collection.children.link(col)

    # Remove old wing labels if any
    for name in ["Txt_Wing_A_Title", "Txt_Wing_A_Sub",
                 "Txt_Wing_B_Title", "Txt_Wing_B_Sub",
                 "Txt_Wing_C_Title", "Txt_Wing_C_Sub",
                 "Card_Wing_A", "Card_Wing_B", "Card_Wing_C"]:
        ob = bpy.data.objects.get(name)
        if ob: bpy.data.objects.remove(ob, do_unlink=True)

    def get_card_mat():
        m = bpy.data.materials.get("UI_Card_Navy")
        if not m:
            m = bpy.data.materials.new("UI_Card_Navy")
            m.use_nodes = True
            nt = m.node_tree; nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
            bs.inputs["Base Color"].default_value = (0.06, 0.10, 0.18, 1.0)
            bs.inputs["Roughness"].default_value = 0.25
            bs.inputs["Alpha"].default_value = 0.92
            nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
        return m

    def get_text_mat():
        m = bpy.data.materials.get("UI_Card_Text")
        if not m:
            m = bpy.data.materials.new("UI_Card_Text")
            m.use_nodes = True
            nt = m.node_tree; nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
            bs.inputs["Base Color"].default_value = (0.96, 0.97, 0.99, 1.0)
            bs.inputs["Emission Color"].default_value = (0.96, 0.97, 0.99, 1.0)
            bs.inputs["Emission Strength"].default_value = 1.2
            nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
        return m

    def get_sub_mat():
        m = bpy.data.materials.get("UI_Card_SubText")
        if not m:
            m = bpy.data.materials.new("UI_Card_SubText")
            m.use_nodes = True
            nt = m.node_tree; nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
            bs.inputs["Base Color"].default_value = (0.55, 0.70, 0.88, 1.0)
            bs.inputs["Emission Color"].default_value = (0.55, 0.70, 0.88, 1.0)
            bs.inputs["Emission Strength"].default_value = 1.0
            nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
        return m

    MAT_CARD = get_card_mat()
    MAT_TEXT = get_text_mat()
    MAT_SUB  = get_sub_mat()

    wing_labels = [
        # (name, title, subtitle, x, y, z)
        ("A", "Building A", "Lab (Critical)", -10.5, 8.5, 5.8),
        ("B", "Building B", "Academic",        0.0, 9.0, 5.8),
        ("C", "Building C", "Auditorium",     10.5, 8.5, 5.8),
    ]

    for tag, title, subtitle, wx, wy, wz in wing_labels:
        # Card background
        me = bpy.data.meshes.new(f"Card_Wing_{tag}")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bm.to_mesh(me); bm.free()
        card = bpy.data.objects.new(f"Card_Wing_{tag}", me)
        card.location = (wx, wy, wz)
        card.scale = (3.5, 1.8, 0.08)
        card.data.materials.append(MAT_CARD)
        col.objects.link(card)

        # Title text
        td = bpy.data.curves.new(f"Txt_Wing_{tag}_Title", "FONT")
        td.body = title
        td.size = 0.50
        td.align_x = "CENTER"
        td.extrude = 0.02
        t_ob = bpy.data.objects.new(f"Txt_Wing_{tag}_Title", td)
        t_ob.location = (wx, wy + 0.25, wz + 0.06)
        t_ob.data.materials.append(MAT_TEXT)
        col.objects.link(t_ob)

        # Subtitle
        sd = bpy.data.curves.new(f"Txt_Wing_{tag}_Sub", "FONT")
        sd.body = subtitle
        sd.size = 0.32
        sd.align_x = "CENTER"
        sd.extrude = 0.01
        s_ob = bpy.data.objects.new(f"Txt_Wing_{tag}_Sub", sd)
        s_ob.location = (wx, wy - 0.35, wz + 0.06)
        s_ob.data.materials.append(MAT_SUB)
        col.objects.link(s_ob)

    print("  Building wing labels added.")


# =====================================================================
# 5. FIX RENDER SETTINGS — Better quality
# =====================================================================
def fix_render_settings():
    print("=== Fixing render settings ===")
    sc = SCENE
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 100

    eevee = sc.eevee
    settings = {
        "taa_render_samples": 128,
        "use_gtao": True,
        "gtao_distance": 0.8,
        "gtao_factor": 1.5,
        "use_bloom": True,
        "bloom_threshold": 0.75,
        "bloom_intensity": 0.15,
        "bloom_radius": 6.5,
    }
    for attr, val in settings.items():
        if hasattr(eevee, attr):
            try: setattr(eevee, attr, val)
            except: pass

    # Color management — slightly warm filmic look
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium High Contrast"
    sc.view_settings.exposure = 0.2
    sc.view_settings.gamma = 1.05

    print("  Render settings optimized.")


# =====================================================================
# Main
# =====================================================================
def main():
    print("\n====== Volt Vision v2 — Comprehensive Beautification ======\n")
    fix_materials()
    fix_lighting()
    fix_world()
    add_building_wing_labels()
    fix_render_settings()
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print(f"\n=== Saved beautified scene -> {BLEND_PATH} ===\n")

if __name__ == "__main__":
    main()
