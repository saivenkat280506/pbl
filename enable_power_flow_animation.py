"""Enable traveling dotted power-flow animation on Volt Vision v2 wires.

Matches the solar_management reference:
- Dim emissive base wires (DC / AC / Data)
- Dashed utility grid wire
- Geometry-nodes pulse spheres with zero bevel on FX_Pulse curves
"""
import bpy

BLEND_PATH = bpy.data.filepath or "VoltVision_v2_WORKING.blend"

WIRE_CFG = {
    "Mat_Wire_DC": {
        "color": (1.0, 0.08, 0.05),
        "strength": 1.8,
        "dashed": False,
    },
    "Mat_Wire_AC": {
        "color": (1.0, 0.45, 0.02),
        "strength": 1.8,
        "dashed": False,
    },
    "Mat_Wire_Data": {
        "color": (0.05, 1.0, 0.20),
        "strength": 1.4,
        "dashed": False,
    },
    "Mat_Wire_Grid": {
        "color": (0.75, 0.80, 0.80),
        "strength": 2.2,
        "dashed": True,
        "dash_scale": 40.0,
        "dash_threshold": 0.45,
    },
}

PULSE_SPEED = {
    "DC": 0.18,
    "AC": 0.16,
    "Data": 0.22,
    "Grid": 0.14,
}

# Campus v2 is much larger than the original solar_management scene.
PULSE_RADIUS = {
    "DC": 0.34,
    "AC": 0.30,
    "Data": 0.22,
    "Grid": 0.26,
}


def clear_material_nodes(mat):
    mat.use_nodes = True
    mat.node_tree.nodes.clear()


def build_emissive_wire(mat_name, color, strength):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    clear_material_nodes(mat)
    nt = mat.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = f"Emission_{mat_name.split('_')[-1]}"
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def build_dashed_wire(mat_name, color, strength, dash_scale, dash_threshold):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    clear_material_nodes(mat)
    try:
        mat.blend_method = "BLEND"
    except Exception:
        pass

    nt = mat.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    em_on = nt.nodes.new("ShaderNodeEmission")
    em_on.name = "Emission_Grid"
    em_off = nt.nodes.new("ShaderNodeEmission")
    em_off.name = "Emission"
    tex = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    math_mul = nt.nodes.new("ShaderNodeMath")
    math_mul.operation = "MULTIPLY"
    math_fract = nt.nodes.new("ShaderNodeMath")
    math_fract.operation = "FRACT"
    math_gt = nt.nodes.new("ShaderNodeMath")
    math_gt.operation = "GREATER_THAN"

    em_on.inputs["Color"].default_value = (*color, 1.0)
    em_on.inputs["Strength"].default_value = strength
    em_off.inputs["Color"].default_value = (0.08, 0.08, 0.09, 1.0)
    em_off.inputs["Strength"].default_value = 0.2
    math_mul.inputs[1].default_value = dash_scale
    math_gt.inputs[1].default_value = dash_threshold

    nt.links.new(tex.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["X"], math_mul.inputs[0])
    nt.links.new(math_mul.outputs["Value"], math_fract.inputs[0])
    nt.links.new(math_fract.outputs["Value"], math_gt.inputs[0])
    nt.links.new(math_gt.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(em_off.outputs["Emission"], mix.inputs[1])
    nt.links.new(em_on.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def ensure_pulse_material(mat_name, color, strength=10.0):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    clear_material_nodes(mat)
    try:
        mat.blend_method = "BLEND"
    except Exception:
        pass
    nt = mat.node_tree
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "Emission_DC"
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def set_gn_speed(pulse_ob, speed):
    mod = pulse_ob.modifiers.get("Energy_Pulses")
    if not mod or mod.type != "NODES" or not mod.node_group:
        return
    for node in mod.node_group.nodes:
        if node.name == "Speed_Multiplier" and node.type == "MATH":
            node.inputs[1].default_value = speed


def set_gn_radius(pulse_ob, radius):
    mod = pulse_ob.modifiers.get("Energy_Pulses")
    if not mod or mod.type != "NODES" or not mod.node_group:
        return
    for node in mod.node_group.nodes:
        if node.type == "MESH_PRIMITIVE_ICO_SPHERE":
            node.inputs["Radius"].default_value = radius


def upgrade_wires():
    for mat_name, cfg in WIRE_CFG.items():
        if cfg.get("dashed"):
            build_dashed_wire(
                mat_name,
                cfg["color"],
                cfg["strength"],
                cfg["dash_scale"],
                cfg["dash_threshold"],
            )
        else:
            build_emissive_wire(mat_name, cfg["color"], cfg["strength"])

    ensure_pulse_material("Mat_Pulse_Particle_DC", (1.0, 0.20, 0.08), 24.0)
    ensure_pulse_material("Mat_Pulse_Particle_AC", (1.0, 0.65, 0.10), 24.0)
    ensure_pulse_material("Mat_Pulse_Particle_Data", (0.20, 1.0, 0.45), 20.0)
    ensure_pulse_material("Mat_Pulse_Particle_Grid", (0.85, 0.90, 0.95), 20.0)

    for key, wire_name, pulse_name, pulse_mat in [
        ("DC", "Wire_DC", "FX_Pulse_DC", "Mat_Pulse_Particle_DC"),
        ("AC", "Wire_AC", "FX_Pulse_AC", "Mat_Pulse_Particle_AC"),
        ("Data", "Wire_Data", "FX_Pulse_Data", "Mat_Pulse_Particle_Data"),
        ("Grid", "Wire_Grid", "FX_Pulse_Grid", "Mat_Pulse_Particle_Grid"),
    ]:
        wire = bpy.data.objects.get(wire_name)
        pulse = bpy.data.objects.get(pulse_name)
        mat = bpy.data.materials.get(f"Mat_Wire_{key}")
        if wire and mat:
            if wire.data.materials:
                wire.data.materials[0] = mat
            else:
                wire.data.materials.append(mat)
        if pulse:
            pulse.data.bevel_depth = 0.0
            pulse.hide_render = False
            pulse.hide_viewport = False
            if pulse.data.materials:
                pulse.data.materials[0] = mat
            set_gn_speed(pulse, PULSE_SPEED[key])
            set_gn_radius(pulse, PULSE_RADIUS[key])
            mod = pulse.modifiers.get("Energy_Pulses")
            if mod and mod.node_group:
                for node in mod.node_group.nodes:
                    if node.type == "SET_MATERIAL":
                        pm = bpy.data.materials.get(pulse_mat)
                        if pm:
                            node.inputs["Material"].default_value = pm


def main():
    print("=== Enabling dotted power-flow animation ===")
    upgrade_wires()
    bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
    print(f"Saved: {BLEND_PATH}")


if __name__ == "__main__":
    main()
