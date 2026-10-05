# Skaterino: measures a map against skate.'s skater limits and reports what will and will not work.
#
#   blender --background --factory-startup --python skaterino.py -- <map.blend|map.glb> [--scale 1.0] [--out report]
#
# The map must be in metres, Z up (Blender's convention; a .glb is converted on import). Every mesh
# object counts as level geometry; Blender curve objects count as grind rails. Writes <out>.md
# and <out>.json next to the map. Limits come from skate_limits.json beside this script.
import bpy, bmesh, sys, os, json, math, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
path = os.path.abspath(args[0])
scale = float(args[args.index("--scale") + 1]) if "--scale" in args else 1.0
out = args[args.index("--out") + 1] if "--out" in args else os.path.splitext(path)[0] + "_skaterino"
here = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(here, "skate_limits.json")))
g = L["gravity_mps2"]
max_drop = L["wipeout_max_landing_speed_down_mps"] ** 2 / (2 * g)

if path.lower().endswith((".glb", ".gltf")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
elif not bpy.data.filepath or os.path.abspath(bpy.data.filepath) != path:
    bpy.ops.wm.open_mainfile(filepath=path)

meshes = [o for o in bpy.data.objects if o.type == "MESH" and len(o.data.polygons)]
curves = [o for o in bpy.data.objects if o.type == "CURVE"]
bm = bmesh.new()
for o in meshes:
    tmp = bmesh.new()
    tmp.from_mesh(o.data)
    tmp.transform(o.matrix_world)
    me = bpy.data.meshes.new("t")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
if scale != 1.0:
    bmesh.ops.scale(bm, vec=(scale,) * 3, verts=bm.verts)
bm.faces.ensure_lookup_table()
bm.normal_update()
bvh = BVHTree.FromBMesh(bm)
report = {"map": os.path.basename(path), "scale_tested": scale, "faces": len(bm.faces), "verts": len(bm.verts)}
lo = Vector((min(v.co[k] for v in bm.verts) for k in range(3)))
hi = Vector((max(v.co[k] for v in bm.verts) for k in range(3)))
report["size_m"] = [round(v, 1) for v in (hi - lo)]
findings = []


def mode(counter):
    return counter.most_common(1)[0][0] if counter else None


# --- scale clues: stair risers and ledge heights
risers, ledges = collections.Counter(), collections.Counter()
for f in bm.faces:
    if abs(f.normal.z) < 0.2:
        d = max(v.co.z for v in f.verts) - min(v.co.z for v in f.verts)
        if 0.12 <= d <= 0.25:          # stair risers (kerb lips at 0.08-0.11 would skew the mode)
            risers[round(d, 2)] += 1
        elif 0.25 < d <= 0.7:
            ledges[round(d, 2)] += 1
r_mode, l_mode = mode(risers), mode(ledges)
report["stair_riser_mode_m"] = r_mode
report["ledge_height_mode_m"] = l_mode
lo_r, hi_r = L["real_world"]["stair_riser_m"]
if r_mode:
    if lo_r <= r_mode <= hi_r:
        findings.append(("ok", "Scale: stair risers are %.2f m, real-world. Keep scale %.2f." % (r_mode, scale)))
    else:
        sug = round(scale * 0.17 / r_mode, 2)
        findings.append(("warn", "Scale: stair risers are %.2f m (real 0.15-0.19). Try --scale %.2f." % (r_mode, sug)))
else:
    findings.append(("info", "Scale: no stair risers found; judge scale by ledges (%s m) and doors." % l_mode))

# --- drops at the edges of walkable faces
up = [f for f in bm.faces if f.normal.z > 0.9]
drops = collections.Counter()
deadly = []
for f in up:
    c = f.calc_center_median()
    for e in f.edges:
        others = [x for x in e.link_faces if x is not f]
        if others and all(x.normal.z > 0.3 for x in others):
            continue
        mid = (e.verts[0].co + e.verts[1].co) / 2
        d2 = mid - c
        if d2.length < 1e-6:
            continue
        probe = mid + d2.normalized() * 0.3
        hit = bvh.ray_cast(probe + Vector((0, 0, 0.05)), Vector((0, 0, -1)), 60)
        if hit[0] is None:
            continue
        d = mid.z - hit[0].z
        if d > 0.25:
            drops[round(d * 2) / 2] += 1
            if d > max_drop and len(deadly) < 8:
                deadly.append([round(v, 1) for v in mid] + [round(d, 1)])
report["drops_m"] = sorted(drops.items())
n_deadly = sum(n for d, n in drops.items() if d > max_drop)
n_hard = sum(n for d, n in drops.items() if L["comfortable_drop_m"] < d <= max_drop)
report["max_survivable_drop_m"] = round(max_drop, 1)
if n_deadly:
    findings.append(("warn", "Drops: %d edges drop more than %.0f m (skate. bails above %d m/s). First at %s. Fence them, add a ramp, or accept the bail." % (n_deadly, max_drop, L["wipeout_max_landing_speed_down_mps"], deadly[:3])))
if n_hard:
    findings.append(("info", "Drops: %d edges drop %d-%.0f m: survivable but rough." % (n_hard, L["comfortable_drop_m"], max_drop)))

# --- ledges you can or cannot pop onto
ledge_counts = collections.Counter()
for d, n in ledges.items():
    ledge_counts["ollie-able" if d <= L["jump_max_height_m"] else "too tall"] += n
report["ledges"] = dict(ledge_counts)

# --- transitions: banked faces and how faceted they are
banked = [f for f in bm.faces if 0.3 < f.normal.z < 0.95]
banked_set = set(f.index for f in banked)
creases = 0
for e in bm.edges:
    fs = e.link_faces
    if len(fs) == 2 and (fs[0].index in banked_set or fs[1].index in banked_set):
        a = fs[0].normal.angle(fs[1].normal, 0.0)
        if math.radians(8) < a < math.radians(60):
            creases += 1
report["banked_faces"] = len(banked)
report["transition_creases"] = creases
if banked and creases / max(1, len(banked)) > 0.6:
    findings.append(("warn", "Transitions: %d banked faces with %d creases between 8 and 60 degrees. Low-poly ramps: skate. follows every facet and treats creases over %d degrees as grind edges. Subdivide and smooth them." % (len(banked), creases, L["grind_edge_detect_crease_deg"])))
else:
    findings.append(("ok", "Transitions: %d banked faces, %d creases; smooth enough." % (len(banked), creases)))

# --- z-fighting: coplanar faces within 1 cm
zf = 0
for f in bm.faces:
    c = f.calc_center_median()
    n = f.normal
    if n.length < 0.5:
        continue
    hit = bvh.ray_cast(c + n * 0.011, -n, 0.022)
    if hit[0] is not None and hit[2] != f.index and abs(bm.faces[hit[2]].normal.dot(n)) > 0.999:
        zf += 1
report["coplanar_overlaps"] = zf
if zf > 20:
    findings.append(("warn", "Overlays: %d faces sit on another face within 1 cm; they will flicker (z-fight). Delete duplicates, lift decals 1-2 cm or make them Studio decals." % zf))
else:
    findings.append(("ok", "Overlays: %d faces within 1 cm of another; fine." % zf))

# --- rails
lengths, heights = [], []
for o in curves:
    for sp in o.data.splines:
        if sp.bezier_points:
            pts = [o.matrix_world @ p.co * scale for p in sp.bezier_points]
        else:
            pts = [o.matrix_world @ Vector(p.co[:3]) * scale for p in sp.points]
        if len(pts) < 2:
            continue
        lengths.append(sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)))
        for p in pts:
            hit = bvh.ray_cast(p - Vector((0, 0, 0.05)), Vector((0, 0, -1)), 60)
            if hit[0] is not None:
                heights.append(p.z - hit[0].z)
hs = sorted(heights)
if hs:
    report["rail_height_median_m"] = round(hs[len(hs) // 2], 2)
    report["rail_height_p90_m"] = round(hs[int(len(hs) * 0.9)], 2)
    reach = L["jump_max_height_m"] + 0.3
    too_high = sum(1 for h in hs if h > reach)
    findings.append(("info", "Rails: %d curves; median %.2f m above ground; %d%% of rail points are above ollie reach (%.1f m) and need a ramp, stairs or a drop-in." % (len(lengths), hs[len(hs) // 2], 100 * too_high // len(hs), reach)))
else:
    findings.append(("info", "Rails: no curve objects; the game will only find grinds on creases over %d degrees." % L["grind_edge_detect_crease_deg"]))
report["rails"] = {"count": len(curves), "total_length_m": round(sum(lengths), 0)}

# --- rooftops: walkable faces more than the survivable drop above ground level
ground_z = sorted(f.calc_center_median().z for f in up)[len(up) // 10] if up else 0
high = sum(1 for f in up if f.calc_center_median().z - ground_z > max_drop)
report["walkable_faces_above_survivable_drop"] = high
if high:
    findings.append(("info", "%d walkable faces sit more than %.0f m above ground level: rooftops. In THPS you survive the jump down; in skate. you will not. Flag them wipeout or no-collision, or leave them as a dare." % (high, max_drop)))

report["findings"] = findings
with open(out + ".json", "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
lines = ["# Skaterino report: %s" % report["map"], "",
         "Size %.0f x %.0f x %.0f m, %d faces, scale tested %.2f." % (*report["size_m"], report["faces"], scale), "",
         "skate. limits used: ollie %.2f m, bail above %d m/s down (about a %.0f m drop), skater %.2f m, grind edges found on creases of %d degrees or more." % (
             L["jump_max_height_m"], L["wipeout_max_landing_speed_down_mps"], max_drop, L["skater_height_m"], L["grind_edge_detect_crease_deg"]), ""]
for kind, text in findings:
    lines.append("- **%s** %s" % (kind.upper(), text))
lines += ["", "Drops (m: edges): " + ", ".join("%.1f: %d" % (d, n) for d, n in report["drops_m"])]
open(out + ".md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines), flush=True)
print("SKATERINO wrote", out + ".md", flush=True)
