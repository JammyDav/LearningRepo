"""
build_lab.py  —  v2 "AAA pass"

Procedural Blender script for the CBRE Lab Safety VR Induction environment.
Two-room lab (main lab + prep room) with full architectural detail, cabinetry,
props, bevelled edges and smooth-shaded cylinders. Exports web/assets/lab.glb.

Run headless:
    blender --background --python blender/build_lab.py

CRITICAL: every HAZARD_* mesh name is contract API for web/main.js — do not
rename them. ctx_* meshes are deliberate non-hazard context items.

Floor plan (Blender Z up, metres):
    Main lab : (0,0) to (8,6)
    Prep room: (8,1) to (12,5)
    Internal doorway: X=8, Y=2..3
    Entrance door (south wall): X=1..2, Y=0
    Window bank (north wall): X=2..6, Z=1.2..2.2
"""

import bpy
import math
import os

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

WALL_HEIGHT = 2.7
CEIL_DROP = 2.55          # suspended ceiling height
WALL_THICK = 0.10
DOOR_WIDTH = 1.0
DOOR_HEIGHT = 2.1

MAIN = (0.0, 0.0, 8.0, 6.0)
PREP = (8.0, 1.0, 12.0, 5.0)

ENTRANCE = (1.0, 2.0)
INTERNAL_DOOR = (2.0, 3.0)
WINDOW_X = (2.0, 6.0)
WINDOW_Z = (1.2, 2.2)

BENCH_DEPTH = 0.7
BENCH_HEIGHT = 0.9
TOP_THICK = 0.04
SHELF_HEIGHT = 1.7
SHELF_DEPTH = 0.3

OUTPUT_GLB = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "web", "assets", "lab.glb")
)

# ----------------------------------------------------------------------------
# Materials — name: (rgba, roughness, metallic [, emission_strength])
# ----------------------------------------------------------------------------

PALETTE = {
    # architecture
    "floor_a":     ((0.55, 0.57, 0.60, 1.0), 0.30, 0.0),
    "floor_b":     ((0.47, 0.49, 0.53, 1.0), 0.30, 0.0),
    "wall":        ((0.91, 0.91, 0.89, 1.0), 0.85, 0.0),
    "wall_accent": ((0.74, 0.80, 0.82, 1.0), 0.85, 0.0),
    "skirting":    ((0.32, 0.34, 0.37, 1.0), 0.55, 0.0),
    "ceiling_tile":((0.94, 0.94, 0.93, 1.0), 0.95, 0.0),
    "ceiling_grid":((0.62, 0.63, 0.65, 1.0), 0.40, 0.6),
    "trim":        ((0.55, 0.58, 0.62, 1.0), 0.45, 0.3),
    "door":        ((0.62, 0.71, 0.78, 1.0), 0.55, 0.0),
    "door_frame":  ((0.45, 0.48, 0.52, 1.0), 0.50, 0.2),
    "window":      ((0.62, 0.78, 0.86, 0.22), 0.05, 0.0),
    "stainless":   ((0.78, 0.79, 0.80, 1.0), 0.25, 0.9),
    "hedge":       ((0.30, 0.42, 0.24, 1.0), 0.95, 0.0),

    # furniture
    "worktop":     ((0.13, 0.14, 0.16, 1.0), 0.28, 0.0),
    "cabinet":     ((0.80, 0.79, 0.76, 1.0), 0.55, 0.0),
    "cabinet_door":((0.84, 0.83, 0.80, 1.0), 0.50, 0.0),
    "plinth":      ((0.25, 0.26, 0.28, 1.0), 0.70, 0.0),
    "shelf":       ((0.86, 0.85, 0.82, 1.0), 0.55, 0.0),
    "bench_body":  ((0.82, 0.80, 0.76, 1.0), 0.55, 0.0),
    "bench_top":   ((0.13, 0.14, 0.16, 1.0), 0.28, 0.0),
    "stool_seat":  ((0.18, 0.30, 0.42, 1.0), 0.60, 0.0),
    "locker":      ((0.52, 0.58, 0.64, 1.0), 0.40, 0.4),

    # lighting
    "light":       ((1.00, 0.98, 0.92, 1.0), 0.20, 0.0, 4.0),

    # props
    "ext_red":     ((0.72, 0.12, 0.10, 1.0), 0.40, 0.0),
    "firstaid":    ((0.93, 0.94, 0.95, 1.0), 0.40, 0.0),
    "sign_green":  ((0.10, 0.48, 0.27, 1.0), 0.60, 0.0),
    "poster_body": ((0.95, 0.95, 0.94, 1.0), 0.80, 0.0),
    "poster_blue": ((0.20, 0.40, 0.62, 1.0), 0.70, 0.0),
    "poster_red":  ((0.75, 0.25, 0.20, 1.0), 0.70, 0.0),
    "poster_text": ((0.55, 0.57, 0.60, 1.0), 0.80, 0.0),
    "flam_yellow": ((0.88, 0.72, 0.12, 1.0), 0.45, 0.1),
    "glass_clear": ((0.80, 0.86, 0.88, 0.25), 0.05, 0.0),
    "glass_dark":  ((0.10, 0.13, 0.16, 1.0), 0.08, 0.0),
    "liquid_blue": ((0.30, 0.55, 0.80, 0.85), 0.10, 0.0),
    "liquid_amber":((0.80, 0.55, 0.18, 0.9), 0.10, 0.0),
    "mat_dark":    ((0.10, 0.10, 0.11, 1.0), 0.90, 0.0),
    "tape_yellow": ((0.92, 0.78, 0.10, 1.0), 0.60, 0.0),
    "tape_black":  ((0.08, 0.08, 0.08, 1.0), 0.60, 0.0),

    # hazards
    "h_fume":      ((0.85, 0.87, 0.88, 1.0), 0.40, 0.1),
    "h_eyewash":   ((0.18, 0.72, 0.38, 1.0), 0.45, 0.0),
    "h_bottle":    ((0.93, 0.80, 0.22, 1.0), 0.40, 0.0),
    "h_cable":     ((0.85, 0.25, 0.22, 1.0), 0.50, 0.0),
    "h_cylinder":  ((0.45, 0.50, 0.55, 1.0), 0.30, 0.7),
    "h_bin":       ((0.38, 0.42, 0.50, 1.0), 0.55, 0.0),
    "h_ppe":       ((0.95, 0.95, 0.95, 1.0), 0.80, 0.0),
    "hivis":       ((0.95, 0.48, 0.06, 1.0), 0.75, 0.0),
    "street_navy": ((0.15, 0.19, 0.30, 1.0), 0.75, 0.0),
    "coat_shadow": ((0.78, 0.78, 0.80, 1.0), 0.80, 0.0),
    "obstruct":    ((0.58, 0.44, 0.30, 1.0), 0.80, 0.0),

    # text / labels
    "label_dark":  ((0.08, 0.08, 0.10, 1.0), 0.60, 0.0),
    "label_red":   ((0.80, 0.18, 0.16, 1.0), 0.55, 0.0),
    "label_white": ((0.97, 0.97, 0.97, 1.0), 0.60, 0.0),
}

_mat_cache = {}

def mat(name):
    if name in _mat_cache:
        return _mat_cache[name]
    spec = PALETTE[name]
    rgba, rough, metal = spec[0], spec[1], spec[2]
    emit = spec[3] if len(spec) > 3 else 0.0
    m = bpy.data.materials.new(name=f"M_{name}")
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0:
        bsdf.inputs["Emission Color"].default_value = rgba
        bsdf.inputs["Emission Strength"].default_value = emit
    if rgba[3] < 1.0:
        bsdf.inputs["Alpha"].default_value = rgba[3]
        m.blend_method = "BLEND"
    _mat_cache[name] = m
    return m

# ----------------------------------------------------------------------------
# Primitive helpers
# ----------------------------------------------------------------------------

def _finish(obj, material, coll, bevel=0.0, smooth=False):
    if material is not None:
        obj.data.materials.append(material)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
    if smooth:
        try:
            bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
        except Exception:
            try:
                bpy.ops.object.shade_smooth()
            except Exception:
                pass
    if coll is not None:
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)
    return obj

def add_box(name, x1, y1, z1, x2, y2, z2, material, coll=None, bevel=0.0):
    cx, cy, cz = (x1+x2)/2, (y1+y2)/2, (z1+z2)/2
    sx, sy, sz = abs(x2-x1), abs(y2-y1), abs(z2-z1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(obj, material, coll, bevel=bevel)

def add_cylinder(name, cx, cy, z_base, radius, height, material,
                 segments=20, coll=None, smooth=True, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments, radius=radius, depth=height,
        location=(cx, cy, z_base + height/2))
    obj = bpy.context.active_object
    obj.name = name
    return _finish(obj, material, coll, bevel=bevel, smooth=smooth)

def add_cone(name, cx, cy, z_base, r1, r2, height, material,
             segments=20, coll=None, smooth=True):
    bpy.ops.mesh.primitive_cone_add(
        vertices=segments, radius1=r1, radius2=r2, depth=height,
        location=(cx, cy, z_base + height/2))
    obj = bpy.context.active_object
    obj.name = name
    return _finish(obj, material, coll, smooth=smooth)

def add_torus(name, cx, cy, cz, major_r, minor_r, material, coll=None):
    bpy.ops.mesh.primitive_torus_add(
        location=(cx, cy, cz), major_radius=major_r, minor_radius=minor_r,
        major_segments=24, minor_segments=8)
    obj = bpy.context.active_object
    obj.name = name
    return _finish(obj, material, coll, smooth=True)

def add_text(name, body_str, x, y, z, facing="+x", size=0.08, extrude=0.005,
             material=None, coll=None, wrap_radius=None):
    """Extruded text-as-mesh. If wrap_radius is set, the glyphs are bent around
    a vertical cylinder of that radius whose axis sits wrap_radius behind the
    text origin (i.e. place the object wrap_radius in front of the bottle axis
    and the text hugs the bottle)."""
    bpy.ops.object.text_add(location=(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = body_str
    obj.data.size = size
    obj.data.extrude = extrude
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    rot = {
        "+x": (math.pi/2, 0,  math.pi/2),
        "-x": (math.pi/2, 0, -math.pi/2),
        "+y": (math.pi/2, 0,  math.pi),
        "-y": (math.pi/2, 0,  0.0),
    }[facing]
    obj.rotation_euler = rot
    bpy.ops.object.convert(target="MESH")
    if wrap_radius is not None:
        # Pre-rotation local space: x = reading direction, y = up, z = out of face.
        # Map onto cylinder: tangent point at local origin, axis at local z=-R.
        R = wrap_radius
        for v in obj.data.vertices:
            phi = v.co.x / R
            radial = R + v.co.z
            v.co.x = radial * math.sin(phi)
            v.co.z = radial * math.cos(phi) - R
    return _finish(obj, material, coll)

def add_cable_curve(name, points, radius=0.012, material=None, coll=None):
    curve_data = bpy.data.curves.new(name + "_curve", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.resolution_u = 10
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, (px, py, pz) in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = (px, py, pz)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return _finish(obj, material, coll, smooth=True)

def get_or_create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.curves):
        for item in list(block):
            block.remove(item)

# ============================================================================
# SHELL
# ============================================================================

def build_floors(coll):
    """1m vinyl tiles in alternating greys."""
    def tiles(room_name, x1, y1, x2, y2):
        ix0, iy0 = int(x1), int(y1)
        for ix in range(int(x1), int(x2)):
            for iy in range(int(y1), int(y2)):
                m = mat("floor_a") if (ix + iy) % 2 == 0 else mat("floor_b")
                add_box(f"floor_{room_name}_{ix}_{iy}",
                        ix, iy, -0.02, ix+1, iy+1, 0.0, m, coll)
    tiles("main", *MAIN)
    tiles("prep", *PREP)

def build_ceilings(coll):
    """Structural slab + suspended grid with tiles and recessed troffers."""
    for room_name, (x1, y1, x2, y2) in (("main", MAIN), ("prep", PREP)):
        # structural slab (above the suspended ceiling, barely visible)
        add_box(f"slab_{room_name}", x1, y1, WALL_HEIGHT, x2, y2, WALL_HEIGHT+0.02,
                mat("ceiling_tile"), coll)
        # suspended tile plane
        add_box(f"ceiling_{room_name}", x1, y1, CEIL_DROP, x2, y2, CEIL_DROP+0.02,
                mat("ceiling_tile"), coll)
        # T-bar grid (1.2 m spacing both ways)
        gx = x1 + 1.2
        i = 0
        while gx < x2 - 0.05:
            add_box(f"grid_{room_name}_x{i}", gx-0.012, y1, CEIL_DROP-0.018,
                    gx+0.012, y2, CEIL_DROP+0.001, mat("ceiling_grid"), coll)
            gx += 1.2; i += 1
        gy = y1 + 1.2
        i = 0
        while gy < y2 - 0.05:
            add_box(f"grid_{room_name}_y{i}", x1, gy-0.012, CEIL_DROP-0.018,
                    x2, gy+0.012, CEIL_DROP+0.001, mat("ceiling_grid"), coll)
            gy += 1.2; i += 1

def build_troffers(coll):
    """Recessed 1.2x0.6 light troffers with metal frame + emissive diffuser."""
    positions_main = [(2.0, 1.2), (5.0, 1.2), (2.0, 3.0), (5.0, 3.0), (2.0, 4.8), (5.0, 4.8)]
    positions_prep = [(9.2, 3.0), (10.9, 3.0)]
    def troffer(tag, cx, cy):
        add_box(f"troffer_frame_{tag}",
                cx-0.62, cy-0.32, CEIL_DROP-0.010, cx+0.62, cy+0.32, CEIL_DROP+0.005,
                mat("ceiling_grid"), coll)
        # Diffuser hangs BELOW the frame so it is visible from the room
        add_box(f"troffer_light_{tag}",
                cx-0.56, cy-0.26, CEIL_DROP-0.024, cx+0.56, cy+0.26, CEIL_DROP-0.009,
                mat("light"), coll)
    for i, (cx, cy) in enumerate(positions_main): troffer(f"m{i}", cx, cy)
    for i, (cx, cy) in enumerate(positions_prep): troffer(f"p{i}", cx, cy)

def add_wall_segment(name, x1, y1, x2, y2, z1=0.0, z2=WALL_HEIGHT, coll=None):
    if abs(x1 - x2) < 1e-6:
        add_box(name, x1 - WALL_THICK/2, min(y1,y2), z1,
                x1 + WALL_THICK/2, max(y1,y2), z2, mat("wall"), coll)
    else:
        add_box(name, min(x1,x2), y1 - WALL_THICK/2, z1,
                max(x1,x2), y1 + WALL_THICK/2, z2, mat("wall"), coll)

def build_walls(coll):
    # Main south wall, split around entrance
    add_wall_segment("wall_main_south_a", 0.0, 0.0, ENTRANCE[0], 0.0, coll=coll)
    add_wall_segment("wall_main_south_b", ENTRANCE[1], 0.0, MAIN[2], 0.0, coll=coll)
    add_wall_segment("wall_main_south_lintel", ENTRANCE[0], 0.0, ENTRANCE[1], 0.0,
                     z1=DOOR_HEIGHT, z2=WALL_HEIGHT, coll=coll)

    # Main north wall with window bank
    add_wall_segment("wall_main_north_a", 0.0, MAIN[3], WINDOW_X[0], MAIN[3], coll=coll)
    add_wall_segment("wall_main_north_b", WINDOW_X[1], MAIN[3], MAIN[2], MAIN[3], coll=coll)
    add_wall_segment("wall_main_north_sill", WINDOW_X[0], MAIN[3], WINDOW_X[1], MAIN[3],
                     z1=0.0, z2=WINDOW_Z[0], coll=coll)
    add_wall_segment("wall_main_north_header", WINDOW_X[0], MAIN[3], WINDOW_X[1], MAIN[3],
                     z1=WINDOW_Z[1], z2=WALL_HEIGHT, coll=coll)

    # West wall
    add_wall_segment("wall_main_west", 0.0, 0.0, 0.0, MAIN[3], coll=coll)

    # East wall / shared wall with prep
    add_wall_segment("wall_main_east_south", MAIN[2], 0.0, MAIN[2], PREP[1], coll=coll)
    add_wall_segment("wall_main_east_north", MAIN[2], PREP[3], MAIN[2], MAIN[3], coll=coll)
    add_wall_segment("wall_shared_a", MAIN[2], PREP[1], MAIN[2], INTERNAL_DOOR[0], coll=coll)
    add_wall_segment("wall_shared_b", MAIN[2], INTERNAL_DOOR[1], MAIN[2], PREP[3], coll=coll)
    add_wall_segment("wall_shared_lintel", MAIN[2], INTERNAL_DOOR[0], MAIN[2], INTERNAL_DOOR[1],
                     z1=DOOR_HEIGHT, z2=WALL_HEIGHT, coll=coll)

    # Prep walls
    add_wall_segment("wall_prep_south", PREP[0], PREP[1], PREP[2], PREP[1], coll=coll)
    add_wall_segment("wall_prep_north", PREP[0], PREP[3], PREP[2], PREP[3], coll=coll)
    add_wall_segment("wall_prep_east", PREP[2], PREP[1], PREP[2], PREP[3], coll=coll)

def build_skirting(coll):
    """Dark skirting along interior wall faces (skipping door openings)."""
    s = mat("skirting")
    H = 0.10
    T = 0.018
    def run_x(tag, x1, x2, y, side):
        # side +1: skirting on +Y side of wall face; -1 opposite
        yf = y + (WALL_THICK/2) * side
        add_box(f"skirt_{tag}", x1, yf, 0.0, x2, yf + T*side, H, s, coll)
    def run_y(tag, y1, y2, x, side):
        xf = x + (WALL_THICK/2) * side
        add_box(f"skirt_{tag}", xf, y1, 0.0, xf + T*side, y2, H, s, coll)
    # Main lab interior
    run_x("ms_a", 0.0, ENTRANCE[0], 0.0, +1)
    run_x("ms_b", ENTRANCE[1], 8.0, 0.0, +1)
    run_x("mn",   0.0, 8.0, MAIN[3], -1)
    run_y("mw",   0.0, 6.0, 0.0, +1)
    run_y("me_a", 0.0, INTERNAL_DOOR[0], MAIN[2], -1)
    run_y("me_b", INTERNAL_DOOR[1], 6.0, MAIN[2], -1)
    # Prep interior
    run_x("ps",   PREP[0], PREP[2], PREP[1], +1)
    run_x("pn",   PREP[0], PREP[2], PREP[3], -1)
    run_y("pe",   PREP[1], PREP[3], PREP[2], -1)
    run_y("pw_a", PREP[1], INTERNAL_DOOR[0], MAIN[2], +1)
    run_y("pw_b", INTERNAL_DOOR[1], PREP[3], MAIN[2], +1)

def build_entrance_door(coll):
    """Door leaf with vision panel, kick plate, push plate + frame."""
    x1, x2 = ENTRANCE
    fr = mat("door_frame")
    # Frame jambs + head
    add_box("doorframe_jamb_l", x1-0.06, -0.07, 0.0, x1+0.01, 0.07, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)
    add_box("doorframe_jamb_r", x2-0.01, -0.07, 0.0, x2+0.06, 0.07, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)
    add_box("doorframe_head",   x1-0.06, -0.07, DOOR_HEIGHT, x2+0.06, 0.07, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)
    # Leaf
    add_box("door_entrance", x1+0.02, -0.025, 0.0, x2-0.02, 0.025, DOOR_HEIGHT-0.02,
            mat("door"), coll, bevel=0.006)
    # Vision panel (glass) with frame
    add_box("door_vision_frame", x1+0.32, -0.030, 1.35, x2-0.32, 0.030, 1.85, fr, coll, bevel=0.003)
    # Dark glazing (reads as an unlit corridor beyond — the leaf behind is solid)
    add_box("door_vision_glass", x1+0.36, -0.012, 1.39, x2-0.36, 0.012, 1.81, mat("glass_dark"), coll)
    # Kick plate + push plate (stainless)
    add_box("door_kickplate", x1+0.03, 0.026, 0.02, x2-0.03, 0.034, 0.28, mat("stainless"), coll)
    add_box("door_pushplate", x2-0.30, 0.026, 0.95, x2-0.12, 0.034, 1.45, mat("stainless"), coll)
    # Handle on outside face
    add_box("door_handle_out", x2-0.28, -0.045, 1.05, x2-0.14, -0.026, 1.09, mat("stainless"), coll, bevel=0.004)

def build_internal_doorway(coll):
    """Architrave around the open doorway between rooms."""
    fr = mat("door_frame")
    y1, y2 = INTERNAL_DOOR
    x = MAIN[2]
    add_box("idoor_jamb_s", x-0.08, y1-0.06, 0.0, x+0.08, y1+0.01, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)
    add_box("idoor_jamb_n", x-0.08, y2-0.01, 0.0, x+0.08, y2+0.06, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)
    add_box("idoor_head",   x-0.08, y1-0.06, DOOR_HEIGHT, x+0.08, y2+0.06, DOOR_HEIGHT+0.06, fr, coll, bevel=0.004)

def build_windows(coll):
    """Window bank: frame, mullions, panes, interior sill board."""
    fr = mat("door_frame")
    y = MAIN[3]
    z1, z2 = WINDOW_Z
    x1, x2 = WINDOW_X
    # Outer frame
    add_box("win_frame_bottom", x1, y-0.06, z1-0.04, x2, y+0.06, z1, fr, coll, bevel=0.003)
    add_box("win_frame_top",    x1, y-0.06, z2, x2, y+0.06, z2+0.04, fr, coll, bevel=0.003)
    add_box("win_frame_l",      x1-0.04, y-0.06, z1, x1, y+0.06, z2, fr, coll, bevel=0.003)
    add_box("win_frame_r",      x2, y-0.06, z1, x2+0.04, y+0.06, z2, fr, coll, bevel=0.003)
    # Mullions at 1m spacing
    for i, mx in enumerate([3.0, 4.0, 5.0]):
        add_box(f"win_mullion_{i}", mx-0.022, y-0.05, z1, mx+0.022, y+0.05, z2, fr, coll, bevel=0.003)
    # Panes (4)
    panes = [(x1, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, x2)]
    for i, (px1, px2) in enumerate(panes):
        add_box(f"window_pane_{i}", px1+0.01, y-0.012, z1+0.01, px2-0.01, y+0.012, z2-0.01,
                mat("window"), coll)
    # Interior sill board
    add_box("win_sill_board", x1-0.05, y-0.18, z1-0.025, x2+0.05, y-0.05, z1,
            mat("cabinet_door"), coll, bevel=0.005)

def build_exterior(coll):
    """Hedge visible through the windows so the outside isn't a void."""
    add_box("ext_hedge", 0.0, MAIN[3]+0.6, 0.0, 12.0, MAIN[3]+1.3, 0.95, mat("hedge"), coll, bevel=0.02)
    add_box("ext_hedge2", 1.0, MAIN[3]+2.2, 0.0, 11.0, MAIN[3]+2.9, 1.4, mat("hedge"), coll, bevel=0.02)

# ============================================================================
# FURNITURE
# ============================================================================

def cabinet_run(tag, axis, fixed, lo, hi, face_dir, coll):
    """Under-bench cabinet run with plinth, carcase, door fronts and handles.

    axis 'y': run along Y at wall X (west bench).  face_dir +1 = doors face +X.
    axis 'x': run along X at wall Y (south bench). face_dir +1 = doors face +Y.
    For the island, face_dir -1 with axis 'x' = doors face -Y.
    `fixed` is the wall-side coordinate of the carcase back.
    """
    cab = mat("cabinet"); cdoor = mat("cabinet_door"); st = mat("stainless")
    depth = BENCH_DEPTH
    body_top = BENCH_HEIGHT - TOP_THICK
    if axis == "y":
        back = fixed
        front = fixed + depth * face_dir
        # plinth (recessed)
        add_box(f"{tag}_plinth", min(back, front - 0.06*face_dir), lo+0.03, 0.0,
                max(back, front - 0.06*face_dir), hi-0.03, 0.12, mat("plinth"), coll)
        # carcase
        add_box(f"{tag}_carcase", min(back, front), lo, 0.12,
                max(back, front), hi, body_top, cab, coll, bevel=0.004)
        # worktop with overhang
        add_box(f"{tag}_top", min(back, front + 0.03*face_dir), lo-0.015, body_top,
                max(back, front + 0.03*face_dir), hi+0.015, BENCH_HEIGHT,
                mat("worktop"), coll, bevel=0.006)
        # splashback on the wall
        sb_x = back + 0.005*face_dir
        add_box(f"{tag}_splash", min(back, sb_x + 0.018*face_dir), lo, BENCH_HEIGHT,
                max(back, sb_x + 0.018*face_dir), hi, BENCH_HEIGHT+0.12, mat("worktop"), coll)
        # door fronts
        run = hi - lo
        n = max(1, round(run / 0.5))
        w = run / n
        df1 = front
        df2 = front + 0.018 * face_dir
        for i in range(n):
            d1 = lo + i*w + 0.008
            d2 = lo + (i+1)*w - 0.008
            add_box(f"{tag}_door_{i}", min(df1, df2), d1, 0.15, max(df1, df2), d2, body_top-0.02,
                    cdoor, coll, bevel=0.004)
            # handle near top
            h1 = front + 0.018*face_dir
            h2 = front + 0.042*face_dir
            hc = (d1+d2)/2
            add_box(f"{tag}_handle_{i}", min(h1, h2), hc-0.06, body_top-0.10,
                    max(h1, h2), hc+0.06, body_top-0.075, st, coll, bevel=0.003)
    else:
        back = fixed
        front = fixed + depth * face_dir
        add_box(f"{tag}_plinth", lo+0.03, min(back, front - 0.06*face_dir), 0.0,
                hi-0.03, max(back, front - 0.06*face_dir), 0.12, mat("plinth"), coll)
        add_box(f"{tag}_carcase", lo, min(back, front), 0.12,
                hi, max(back, front), body_top, cab, coll, bevel=0.004)
        add_box(f"{tag}_top", lo-0.015, min(back, front + 0.03*face_dir), body_top,
                hi+0.015, max(back, front + 0.03*face_dir), BENCH_HEIGHT,
                mat("worktop"), coll, bevel=0.006)
        run = hi - lo
        n = max(1, round(run / 0.5))
        w = run / n
        df1 = front
        df2 = front + 0.018 * face_dir
        for i in range(n):
            d1 = lo + i*w + 0.008
            d2 = lo + (i+1)*w - 0.008
            add_box(f"{tag}_door_{i}", d1, min(df1, df2), 0.15, d2, max(df1, df2), body_top-0.02,
                    mat("cabinet_door"), coll, bevel=0.004)
            h1 = front + 0.018*face_dir
            h2 = front + 0.042*face_dir
            hc = (d1+d2)/2
            add_box(f"{tag}_handle_{i}", hc-0.06, min(h1, h2), body_top-0.10,
                    hc+0.06, max(h1, h2), body_top-0.075, mat("stainless"), coll, bevel=0.003)

def wall_shelf(tag, x1, y1, x2, y2, coll):
    """Shelf with L-brackets."""
    sh = mat("shelf"); br = mat("trim")
    add_box(tag, x1, y1, SHELF_HEIGHT, x2, y2, SHELF_HEIGHT+0.028, sh, coll, bevel=0.004)
    # brackets every ~0.8m along the long axis
    if (y2 - y1) > (x2 - x1):
        n = max(2, int((y2-y1) / 0.8) + 1)
        for i in range(n):
            by = y1 + 0.06 + (y2-y1-0.12) * i / (n-1)
            add_box(f"{tag}_brk_{i}v", x1, by-0.012, SHELF_HEIGHT-0.22, x1+0.025, by+0.012, SHELF_HEIGHT, br, coll)
            add_box(f"{tag}_brk_{i}h", x1, by-0.012, SHELF_HEIGHT-0.03, x2-0.03, by+0.012, SHELF_HEIGHT, br, coll)
    else:
        n = max(2, int((x2-x1) / 0.8) + 1)
        for i in range(n):
            bx = x1 + 0.06 + (x2-x1-0.12) * i / (n-1)
            add_box(f"{tag}_brk_{i}v", bx-0.012, y2-0.025, SHELF_HEIGHT-0.22, bx+0.012, y2, SHELF_HEIGHT, br, coll)
            add_box(f"{tag}_brk_{i}h", bx-0.012, y1+0.03, SHELF_HEIGHT-0.03, bx+0.012, y2, SHELF_HEIGHT, br, coll)

def add_stool(tag, cx, cy, coll):
    add_cylinder(f"{tag}_base", cx, cy, 0.0, 0.20, 0.025, mat("trim"), coll=coll)
    add_cylinder(f"{tag}_column", cx, cy, 0.025, 0.024, 0.42, mat("stainless"), coll=coll)
    add_torus(f"{tag}_footring", cx, cy, 0.22, 0.15, 0.012, mat("stainless"), coll=coll)
    add_cylinder(f"{tag}_seat", cx, cy, 0.445, 0.17, 0.05, mat("stool_seat"), coll=coll, bevel=0.01)

def build_sink(coll):
    """Inset stainless sink + mixer tap on west bench b."""
    st = mat("stainless")
    # sink top plate inset into worktop
    add_box("sink_plate", 0.13, 4.45, BENCH_HEIGHT, 0.78, 5.15, BENCH_HEIGHT+0.004, st, coll)
    # basin (open box: floor + 4 thin walls, visible recess)
    bx1, by1, bx2, by2 = 0.22, 4.55, 0.68, 5.05
    depth = 0.16
    add_box("sink_basin_floor", bx1, by1, BENCH_HEIGHT-depth, bx2, by2, BENCH_HEIGHT-depth+0.01, st, coll)
    add_box("sink_basin_w1", bx1, by1, BENCH_HEIGHT-depth, bx1+0.01, by2, BENCH_HEIGHT+0.004, st, coll)
    add_box("sink_basin_w2", bx2-0.01, by1, BENCH_HEIGHT-depth, bx2, by2, BENCH_HEIGHT+0.004, st, coll)
    add_box("sink_basin_w3", bx1, by1, BENCH_HEIGHT-depth, bx2, by1+0.01, BENCH_HEIGHT+0.004, st, coll)
    add_box("sink_basin_w4", bx1, by2-0.01, BENCH_HEIGHT-depth, bx2, by2, BENCH_HEIGHT+0.004, st, coll)
    # mixer tap (curved spout via cable curve)
    add_cylinder("sink_tap_base", 0.16, 4.80, BENCH_HEIGHT, 0.022, 0.05, st, coll=coll)
    add_cable_curve("sink_tap_spout",
                    [(0.16, 4.80, BENCH_HEIGHT+0.05),
                     (0.16, 4.80, BENCH_HEIGHT+0.28),
                     (0.30, 4.80, BENCH_HEIGHT+0.30),
                     (0.36, 4.80, BENCH_HEIGHT+0.22)],
                    radius=0.015, material=st, coll=coll)
    # soap dispenser + paper towel dispenser on wall
    add_box("soap_disp", 0.055, 5.20, 1.15, 0.12, 5.30, 1.32, mat("firstaid"), coll, bevel=0.004)
    add_box("towel_disp", 0.055, 4.20, 1.20, 0.14, 4.55, 1.55, mat("stainless"), coll, bevel=0.004)

def build_furniture(coll):
    # West wall cabinet runs (split around eyewash bay)
    cabinet_run("bench_w_a", "y", 0.10, 0.5, 2.5, +1, coll)
    cabinet_run("bench_w_b", "y", 0.10, 4.0, 5.5, +1, coll)
    wall_shelf("shelf_w_a", 0.10, 0.5, 0.10+SHELF_DEPTH, 2.5, coll)
    wall_shelf("shelf_w_b", 0.10, 4.0, 0.10+SHELF_DEPTH, 5.5, coll)

    # South bench
    cabinet_run("bench_s", "x", 0.10, 2.5, 7.0, +1, coll)

    # Island (doors face south)
    cabinet_run("bench_island", "x", 3.70, 3.0, 5.5, -1, coll)

    # Prep east bench
    cabinet_run("bench_p", "y", PREP[2]-0.10, 1.3, 4.7, -1, coll)
    wall_shelf("shelf_p", PREP[2]-0.10-SHELF_DEPTH, 1.3, PREP[2]-0.10, 4.7, coll)

    # Stools
    add_stool("stool_1", 4.0, 2.45, coll)
    add_stool("stool_2", 5.0, 2.45, coll)
    add_stool("stool_3", 10.8, 3.6, coll)

    # Sink on west bench b
    build_sink(coll)

    # Coat strip + hooks (prep south wall)
    add_box("coat_strip", PREP[0]+0.4, PREP[1]+WALL_THICK/2, 1.62,
            PREP[0]+2.4, PREP[1]+WALL_THICK/2+0.04, 1.70, mat("trim"), coll, bevel=0.003)
    for i, hx in enumerate([0.7, 1.2, 1.7, 2.2]):
        add_box(f"coat_hook_{i}",
                PREP[0]+hx-0.018, PREP[1]+WALL_THICK/2+0.04, 1.54,
                PREP[0]+hx+0.018, PREP[1]+WALL_THICK/2+0.09, 1.66, mat("stainless"), coll, bevel=0.003)

    # Lockers (prep south wall, east of coats)
    lk = mat("locker")
    lx1, lx2 = 10.55, 11.15
    add_box("locker_body", lx1, PREP[1]+0.05, 0.0, lx2, PREP[1]+0.50, 1.80, lk, coll, bevel=0.005)
    for i in range(2):
        dx1 = lx1 + 0.02 + i*0.30
        add_box(f"locker_door_{i}", dx1, PREP[1]+0.035, 0.03, dx1+0.26, PREP[1]+0.05, 1.77,
                mat("locker"), coll, bevel=0.004)
        # louvre vents
        for v in range(3):
            add_box(f"locker_vent_{i}_{v}", dx1+0.05, PREP[1]+0.030, 1.45+v*0.08,
                    dx1+0.21, PREP[1]+0.038, 1.475+v*0.08, mat("skirting"), coll)
        add_box(f"locker_handle_{i}", dx1+0.20, PREP[1]+0.018, 0.95, dx1+0.235, PREP[1]+0.036, 1.05,
                mat("stainless"), coll)

    # Wall trunking with sockets above benches (split around the eyewash bay)
    tr = mat("trim")
    add_box("trunk_w_a", 0.05, 0.5, 1.10, 0.10, 2.5, 1.22, tr, coll)
    add_box("trunk_w_b", 0.05, 4.0, 1.10, 0.10, 5.5, 1.22, tr, coll)
    for i, ty in enumerate([1.0, 1.8, 4.3, 5.1]):
        add_box(f"socket_w_{i}", 0.10, ty-0.06, 1.12, 0.115, ty+0.06, 1.20, mat("label_white"), coll)
    add_box("trunk_s", 2.5, 0.05, 1.10, 7.0, 0.10, 1.22, tr, coll)
    for i, tx in enumerate([3.0, 4.2, 5.4, 6.6]):
        add_box(f"socket_s_{i}", tx-0.06, 0.10, 1.12, tx+0.06, 0.115, 1.20, mat("label_white"), coll)

# ============================================================================
# PROPS
# ============================================================================

def build_glassware(coll):
    gl = mat("glass_clear")
    # Beakers on island
    add_cylinder("ctx_beaker_1", 4.85, 3.35, BENCH_HEIGHT, 0.040, 0.095, gl, coll=coll)
    add_cylinder("ctx_beaker_1_liquid", 4.85, 3.35, BENCH_HEIGHT+0.005, 0.036, 0.04, mat("liquid_blue"), coll=coll)
    add_cylinder("ctx_beaker_2", 5.05, 3.25, BENCH_HEIGHT, 0.033, 0.080, gl, coll=coll)
    # Conical flask
    add_cone("ctx_flask", 4.62, 3.42, BENCH_HEIGHT, 0.055, 0.014, 0.115, gl, coll=coll)
    add_cone("ctx_flask_liquid", 4.62, 3.42, BENCH_HEIGHT+0.004, 0.048, 0.030, 0.045, mat("liquid_amber"), coll=coll)
    # Test tube rack on south bench
    add_box("ctx_tube_rack", 3.0, 0.35, BENCH_HEIGHT, 3.3, 0.50, BENCH_HEIGHT+0.025, mat("cabinet_door"), coll, bevel=0.003)
    for i in range(5):
        add_cylinder(f"ctx_tube_{i}", 3.05+i*0.05, 0.425, BENCH_HEIGHT+0.02, 0.009, 0.085, gl, segments=10, coll=coll)

def build_shelf_bottles(coll):
    """Rows of reagent bottles on the wall shelves."""
    import random
    rnd = random.Random(7)
    cols = ["h_bottle", "liquid_amber", "liquid_blue", "bench_body", "sign_green"]
    def row(tag, axis, fixed, lo, hi, n):
        for i in range(n):
            t = lo + (hi-lo) * (i + 0.5) / n
            r = 0.030 + rnd.random()*0.014
            h = 0.13 + rnd.random()*0.09
            cm = mat(cols[rnd.randrange(len(cols))])
            if axis == "y":
                add_cylinder(f"{tag}_{i}", fixed, t, SHELF_HEIGHT+0.028, r, h, cm, segments=12, coll=coll)
                add_cylinder(f"{tag}_{i}_cap", fixed, t, SHELF_HEIGHT+0.028+h, r*0.55, 0.02, mat("label_dark"), segments=10, coll=coll)
            else:
                add_cylinder(f"{tag}_{i}", t, fixed, SHELF_HEIGHT+0.028, r, h, cm, segments=12, coll=coll)
                add_cylinder(f"{tag}_{i}_cap", t, fixed, SHELF_HEIGHT+0.028+h, r*0.55, 0.02, mat("label_dark"), segments=10, coll=coll)
    row("ctx_shelfbtl_wa", "y", 0.26, 0.65, 2.35, 7)
    row("ctx_shelfbtl_wb", "y", 0.26, 4.15, 5.35, 5)
    row("ctx_shelfbtl_p",  "y", PREP[2]-0.26, 1.45, 4.55, 9)

def build_safety_props(coll):
    # --- Fire extinguisher beside entrance ---
    ex, ey = 2.35, 0.22
    add_box("ext_bracket", ex-0.03, 0.05, 0.95, ex+0.03, 0.10, 1.05, mat("trim"), coll)
    add_cylinder("ctx_extinguisher", ex, ey, 0.30, 0.085, 0.55, mat("ext_red"), coll=coll, bevel=0.01)
    add_cylinder("ctx_extinguisher_top", ex, ey, 0.85, 0.025, 0.07, mat("label_dark"), segments=12, coll=coll)
    add_box("ctx_extinguisher_handle", ex-0.06, ey-0.015, 0.90, ex+0.06, ey+0.015, 0.935, mat("label_dark"), coll)
    add_box("ctx_extinguisher_label", ex-0.05, ey-0.0865, 0.45, ex+0.05, ey-0.082, 0.62, mat("label_white"), coll)
    add_text("ctx_extinguisher_text", "FIRE", ex, ey-0.092, 0.54, facing="-y", size=0.032,
             material=mat("label_red"), coll=coll)

    # --- First aid cabinet (west wall, between bench a and eyewash) ---
    add_box("ctx_firstaid_box", 0.055, 2.62, 1.30, 0.16, 2.98, 1.72, mat("firstaid"), coll, bevel=0.005)
    add_box("ctx_firstaid_cross_v", 0.16, 2.755, 1.42, 0.168, 2.845, 1.60, mat("sign_green"), coll)
    add_box("ctx_firstaid_cross_h", 0.16, 2.715, 1.475, 0.168, 2.885, 1.545, mat("sign_green"), coll)
    add_text("ctx_firstaid_text", "FIRST AID", 0.168, 2.80, 1.36, facing="+x", size=0.035,
             material=mat("sign_green"), coll=coll)

    # --- FIRE EXIT sign above entrance (inside face) ---
    add_box("sign_fireexit_panel", 1.18, 0.055, 2.18, 1.82, 0.075, 2.36, mat("sign_green"), coll)
    add_text("sign_fireexit_text", "FIRE EXIT", 1.5, 0.080, 2.27, facing="+y", size=0.075,
             material=mat("label_white"), coll=coll)

    # --- Posters ---
    def poster(tag, kind, axis, fixed, c1, c2, z1, z2, facing, header):
        body = mat("poster_body")
        if axis == "y":  # on a wall running along Y (west/east walls)
            add_box(f"{tag}_body", fixed, c1, z1, fixed + (0.008 if facing == "+x" else -0.008), c2, z2, body, coll)
            hz1 = z2 - 0.12
            off = 0.010 if facing == "+x" else -0.010
            add_box(f"{tag}_band", fixed, c1, hz1, fixed + off, c2, z2, mat(kind), coll)
            add_text(f"{tag}_title", header, fixed + off*1.4, (c1+c2)/2, (hz1+z2)/2, facing=facing,
                     size=0.045, material=mat("label_white"), coll=coll)
            for i in range(4):
                lz = z1 + 0.08 + i*0.09
                add_box(f"{tag}_line_{i}", fixed, c1+0.06, lz, fixed + off, c2-0.06, lz+0.025,
                        mat("poster_text"), coll)
        else:  # wall running along X (south/north walls)
            add_box(f"{tag}_body", c1, fixed, z1, c2, fixed + (0.008 if facing == "+y" else -0.008), z2, body, coll)
            hz1 = z2 - 0.12
            off = 0.010 if facing == "+y" else -0.010
            add_box(f"{tag}_band", c1, fixed, hz1, c2, fixed + off, z2, mat(kind), coll)
            add_text(f"{tag}_title", header, (c1+c2)/2, fixed + off*1.4, (hz1+z2)/2, facing=facing,
                     size=0.045, material=mat("label_white"), coll=coll)
            for i in range(4):
                lz = z1 + 0.08 + i*0.09
                add_box(f"{tag}_line_{i}", c1+0.06, fixed, lz, c2-0.06, fixed + off, lz+0.025,
                        mat("poster_text"), coll)

    # South wall of main lab (above the bench trunking)
    poster("poster_coshh", "poster_blue", "x", 0.055, 4.4, 5.1, 1.35, 1.95, "+y", "COSHH")
    poster("poster_fire", "poster_red", "x", 0.055, 2.6, 3.3, 1.35, 1.95, "+y", "FIRE ACTION")
    # Shared wall, main lab side
    poster("poster_safety", "poster_blue", "y", MAIN[2]-0.055, 3.4, 4.1, 1.35, 1.95, "-x", "SAFETY")
    # Prep north wall, beside the flammables cabinet (south wall is busy with coats/lockers)
    poster("poster_prep", "poster_blue", "x", PREP[3]-0.055, 10.5, 11.2, 1.35, 1.95, "-y", "PPE ZONES")

    # --- Wall clock (north wall, west of window) ---
    add_cylinder("ctx_clock", 1.0, MAIN[3]-0.055, 2.25, 0.16, 0.03, mat("label_white"), coll=coll)
    # rotate to face -y (into room): cylinder axis is Z; rotate 90° about X
    obj = bpy.data.objects["ctx_clock"]
    obj.rotation_euler = (math.pi/2, 0, 0)
    add_box("ctx_clock_hand_m", 0.995, MAIN[3]-0.085, 2.25, 1.005, MAIN[3]-0.082, 2.37, mat("label_dark"), coll)
    add_box("ctx_clock_hand_h", 1.0, MAIN[3]-0.085, 2.245, 1.09, MAIN[3]-0.082, 2.255, mat("label_dark"), coll)

    # --- Flammables cabinet (prep north wall) ---
    fy2 = PREP[3] - 0.05
    fy1 = fy2 - 0.62
    add_box("ctx_flam_body", 9.0, fy1, 0.0, 10.1, fy2, 1.25, mat("flam_yellow"), coll, bevel=0.006)
    add_box("ctx_flam_door_l", 9.03, fy1-0.015, 0.04, 9.53, fy1, 1.21, mat("flam_yellow"), coll, bevel=0.004)
    add_box("ctx_flam_door_r", 9.57, fy1-0.015, 0.04, 10.07, fy1, 1.21, mat("flam_yellow"), coll, bevel=0.004)
    add_box("ctx_flam_handle_l", 9.46, fy1-0.035, 0.60, 9.50, fy1-0.015, 0.72, mat("label_dark"), coll)
    add_box("ctx_flam_handle_r", 9.60, fy1-0.035, 0.60, 9.64, fy1-0.015, 0.72, mat("label_dark"), coll)
    add_box("ctx_flam_stripe", 9.03, fy1-0.018, 0.92, 10.07, fy1-0.012, 1.04, mat("label_dark"), coll)
    add_text("ctx_flam_text", "FLAMMABLE", 9.55, fy1-0.025, 0.98, facing="-y", size=0.065,
             material=mat("flam_yellow"), coll=coll)

    # --- Smoke detectors ---
    add_cylinder("ctx_smoke_main", 4.0, 3.0, CEIL_DROP-0.030, 0.06, 0.03, mat("label_white"), coll=coll)
    add_cylinder("ctx_smoke_prep", 10.0, 3.0, CEIL_DROP-0.030, 0.06, 0.03, mat("label_white"), coll=coll)

    # --- Light switches by doors ---
    add_box("ctx_switch_main", 2.15, 0.052, 1.15, 2.25, 0.065, 1.27, mat("label_white"), coll, bevel=0.002)
    add_box("ctx_switch_prep", 8.06, 3.10, 1.15, 8.075, 3.20, 1.27, mat("label_white"), coll, bevel=0.002)

    # --- Anti-fatigue mat in front of fume hood ---
    add_box("ctx_fatigue_mat", 6.1, 4.15, 0.0, 7.7, 4.95, 0.018, mat("mat_dark"), coll, bevel=0.006)

    # --- Hazard floor tape around the gas cylinder corner ---
    tz = 0.004
    x1, y1, x2, y2 = 7.05, 0.15, 7.95, 1.65
    w = 0.05
    for i, (sx1, sy1, sx2, sy2) in enumerate([
        (x1, y1, x2, y1+w), (x1, y2-w, x2, y2), (x1, y1, x1+w, y2), (x2-w, y1, x2, y2)]):
        add_box(f"ctx_haztape_{i}", sx1, sy1, 0.0, sx2, sy2, tz, mat("tape_yellow"), coll)
    # black diagonal dashes inside the yellow border (suggestion of chevrons)
    for i in range(6):
        dx = x1 + 0.12 + i * 0.13
        add_box(f"ctx_haztape_dash_{i}", dx, y1+0.012, tz, dx+0.05, y1+0.038, tz+0.002, mat("tape_black"), coll)

def build_fume_hood_extras(coll):
    """Detail added around the existing hazard fume hood (names stay HAZARD_01_*)."""
    # Extract duct from canopy to ceiling
    add_cylinder("fh_duct", 6.9, 5.42, 2.45, 0.14, CEIL_DROP-2.45+0.02, mat("trim"), coll=coll)
    # Control panel with buttons on right fascia
    add_box("fh_panel", 7.55, 4.96, 0.40, 7.76, 4.985, 0.62, mat("label_dark"), coll, bevel=0.003)
    for i in range(3):
        add_box(f"fh_btn_{i}", 7.58+i*0.06, 4.95, 0.52, 7.62+i*0.06, 4.965, 0.56,
                mat(["sign_green", "h_bottle", "ext_red"][i]), coll)

# ============================================================================
# HAZARDS  (mesh names are API for web/main.js — DO NOT RENAME)
# ============================================================================

def build_hazard_01_fume_hood(coll):
    x1, x2 = 6.0, 7.8
    y_back = MAIN[3] - WALL_THICK - 0.05
    y_front = y_back - 0.85
    body = mat("h_fume"); glass = mat("window")
    trim_m = mat("trim"); inner = mat("worktop")

    add_box("HAZARD_01_fume_hood_side_l", x1, y_front, 0.0, x1+0.05, y_back, 2.30, body, coll, bevel=0.005)
    add_box("HAZARD_01_fume_hood_side_r", x2-0.05, y_front, 0.0, x2, y_back, 2.30, body, coll, bevel=0.005)
    add_box("HAZARD_01_fume_hood_back",   x1+0.05, y_back-0.05, 0.0, x2-0.05, y_back, 2.30, body, coll)
    add_box("HAZARD_01_fume_hood_top",    x1+0.05, y_front, 2.20, x2-0.05, y_back-0.05, 2.30, body, coll, bevel=0.005)
    add_box("HAZARD_01_fume_hood_lower",  x1+0.05, y_front, 0.0,  x2-0.05, y_back-0.05, 0.85, body, coll, bevel=0.005)
    add_box("HAZARD_01_fume_hood_top_band", x1+0.05, y_front, 2.05, x2-0.05, y_front+0.04, 2.20, body, coll)
    add_box("HAZARD_01_fume_hood_worktop", x1+0.05, y_front+0.02, 0.85, x2-0.05, y_back-0.05, 0.88, inner, coll)
    add_box("HAZARD_01_fume_hood_baffle",  x1+0.05, y_back-0.06, 0.88, x2-0.05, y_back-0.05, 2.20, inner, coll)
    # Sash glass RAISED (the hazard)
    add_box("HAZARD_01_fume_hood_sash", x1+0.06, y_front+0.005, 1.92, x2-0.06, y_front+0.025, 2.05, glass, coll)
    add_box("HAZARD_01_fume_hood_sash_rail", x1+0.05, y_front, 1.87, x2-0.05, y_front+0.045, 1.92, trim_m, coll, bevel=0.004)
    add_box("HAZARD_01_fume_hood_fascia", x1+0.05, y_front, 0.65, x2-0.05, y_front+0.03, 0.85, trim_m, coll)
    add_box("HAZARD_01_fume_hood_canopy", x1-0.02, y_front-0.02, 2.30, x2+0.02, y_back+0.02, 2.45, trim_m, coll, bevel=0.006)
    # Max-height marker + sticker (pedagogical hint, part of the hazard prefix)
    add_box("HAZARD_01_sash_marker", x1+0.05, y_front-0.005, 1.30, x2-0.05, y_front+0.002, 1.315, mat("label_red"), coll)
    add_text("HAZARD_01_sash_sticker", "MAX WORKING HEIGHT", (x1+x2)/2, y_front-0.010, 1.36,
             facing="-y", size=0.038, material=mat("label_red"), coll=coll)

def build_hazard_02_eyewash(coll):
    cy = 3.25
    g = mat("h_eyewash"); t = mat("stainless"); obs = mat("obstruct"); dk = mat("worktop")

    add_box("HAZARD_02_eyewash_backplate", 0.0, cy-0.50, 0.95, WALL_THICK/2+0.02, cy+0.50, 1.75, g, coll, bevel=0.005)
    add_text("HAZARD_02_eyewash_label", "EYEWASH", WALL_THICK/2+0.025, cy, 1.55, facing="+x", size=0.12,
             material=mat("label_white"), coll=coll)
    add_text("HAZARD_02_eyewash_label_sub", "STATION", WALL_THICK/2+0.025, cy, 1.38, facing="+x", size=0.085,
             material=mat("label_white"), coll=coll)
    add_box("HAZARD_02_eyewash_cross_v", 0.0, cy-0.04, 1.07, WALL_THICK/2+0.030, cy+0.04, 1.27, mat("label_white"), coll)
    add_box("HAZARD_02_eyewash_cross_h", 0.0, cy-0.10, 1.13, WALL_THICK/2+0.030, cy+0.10, 1.21, mat("label_white"), coll)
    add_box("HAZARD_02_eyewash_bowl", WALL_THICK/2, cy-0.30, 1.05, WALL_THICK/2+0.32, cy+0.30, 1.12, t, coll, bevel=0.008)
    add_box("HAZARD_02_eyewash_bowl_inner", WALL_THICK/2+0.04, cy-0.26, 1.10, WALL_THICK/2+0.32, cy+0.26, 1.14, dk, coll)
    add_cylinder("HAZARD_02_eyewash_spout_l", WALL_THICK/2+0.10, cy-0.10, 1.14, 0.022, 0.10, t, segments=10, coll=coll)
    add_cylinder("HAZARD_02_eyewash_spout_r", WALL_THICK/2+0.10, cy+0.10, 1.14, 0.022, 0.10, t, segments=10, coll=coll)
    add_box("HAZARD_02_eyewash_paddle", WALL_THICK/2, cy+0.32, 1.10, WALL_THICK/2+0.22, cy+0.40, 1.20, mat("h_bottle"), coll, bevel=0.006)
    add_box("HAZARD_02_eyewash_pipe", WALL_THICK/2, cy-0.03, 1.40, WALL_THICK/2+0.06, cy+0.03, 1.85, t, coll)
    # Obstruction crates
    add_box("HAZARD_02_eyewash_obstruction_a", WALL_THICK/2+0.32, cy-0.40, 0.0, WALL_THICK/2+1.02, cy+0.40, 0.50, obs, coll, bevel=0.008)
    add_box("HAZARD_02_eyewash_obstruction_b", WALL_THICK/2+0.42, cy-0.30, 0.50, WALL_THICK/2+0.92, cy+0.30, 0.95, obs, coll, bevel=0.008)

def build_hazard_03_unlabelled_bottle(coll):
    base = BENCH_HEIGHT
    def make_bottle(prefix, cx, cy, body_mat, panel_mat, text_str=None, text_col=None,
                    height=0.20, radius=0.05):
        add_cylinder(prefix,         cx, cy, base,            radius,      height, body_mat, segments=16, coll=coll)
        add_cylinder(prefix+"_neck", cx, cy, base+height,     radius*0.5,  0.04,   body_mat, segments=12, coll=coll)
        add_cylinder(prefix+"_cap",  cx, cy, base+height+0.04, radius*0.6, 0.025,  mat("label_dark"), segments=12, coll=coll)
        # Wrap-around band label (full 360° sleeve, slightly proud of the glass)
        band_r = radius + 0.004
        add_cylinder(prefix+"_label", cx, cy, base+0.05, band_r, height-0.07,
                     panel_mat, segments=20, coll=coll)
        if text_str is not None:
            # Curved text hugging the band on the south face
            text_r = band_r + 0.002
            add_text(prefix+"_text", text_str, cx, cy-text_r, base + (height/2) + 0.02,
                     facing="-y", size=0.020, extrude=0.002, material=text_col, coll=coll,
                     wrap_radius=text_r)
    make_bottle("HAZARD_03_unlabelled_bottle", 3.40, 3.20, mat("h_bottle"), mat("label_white"))
    make_bottle("ctx_labelled_bottle",  3.70, 3.20, mat("bench_body"), mat("label_white"),
                text_str="ETHANOL", text_col=mat("label_dark"))
    make_bottle("ctx_labelled_bottle2", 3.10, 3.20, mat("bench_body"), mat("label_white"),
                text_str="ACETONE", text_col=mat("label_dark"), height=0.18, radius=0.045)

def build_hazard_04_extension_lead(coll):
    cable = mat("h_cable"); plug = mat("label_dark")
    psx, psy = 3.55, 0.92
    add_box("HAZARD_04_power_strip", psx, psy, 0.0, psx+0.50, psy+0.14, 0.05, cable, coll, bevel=0.005)
    for i in range(3):
        sx = psx + 0.10 + i * 0.13
        add_box(f"HAZARD_04_power_strip_socket_{i}", sx-0.025, psy+0.04, 0.05, sx+0.025, psy+0.10, 0.052,
                mat("label_dark"), coll)
    cable_path = [
        (3.85, 1.07, 0.025), (4.05, 1.40, 0.020), (3.78, 1.80, 0.020),
        (4.10, 2.20, 0.020), (3.80, 2.55, 0.020), (4.00, 2.85, 0.020),
        (3.95, 3.00, 0.045), (3.95, 3.06, 0.075),
    ]
    add_cable_curve("HAZARD_04_extension_lead", cable_path, radius=0.012, material=cable, coll=coll)
    add_box("HAZARD_04_extension_lead_plug", 3.88, 3.02, 0.045, 4.00, 3.12, 0.10, plug, coll, bevel=0.004)
    # Context: balance on the island
    add_box("ctx_lab_equipment", 3.85, 3.15, BENCH_HEIGHT, 4.25, 3.55, BENCH_HEIGHT+0.22, mat("trim"), coll, bevel=0.006)
    add_box("ctx_lab_equipment_screen", 3.92, 3.135, BENCH_HEIGHT+0.07, 4.18, 3.155, BENCH_HEIGHT+0.18, mat("label_dark"), coll)
    add_text("ctx_lab_equipment_label", "BALANCE", 4.05, 3.130, BENCH_HEIGHT+0.20, facing="-y", size=0.022,
             material=mat("label_white"), coll=coll)
    add_cylinder("ctx_lab_equipment_pan", 4.05, 3.35, BENCH_HEIGHT+0.22, 0.07, 0.012, mat("stainless"), coll=coll)

def build_hazard_05_gas_cylinder(coll):
    cx, cy = 7.5, 1.10
    body = mat("h_cylinder"); valve = mat("stainless"); shoulder = mat("sign_green")

    add_cylinder("HAZARD_05_gas_cylinder",           cx, cy, 0.0,  0.130, 1.40, body, segments=24, coll=coll)
    add_cylinder("HAZARD_05_gas_cylinder_shoulder",  cx, cy, 1.40, 0.110, 0.10, shoulder, segments=24, coll=coll)
    add_cylinder("HAZARD_05_gas_cylinder_collar",    cx, cy, 1.50, 0.105, 0.05, valve, segments=24, coll=coll)
    add_cylinder("HAZARD_05_gas_cylinder_valve",     cx, cy, 1.55, 0.025, 0.10, valve, segments=12, coll=coll)
    add_cylinder("HAZARD_05_gas_cylinder_handwheel", cx, cy, 1.65, 0.050, 0.018, valve, segments=16, coll=coll)
    add_cylinder("HAZARD_05_gas_cylinder_base",      cx, cy, 0.0,  0.140, 0.04, valve, segments=24, coll=coll)
    # Empty bracket + dangling chain on east wall
    bx_in = MAIN[2] - WALL_THICK/2
    add_box("HAZARD_05_bracket_plate", bx_in-0.05, cy-0.10, 1.00, bx_in, cy+0.10, 1.06, valve, coll, bevel=0.004)
    for i in range(5):
        z = 1.00 - i * 0.06
        add_box(f"HAZARD_05_loose_chain_{i}", bx_in-0.06, cy+0.085, z-0.018, bx_in-0.04, cy+0.105, z+0.012, valve, coll)

    # Context: a SECOND cylinder correctly chained to the wall (teaching contrast)
    sx, sy = 7.55, 0.50
    add_cylinder("ctx_cylinder_secured",          sx, sy, 0.0,  0.130, 1.40, body, segments=24, coll=coll)
    add_cylinder("ctx_cylinder_secured_shoulder", sx, sy, 1.40, 0.110, 0.10, mat("liquid_blue"), segments=24, coll=coll)
    add_cylinder("ctx_cylinder_secured_valve",    sx, sy, 1.50, 0.025, 0.12, valve, segments=12, coll=coll)
    add_box("ctx_cylinder_secured_bracket", MAIN[2]-WALL_THICK/2-0.05, sy-0.10, 1.00, MAIN[2]-WALL_THICK/2, sy+0.10, 1.06, valve, coll, bevel=0.004)
    add_torus("ctx_cylinder_secured_chain", sx, sy, 1.05, 0.155, 0.013, valve, coll=coll)
    add_box("ctx_cylinder_secured_link", sx+0.14, sy-0.02, 1.02, MAIN[2]-WALL_THICK/2-0.02, sy+0.02, 1.06, valve, coll)

def build_hazard_06_sharps_in_bin(coll):
    # Bins sit side by side against the north wall, under the window bank
    # (prep-room corner was too crowded with coats/lockers/doorway)
    bin_cx, bin_cy = 4.4, 5.55
    bin_body = mat("h_bin"); pedal = mat("trim")

    add_cylinder("HAZARD_06_general_bin", bin_cx, bin_cy, 0.0, 0.22, 0.55, bin_body, segments=18, coll=coll)
    # Round lid sitting ajar (half off) so the sharps inside are exposed
    lid = add_cylinder("HAZARD_06_general_bin_lid", bin_cx+0.14, bin_cy, 0.55, 0.225, 0.025, pedal, segments=18, coll=coll)
    lid.rotation_euler = (0, math.radians(-8), 0)
    # Pedal + labels face SOUTH (-y) into the room
    add_box("HAZARD_06_general_bin_pedal", bin_cx-0.10, bin_cy-0.32, 0.0, bin_cx+0.10, bin_cy-0.22, 0.04, pedal, coll, bevel=0.004)
    add_box("HAZARD_06_general_bin_label_panel",
            bin_cx-0.16, bin_cy-0.225, 0.20, bin_cx+0.16, bin_cy-0.218, 0.42, mat("label_white"), coll)
    add_text("HAZARD_06_general_bin_label", "GENERAL", bin_cx, bin_cy-0.232, 0.34, facing="-y", size=0.040,
             material=mat("label_dark"), coll=coll)
    add_text("HAZARD_06_general_bin_label_2", "WASTE", bin_cx, bin_cy-0.232, 0.27, facing="-y", size=0.040,
             material=mat("label_dark"), coll=coll)
    # Sharps poking out
    sx1, sy1 = bin_cx-0.05, bin_cy-0.03
    add_cylinder("HAZARD_06_sharps_barrel_1", sx1, sy1, 0.50, 0.015, 0.10, mat("h_ppe"), segments=10, coll=coll)
    add_cylinder("HAZARD_06_sharps_needle_1", sx1, sy1, 0.60, 0.003, 0.08, mat("stainless"), segments=8, coll=coll)
    sx2, sy2 = bin_cx+0.07, bin_cy-0.10
    add_cylinder("HAZARD_06_sharps_barrel_2", sx2, sy2, 0.52, 0.015, 0.08, mat("h_eyewash"), segments=10, coll=coll)
    sx3, sy3 = bin_cx-0.02, bin_cy+0.10
    add_cylinder("HAZARD_06_sharps_barrel_3", sx3, sy3, 0.51, 0.013, 0.09, mat("h_ppe"), segments=10, coll=coll)

    # Correct yellow sharps bin — to the right of the general bin, same wall
    sb_x, sb_y = bin_cx + 0.60, bin_cy
    add_cylinder("ctx_sharps_bin_correct", sb_x, sb_y, 0.0, 0.18, 0.45, mat("h_bottle"), segments=18, coll=coll)
    add_cylinder("ctx_sharps_bin_correct_lid", sb_x, sb_y, 0.45, 0.18, 0.06, mat("trim"), segments=18, coll=coll)
    add_box("ctx_sharps_bin_correct_label_panel",
            sb_x-0.14, sb_y-0.183, 0.18, sb_x+0.14, sb_y-0.176, 0.38, mat("label_red"), coll)
    add_text("ctx_sharps_bin_correct_label", "SHARPS", sb_x, sb_y-0.190, 0.32, facing="-y", size=0.038,
             material=mat("label_white"), coll=coll)
    add_text("ctx_sharps_bin_correct_label_2", "ONLY", sb_x, sb_y-0.190, 0.25, facing="-y", size=0.038,
             material=mat("label_white"), coll=coll)

def build_hazard_07_ppe_failure(coll):
    """Lab coat (long, white, buttoned, on a hanger) sharing hook with a navy
    hooded street jacket (short, bulky, zipped, angled sleeves)."""
    cx = PREP[0] + 1.2
    coat = mat("h_ppe"); street = mat("street_navy")
    trim_m = mat("coat_shadow"); st = mat("stainless")
    yb = PREP[1] + WALL_THICK/2 + 0.06
    yf = PREP[1] + WALL_THICK/2 + 0.16

    # ---- Lab coat (long + white, hangs on a visible hanger) ----
    # Hanger: hook stem + angled shoulder bars
    add_cylinder("HAZARD_07_hanger_stem", cx, (yb+yf)/2, 1.56, 0.006, 0.10, st, segments=8, coll=coll)
    bar_l = add_box("HAZARD_07_hanger_bar_l", cx-0.24, (yb+yf)/2-0.008, 1.49, cx, (yb+yf)/2+0.008, 1.505, st, coll)
    bar_l.rotation_euler = (0, math.radians(-10), 0)
    bar_r = add_box("HAZARD_07_hanger_bar_r", cx, (yb+yf)/2-0.008, 1.49, cx+0.24, (yb+yf)/2+0.008, 1.505, st, coll)
    bar_r.rotation_euler = (0, math.radians(10), 0)

    # Shoulders slope down from the hanger
    sh_l = add_box("HAZARD_07_lab_coat_shoulder_l", cx-0.25, yb, 1.40, cx-0.02, yf, 1.49, coat, coll, bevel=0.012)
    sh_l.rotation_euler = (0, math.radians(-8), 0)
    sh_r = add_box("HAZARD_07_lab_coat_shoulder_r", cx+0.02, yb, 1.40, cx+0.25, yf, 1.49, coat, coll, bevel=0.012)
    sh_r.rotation_euler = (0, math.radians(8), 0)
    # Long body, slight A-line flare toward the hem (knee length)
    add_box("HAZARD_07_lab_coat_torso", cx-0.21, yb, 1.05, cx+0.21, yf, 1.42, coat, coll, bevel=0.012)
    add_box("HAZARD_07_lab_coat_hem",   cx-0.25, yb+0.005, 0.58, cx+0.25, yf-0.005, 1.05, coat, coll, bevel=0.012)
    # Sleeves angled slightly outward, full length (lab coats have long sleeves)
    sl_l = add_box("HAZARD_07_lab_coat_sleeve_l", cx-0.33, yb, 0.92, cx-0.23, yf, 1.40, coat, coll, bevel=0.012)
    sl_l.rotation_euler = (0, math.radians(-9), 0)
    sl_r = add_box("HAZARD_07_lab_coat_sleeve_r", cx+0.23, yb, 0.92, cx+0.33, yf, 1.40, coat, coll, bevel=0.012)
    sl_r.rotation_euler = (0, math.radians(9), 0)
    # Open collar V: two slim lapel strips tilted in the coat's face plane
    lap_l = add_box("HAZARD_07_lab_coat_lapel_l", cx-0.085, yf-0.002, 1.28, cx-0.035, yf+0.006, 1.44, trim_m, coll)
    lap_l.rotation_euler = (0, math.radians(-14), 0)
    lap_r = add_box("HAZARD_07_lab_coat_lapel_r", cx+0.035, yf-0.002, 1.28, cx+0.085, yf+0.006, 1.44, trim_m, coll)
    lap_r.rotation_euler = (0, math.radians(14), 0)
    # Button placket + buttons down the front
    add_box("HAZARD_07_lab_coat_placket", cx-0.010, yf-0.001, 0.70, cx+0.010, yf+0.004, 1.26, trim_m, coll)
    for i, bz in enumerate([0.80, 0.95, 1.10, 1.22]):
        add_cylinder(f"HAZARD_07_lab_coat_button_{i}", cx, yf+0.006, bz, 0.014, 0.008,
                     mat("label_dark"), segments=10, coll=coll, smooth=False)
        bpy.data.objects[f"HAZARD_07_lab_coat_button_{i}"].rotation_euler = (math.pi/2, 0, 0)
    # Chest pocket with pen
    add_box("HAZARD_07_lab_coat_pocket", cx-0.16, yf-0.001, 1.16, cx-0.06, yf+0.005, 1.26, trim_m, coll)
    add_box("HAZARD_07_lab_coat_pen", cx-0.13, yf+0.005, 1.20, cx-0.115, yf+0.012, 1.28, mat("poster_blue"), coll)

    # ---- Street jacket (short + bulky + NAVY + hood) on the SAME hook ----
    sx = cx + 0.16
    syb = yf + 0.005; syf = yf + 0.13   # bulkier depth than the lab coat
    # Hood: rounded chunk above the shoulders
    add_box("HAZARD_07_street_coat_hood", sx-0.17, syb, 1.42, sx+0.17, syf+0.03, 1.62, street, coll, bevel=0.03)
    add_box("HAZARD_07_street_coat_hood_opening", sx-0.09, syf+0.005, 1.43, sx+0.09, syf+0.034, 1.47, mat("label_dark"), coll)
    # Shoulders/yoke
    add_box("HAZARD_07_street_coat_yoke", sx-0.27, syb, 1.30, sx+0.27, syf, 1.43, street, coll, bevel=0.02)
    # Puffy torso — wider than it is deep, with horizontal quilt bands
    add_box("HAZARD_07_street_coat_torso", sx-0.25, syb, 0.88, sx+0.25, syf, 1.30, street, coll, bevel=0.02)
    for i, qz in enumerate([1.00, 1.12, 1.24]):
        add_box(f"HAZARD_07_street_coat_quilt_{i}", sx-0.25, syf-0.004, qz-0.006, sx+0.25, syf+0.004, qz+0.006,
                mat("label_dark"), coll)
    # Elastic hem band (jackets end at the waist — much shorter than the lab coat)
    add_box("HAZARD_07_street_coat_hem", sx-0.24, syb+0.005, 0.80, sx+0.24, syf-0.005, 0.88, mat("label_dark"), coll, bevel=0.01)
    # Bulky sleeves angled outward
    ssl = add_box("HAZARD_07_street_coat_sleeve_l", sx-0.37, syb, 0.84, sx-0.25, syf, 1.34, street, coll, bevel=0.02)
    ssl.rotation_euler = (0, math.radians(-13), 0)
    ssr = add_box("HAZARD_07_street_coat_sleeve_r", sx+0.25, syb, 0.84, sx+0.37, syf, 1.34, street, coll, bevel=0.02)
    ssr.rotation_euler = (0, math.radians(13), 0)
    # Silver zip down the front
    add_box("HAZARD_07_street_coat_zip", sx-0.008, syf-0.001, 0.88, sx+0.008, syf+0.008, 1.40, st, coll)

    # Hi-vis on separate hook (correct)
    hx = PREP[0] + 2.2
    yf_h = yf - 0.05; yb_h = yb
    add_box("ctx_hivis_yoke",  hx-0.24, yb_h, 1.34, hx+0.24, yf_h, 1.46, mat("hivis"), coll, bevel=0.01)
    add_box("ctx_hivis_torso", hx-0.20, yb_h, 0.90, hx+0.20, yf_h, 1.34, mat("hivis"), coll, bevel=0.01)
    add_box("ctx_hivis_stripe_a", hx-0.205, yf_h-0.001, 1.05, hx+0.205, yf_h+0.005, 1.10, mat("label_white"), coll)
    add_box("ctx_hivis_stripe_b", hx-0.205, yf_h-0.001, 1.20, hx+0.205, yf_h+0.005, 1.25, mat("label_white"), coll)
    add_box("ctx_hivis_stripe_c", hx-0.235, yf_h-0.001, 1.36, hx+0.235, yf_h+0.005, 1.39, mat("label_white"), coll)

# ============================================================================
# SIGNAGE / META
# ============================================================================

def build_signage(coll):
    door_y = (INTERNAL_DOOR[0] + INTERNAL_DOOR[1]) / 2
    sign_z = (DOOR_HEIGHT + CEIL_DROP) / 2 + 0.02
    add_box("sign_to_prep_panel", MAIN[2]-WALL_THICK/2-0.012, door_y-0.40, sign_z-0.10,
            MAIN[2]-WALL_THICK/2-0.002, door_y+0.40, sign_z+0.10, mat("label_white"), coll)
    add_text("sign_to_prep", "PREP ROOM", MAIN[2]-WALL_THICK/2-0.016, door_y, sign_z,
             facing="-x", size=0.085, material=mat("label_dark"), coll=coll)
    add_box("sign_to_main_panel", MAIN[2]+WALL_THICK/2+0.002, door_y-0.40, sign_z-0.10,
            MAIN[2]+WALL_THICK/2+0.012, door_y+0.40, sign_z+0.10, mat("label_white"), coll)
    add_text("sign_to_main", "MAIN LAB", MAIN[2]+WALL_THICK/2+0.016, door_y, sign_z,
             facing="+x", size=0.085, material=mat("label_dark"), coll=coll)

def add_spawn(coll):
    bpy.ops.object.empty_add(type="ARROWS", radius=0.5, location=(1.5, 1.0, 1.7))
    obj = bpy.context.active_object
    obj.name = "SPAWN_POINT"
    obj.rotation_euler = (0, 0, math.pi/2)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)

# ============================================================================
# EXPORT / MAIN
# ============================================================================

def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        use_selection=False,
        export_extras=True,
    )
    print(f"[build_lab] Exported -> {path}")

def main():
    clear_scene()
    c_shell = get_or_create_collection("shell")
    c_furn = get_or_create_collection("furniture")
    c_props = get_or_create_collection("props")
    c_haz = get_or_create_collection("hazards")
    c_meta = get_or_create_collection("meta")

    build_floors(c_shell)
    build_ceilings(c_shell)
    build_troffers(c_shell)
    build_walls(c_shell)
    build_skirting(c_shell)
    build_entrance_door(c_shell)
    build_internal_doorway(c_shell)
    build_windows(c_shell)
    build_exterior(c_shell)

    build_furniture(c_furn)

    build_glassware(c_props)
    build_shelf_bottles(c_props)
    build_safety_props(c_props)
    build_fume_hood_extras(c_props)

    build_hazard_01_fume_hood(c_haz)
    build_hazard_02_eyewash(c_haz)
    build_hazard_03_unlabelled_bottle(c_haz)
    build_hazard_04_extension_lead(c_haz)
    build_hazard_05_gas_cylinder(c_haz)
    build_hazard_06_sharps_in_bin(c_haz)
    build_hazard_07_ppe_failure(c_haz)

    build_signage(c_shell)
    add_spawn(c_meta)

    export_glb(OUTPUT_GLB)
    print("[build_lab] Done.")

if __name__ == "__main__":
    main()
