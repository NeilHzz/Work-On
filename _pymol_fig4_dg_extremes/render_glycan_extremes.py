
from pathlib import Path
import json
import math
import pymol
from pymol.cgo import CYLINDER, CONE, BEGIN, LINES, COLOR, VERTEX, END

pymol.finish_launching(['pymol', '-cq'])
from pymol import cmd

HERE = Path(__file__).resolve().parent
JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

def set_color(name, rgb):
    cmd.set_color(name, [float(x) for x in rgb])

def add_arrow(name, start, end, color, radius=0.026, head_radius=0.095, head_length=0.34):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    if length < 1e-6:
        return
    head_length = min(head_length, length * 0.32)
    ux, uy, uz = vx / length, vy / length, vz / length
    shaft_end = [ex - ux * head_length, ey - uy * head_length, ez - uz * head_length]
    r, g, b = [float(c) for c in color]
    obj = [
        CYLINDER, sx, sy, sz, shaft_end[0], shaft_end[1], shaft_end[2], radius, r, g, b, r, g, b,
        CONE, shaft_end[0], shaft_end[1], shaft_end[2], ex, ey, ez, head_radius, 0.0, r, g, b, r, g, b, 1.0, 0.0,
    ]
    cmd.load_cgo(obj, name)

def add_line(name, start, end, color, radius=0.024):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    r, g, b = [float(c) for c in color]
    cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name)

def add_camera_circle(name, center, radius, color=(0.0, 0.0, 0.0), segments=144):
    view = cmd.get_view()
    right = [view[0], view[1], view[2]]
    up = [view[3], view[4], view[5]]
    center = [float(v) for v in center]
    r, g, b = [float(c) for c in color]
    obj = [BEGIN, LINES, COLOR, r, g, b]
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        p0 = [center[j] + radius * math.cos(a0) * right[j] + radius * math.sin(a0) * up[j] for j in range(3)]
        p1 = [center[j] + radius * math.cos(a1) * right[j] + radius * math.sin(a1) * up[j] for j in range(3)]
        obj.extend([VERTEX, p0[0], p0[1], p0[2], VERTEX, p1[0], p1[1], p1[2]])
    obj.append(END)
    cmd.load_cgo(obj, name)

def setup_scene(job):
    cmd.reinitialize()
    set_color('species_color', job['species_color'])
    for metric in job['metrics']:
        set_color('metric_' + metric['name'].replace('-', '_').replace(' ', '_'), metric['color'])
    cmd.load(job['pdb'], 'oval')
    cmd.remove('hydrogens')
    cmd.hide('everything')
    cmd.bg_color('white')
    cmd.set('opaque_background', 1)
    cmd.set('antialias', 2)
    cmd.set('ambient', 0.62)
    cmd.set('specular', 0.12)
    cmd.set('shininess', 10)
    cmd.set('depth_cue', 0)
    cmd.set('line_smooth', 1)
    cmd.set('stick_quality', 18)
    cmd.set('sphere_quality', 2)
    cmd.set('surface_quality', 1)
    cmd.set('ray_trace_mode', 1)
    cmd.set('ray_opaque_background', 1)
    cmd.set('orthoscopic', 1)
    cmd.set('two_sided_lighting', 1)
    cmd.set('transparency_mode', 3)

def color_full_glycan():
    cmd.show('sticks', 'oval and chain B')
    cmd.show('spheres', 'oval and chain B')
    cmd.color('species_color', 'oval and chain B and elem C')
    cmd.color('red', 'oval and chain B and elem O')
    cmd.color('blue', 'oval and chain B and elem N')
    cmd.color('white', 'oval and chain B and elem H')
    cmd.set('stick_radius', 0.10, 'oval and chain B')
    cmd.set('sphere_scale', 0.12, 'oval and chain B')
    cmd.set('stick_ball', 1, 'oval and chain B')
    cmd.set('stick_ball_ratio', 1.55, 'oval and chain B')

def scene_overview(job):
    setup_scene(job)
    cmd.show('surface', 'oval and chain A')
    cmd.color('gray85', 'oval and chain A')
    cmd.set('transparency', 0.42, 'oval and chain A')
    cmd.show('lines', 'oval and chain A')
    cmd.color('gray65', 'oval and chain A')
    cmd.set('line_width', 0.65, 'oval and chain A')
    color_full_glycan()
    cmd.orient('oval and chain A or oval and chain B')
    cmd.turn('x', -12)
    cmd.turn('y', 26)
    cmd.turn('z', -6)
    cmd.zoom('oval and chain A or oval and chain B', 22)
    cmd.clip('slab', 220)
    add_camera_circle('glycan_locator', job['glycan_center'], max(6.0, job['glycan_radius'] * 1.35))
    cmd.png(job['overview_out'], width=2200, height=1800, dpi=300, ray=1)

def scene_zoom(job, out_path, rotate_y=0, show_metrics=True):
    setup_scene(job)

    cmd.select('protein_context', 'byres (oval and chain A within 8 of (oval and chain B))')
    cmd.show('lines', 'protein_context')
    cmd.color('gray70', 'protein_context')
    cmd.set('line_width', 1.35, 'protein_context')
    color_full_glycan()
    cmd.orient('oval and chain B')
    cmd.turn('x', -14)
    cmd.turn('y', 18 + float(rotate_y))
    cmd.turn('z', -8)
    cmd.zoom('oval and chain B', 14)
    cmd.clip('slab', 160)

    if show_metrics:
        for index, metric in enumerate(job['metrics']):
            if metric['name'] == 'Glycan-Protein':
                add_line('metric_' + str(index), metric['start'], metric['end'], metric['color'], radius=0.018)
            else:
                add_arrow('metric_' + str(index), metric['start'], metric['end'], metric['color'])

    cmd.png(out_path, width=2200, height=2200, dpi=300, ray=1)

for item in JOBS:
    scene_overview(item)
    scene_zoom(item, item['zoom_front_out'], rotate_y=0, show_metrics=True)
    scene_zoom(item, item['zoom_back_out'], rotate_y=180, show_metrics=False)
cmd.quit()
