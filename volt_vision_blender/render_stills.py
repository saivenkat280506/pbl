"""Render Volt Vision hero stills. Run: blender -b volt_vision.blend --python render_stills.py"""
import bpy, os
blend_dir = os.path.dirname(os.path.abspath(bpy.data.filepath))
out = os.path.join(blend_dir, "renders", "stills")
os.makedirs(out, exist_ok=True)
s = bpy.context.scene
s.render.image_settings.file_format = 'PNG'
s.render.resolution_percentage = 100
jobs = [
    ("CAM_Solar", 50, "shot1_solar.png"),
    ("CAM_Controller", 150, "shot2_controller.png"),
    ("CAM_Battery", 250, "shot3_battery.png"),
    ("CAM_Grid", 350, "shot4_grid.png"),
    ("CAM_Buildings", 410, "shot5_buildings_lit.png"),
    ("CAM_Buildings", 490, "shot5_buildings_shed.png"),
    ("CAM_Final", 550, "shot6_final.png"),
]
for cam_name, frame, fname in jobs:
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        print("MISSING CAM", cam_name)
        continue
    s.camera = cam
    s.frame_current = frame
    # update drivers/animated emission
    bpy.context.view_layer.update()
    s.render.filepath = os.path.join(out, fname)
    print(f"Rendering {fname} cam={cam_name} frame={frame} -> {s.render.filepath}")
    bpy.ops.render.render(write_still=True)
print("DONE stills ->", out)
