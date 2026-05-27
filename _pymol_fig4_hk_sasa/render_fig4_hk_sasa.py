
from pathlib import Path
import json
import math
import pymol
from pymol.cgo import BEGIN, TRIANGLES, COLOR, VERTEX, END, CYLINDER

pymol.finish_launching(['pymol', '-cq'])
from pymol import cmd

HERE = Path(__file__).resolve().parent
JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

def set_color(name, rgb):
    cmd.set_color(name, [float(x) for x in rgb])

def nearest_point(point, candidates):
    best = None
    best_d2 = None
    px, py, pz = [float(x) for x in point]
    for item in candidates:
        dx = px - float(item[0])
        dy = py - float(item[1])
        dz = pz - float(item[2])
        d2 = dx * dx + dy * dy + dz * dz
        if best_d2 is None or d2 < best_d2:
            best = item
            best_d2 = d2
    return [float(x) for x in best]

def add_cylinder(name, start, end, color, radius=0.055):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    r, g, b = [float(v) for v in color]
    cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name, zoom=0)

def add_cube(name, center, size, color):
    cx, cy, cz = [float(v) for v in center]
    s = float(size) / 2.0
    vertices = [
        (cx - s, cy - s, cz - s), (cx + s, cy - s, cz - s), (cx + s, cy + s, cz - s), (cx - s, cy + s, cz - s),
        (cx - s, cy - s, cz + s), (cx + s, cy - s, cz + s), (cx + s, cy + s, cz + s), (cx - s, cy + s, cz + s),
    ]
    faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1),
             (1, 5, 6), (1, 6, 2), (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    r, g, b = [float(v) for v in color]
    obj = [BEGIN, TRIANGLES, COLOR, r, g, b]
    for face in faces:
        for index in face:
            obj.extend([VERTEX, vertices[index][0], vertices[index][1], vertices[index][2]])
    obj.append(END)
    cmd.load_cgo(obj, name, zoom=0)

def add_square_glycan(job):
    centers = job.get('glycan_centers', [])
    color = job['species_color']
    if not centers:
        return
    previous = None
    for index, center in enumerate(centers):
        add_cube('glycan_square_' + str(index), center, 1.05, color)
        if previous is not None:
            add_cylinder('glycan_link_' + str(index), previous, center, color, radius=0.085)
        previous = center
    anchor = nearest_point(centers[0], job['protein_atoms'])
    add_cylinder('glycan_protein_anchor', anchor, centers[0], color, radius=0.065)

def add_camera_dashed_envelope(job, name='sasa_outline'):
    center = [float(v) for v in job['envelope_center']]
    radius = float(job['envelope_radius'])
    view = cmd.get_view()
    right = [view[0], view[1], view[2]]
    up = [view[3], view[4], view[5]]
    obj = []
    segments = 96
    for i in range(segments):
        if i % 2 == 1:
            continue
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 0.62) / segments
        p0 = [center[j] + radius * math.cos(a0) * right[j] + radius * math.sin(a0) * up[j] for j in range(3)]
        p1 = [center[j] + radius * math.cos(a1) * right[j] + radius * math.sin(a1) * up[j] for j in range(3)]
        obj.extend([CYLINDER, p0[0], p0[1], p0[2], p1[0], p1[1], p1[2], 0.055, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06])
    cmd.load_cgo(obj, name, zoom=0)

def select_regions(job):
    accessible = 'oval and chain A and resi ' + job['accessible_resi'] if job['accessible_resi'] != 'none' else 'none'
    shielded = 'oval and chain A and resi ' + job['shielded_resi'] if job['shielded_resi'] != 'none' else 'none'
    cmd.select('accessible_region', accessible)
    cmd.select('shielded_region', shielded)

def setup_scene(job):
    cmd.reinitialize()
    set_color('species_color', job['species_color'])
    set_color('neutral_gray', [0.70, 0.70, 0.70])
    set_color('shield_black', [0.02, 0.02, 0.02])
    cmd.load(job['pdb'], 'oval')
    cmd.remove('hydrogens')
    cmd.hide('everything')
    cmd.bg_color('white')
    cmd.set('opaque_background', 1)
    cmd.set('ray_opaque_background', 1)
    cmd.set('orthoscopic', 1)
    cmd.set('transparency_mode', 3)
    cmd.set('two_sided_lighting', 1)
    cmd.set('depth_cue', 0)
    cmd.set('ambient', 0.66)
    cmd.set('specular', 0.16)
    cmd.set('shininess', 12)
    cmd.set('antialias', 2)
    cmd.set('surface_quality', 2)
    cmd.set('sphere_quality', 3)
    cmd.show('surface', 'oval and chain A')
    cmd.color('neutral_gray', 'oval and chain A')
    cmd.set('transparency', 0.58, 'oval and chain A')
    select_regions(job)
    cmd.color('species_color', 'accessible_region')
    cmd.color('shield_black', 'shielded_region')
    cmd.set('transparency', 0.20, 'accessible_region')
    cmd.set('transparency', 0.04, 'shielded_region')
    cmd.show('sticks', 'accessible_region or shielded_region')
    cmd.set('stick_radius', 0.13, 'accessible_region or shielded_region')
    cmd.show('spheres', 'accessible_region and name CA')
    cmd.show('spheres', 'shielded_region and name CA')
    cmd.set('sphere_scale', 0.38, 'accessible_region and name CA')
    cmd.set('sphere_scale', 0.44, 'shielded_region and name CA')
    add_square_glycan(job)
    cmd.orient('oval')
    cmd.turn('x', -14)
    cmd.turn('y', 30)
    cmd.turn('z', -8)
    cmd.zoom('oval', buffer=8, complete=1)
    cmd.clip('slab', 300)
    add_camera_dashed_envelope(job)

for item in JOBS:
    setup_scene(item)
    cmd.png(item['out'], width=1900, height=1450, dpi=300, ray=1)
cmd.quit()
