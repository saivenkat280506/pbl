"""Render 4 case-variant final-wide stills (balanced/high/low/outage).
Run: blender -b volt_vision_blender/volt_vision.blend --python volt_vision_blender/render_cases.py
Out: renders/cases/case_<name>.png (CAM_Final @ f415, 1920x1080)
Toggle live in Blender: scene['volt_case'] in ('high_solar','low_solar','balanced','outage')
"""
import bpy, os

blend_dir = os.path.dirname(os.path.abspath(bpy.data.filepath))
out = os.path.join(blend_dir, "renders", "cases")
os.makedirs(out, exist_ok=True)

def set_emission(name, strength):
    m = bpy.data.materials.get(name)
    if m is None:
        print("  MISSING", name)
        return
    try:
        n = m.node_tree.nodes.get("Emission")
        if n is not None:
            n.inputs["Strength"].default_value = strength
    except Exception as e:
        print("  emis fail", name, e)

# dark clone for Building-C windows in outage (WinC has load-shed keyframes, so
# case stills swap materials instead of fighting the fcurve). Render at f550
# (SHOT6_Final marker range) so the marker-bound CAM_Final is the render camera.
def clone_emission(name, rgb, strength):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nn = m.node_tree.nodes
    ll = m.node_tree.links
    nn.clear()
    o = nn.new("ShaderNodeOutputMaterial")
    e = nn.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1.0)
    e.inputs["Strength"].default_value = strength
    ll.new(e.outputs["Emission"], o.inputs["Surface"])
    return m

dark = clone_emission("WinC_Outage", (0.25, 0.18, 0.10), 0.05)
lit = clone_emission("WinC_Lit", (1.0, 0.55, 0.15), 6.0)
winc = bpy.data.materials.get("WinC")

CASES = {
    "high_solar": dict(dc=8, ac=8, acc=8, data=6, grid=0.6, wab=9, gridvis=True, xvis=False, cout=False),
    "low_solar": dict(dc=1.5, ac=6, acc=6, data=5, grid=8, wab=7, gridvis=True, xvis=False, cout=False),
    "balanced": dict(dc=5, ac=5, acc=5, data=5, grid=5, wab=8, gridvis=True, xvis=False, cout=False),
    "outage": dict(dc=6, ac=7, acc=0.5, data=5, grid=0, wab=8, gridvis=False, xvis=True, cout=True),
}

s = bpy.context.scene
s.render.image_settings.file_format = 'PNG'
s.render.resolution_percentage = 100
cam = bpy.data.objects.get("CAM_Final")
s.camera = cam
s.frame_current = 550  # inside SHOT6_Final marker range -> marker-bound CAM_Final renders
bpy.context.view_layer.update()

for name, c in CASES.items():
    set_emission("WireDC_Red", c["dc"])
    set_emission("WireAC_Orange", c["ac"])
    set_emission("WireAC_Orange_C", c["acc"])
    set_emission("WireDATA_Green", c["data"])
    set_emission("WireGRID_Dashed", c["grid"])
    set_emission("WinLit", c["wab"])
    for oname, vis in (("GRID_Ctrl_to_Meter", c["gridvis"]), ("GRID_Meter_to_Pole", c["gridvis"]),
                       ("GridOutage_X1", c["xvis"]), ("GridOutage_X2", c["xvis"])):
        o = bpy.data.objects.get(oname)
        if o:
            o.hide_viewport = not vis
            o.hide_render = not vis
    for o in bpy.data.objects:
        if o.name.startswith("Win_C_"):
            try:
                o.data.materials.clear()
                o.data.materials.append(dark if c["cout"] else lit)
            except Exception:
                pass
    bpy.context.view_layer.update()
    s["volt_case"] = name
    s.render.filepath = os.path.join(out, f"case_{name}.png")
    print(f"Rendering case {name} -> {s.render.filepath}")
    bpy.ops.render.render(write_still=True)

# restore balanced defaults
s["volt_case"] = "balanced"
print("DONE cases ->", out)
