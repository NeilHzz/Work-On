
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

def add_arrow(name, start, end, color, radius=0.018, head_radius=0.065, head_length=0.24):
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

def add_line(name, start, end, color, radius=0.016):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    r, g, b = [float(c) for c in color]
    cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name)

def add_dashed_line(name, start, end, color, radius=0.055, segments=18):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    r, g, b = [float(c) for c in color]
    obj = []
    for i in range(segments):
        if i % 2 == 1:
            continue
        t0 = i / segments
        t1 = (i + 1) / segments
        x0, y0, z0 = sx + (ex - sx) * t0, sy + (ey - sy) * t0, sz + (ez - sz) * t0
        x1, y1, z1 = sx + (ex - sx) * t1, sy + (ey - sy) * t1, sz + (ez - sz) * t1
        obj.extend([CYLINDER, x0, y0, z0, x1, y1, z1, radius, r, g, b, r, g, b])
    cmd.load_cgo(obj, name)

def add_endpoint_spheres(name, start, end, color, radius=0.22):
    set_color(name + '_color', color)
    cmd.pseudoatom(name + '_start', pos=[float(v) for v in start], vdw=radius)
    cmd.pseudoatom(name + '_end', pos=[float(v) for v in end], vdw=radius)
    cmd.show('spheres', name + '_start or ' + name + '_end')
    cmd.color(name + '_color', name + '_start or ' + name + '_end')

def add_metric_label(name, label, start, end, color, shift=(0.0, 0.0, 0.0)):
    pos = [
        (float(start[i]) + float(end[i])) * 0.5 + float(shift[i])
        for i in range(3)
    ]
    color_name = name + '_label_color'
    set_color(color_name, color)
    cmd.pseudoatom(name + '_label', pos=pos)
    cmd.label(name + '_label', repr(label))
    cmd.set('label_color', color_name, name + '_label')
    cmd.set('label_size', 22, name + '_label')
    cmd.set('label_font_id', 7, name + '_label')
    cmd.set('label_position', [0, 0, 0], name + '_label')

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

def add_rg_sphere(job):
    center = [float(v) for v in job['glycan_center']]
    rg = float(job['glycan_rg'])
    set_color('rg_gold', [1.0, 0.58, 0.04])
    set_color('rg_orange', [0.95, 0.34, 0.00])
    cmd.pseudoatom('rg_centroid', pos=center, vdw=0.30)
    cmd.show('spheres', 'rg_centroid')
    cmd.color('rg_gold', 'rg_centroid')
    cmd.pseudoatom('rg_shell', pos=center, vdw=rg)
    cmd.show('spheres', 'rg_shell')
    cmd.color('rg_gold', 'rg_shell')
    cmd.set('sphere_transparency', 0.90 if job.get('is_focus') else 0.86, 'rg_shell')
    cmd.set('sphere_quality', 3, 'rg_shell')
    rg_metric = next((metric for metric in job['metrics'] if metric['name'] == 'Rg turn'), None)
    if rg_metric:
        target = rg_metric['end']
        if job.get('is_focus'):
            target = [center[0] - 0.82 * rg, center[1] + 0.30 * rg, center[2] + 0.48 * rg]
            add_arrow('rg_radius_arrow', center, target, [1.0, 0.47, 0.0], radius=0.052, head_radius=0.17, head_length=0.42)
        else:
            add_arrow('rg_radius_arrow', center, target, [1.0, 0.47, 0.0], radius=0.030, head_radius=0.115, head_length=0.34)

def add_focus_glycan_protein_distance(job):
    metric = next((item for item in job['metrics'] if item['name'] == 'Glycan-Protein'), None)
    if metric:
        add_dashed_line('focus_glycan_protein_dashed', metric['start'], metric['end'], [0.0, 0.62, 0.36], radius=0.095, segments=12)

def add_focus_metrics(job):
    metric_specs = {
        'End-to-End': {'letter': 'E', 'radius': 0.115, 'head_radius': 0.300, 'head_length': 0.70, 'color': [0.00, 0.44, 0.70], 'shift': [1.10, 0.82, 0.18]},
        'Glycan-Protein': {'letter': 'F', 'radius': 0.100, 'head_radius': 0.270, 'head_length': 0.58, 'color': [0.00, 0.62, 0.36], 'shift': [-0.95, 0.72, 0.22]},
        'Glycan-Backbone': {'letter': 'G', 'radius': 0.125, 'head_radius': 0.330, 'head_length': 0.58, 'color': [0.80, 0.25, 0.55], 'shift': [0.70, -0.68, 0.32]},
    }
    for metric in job['metrics']:
        name = metric['name']
        if name not in metric_specs:
            continue
        spec = metric_specs[name]
        add_arrow(
            'focus_' + name.replace('-', '_').replace(' ', '_'),
            metric['start'],
            metric['end'],
            spec['color'],
            radius=spec['radius'],
            head_radius=spec['head_radius'],
            head_length=spec['head_length'],
        )
        if name in {'Glycan-Protein', 'Glycan-Backbone'}:
            add_endpoint_spheres('endpoint_' + name.replace('-', '_').replace(' ', '_'), metric['start'], metric['end'], spec['color'], radius=0.15)
        add_metric_label(
            'label_' + name.replace('-', '_').replace(' ', '_'),
            spec['letter'],
            metric['start'],
            metric['end'],
            spec['color'],
            shift=spec['shift'],
        )

def render_focus_markers(job):
    marker_colors = {
        'End-to-End': {'start': [1.0, 0.0, 0.0], 'end': [0.0, 1.0, 0.0]},
        'Glycan-Protein': {'start': [0.0, 0.0, 1.0], 'end': [1.0, 0.0, 1.0]},
        'Glycan-Backbone': {'start': [0.0, 1.0, 1.0], 'end': [1.0, 1.0, 0.0]},
    }
    cmd.hide('everything')
    cmd.delete('rg_centroid')
    cmd.delete('rg_shell')
    cmd.bg_color('black')
    cmd.set('opaque_background', 1)
    for metric in job['metrics']:
        name = metric['name']
        if name not in marker_colors:
            continue
        safe = name.replace('-', '_').replace(' ', '_')
        for end_name in ['start', 'end']:
            color_name = safe + '_' + end_name + '_marker_color'
            object_name = safe + '_' + end_name + '_marker'
            set_color(color_name, marker_colors[name][end_name])
            cmd.pseudoatom(object_name, pos=metric[end_name], vdw=0.65)
            cmd.show('spheres', object_name)
            cmd.color(color_name, object_name)
            cmd.set('sphere_transparency', 0.0, object_name)
    cmd.png(job['marker_out'], width=2200, height=1800, dpi=300, ray=1)

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
    cmd.set('transparency', 0.50, 'oval and chain A')
    cmd.select('protein_anchor', 'byres (oval and chain A within 4 of (oval and chain B))')
    cmd.color('gray62', 'protein_anchor')
    cmd.set('transparency', 0.68 if job.get('is_focus') else 0.32, 'protein_anchor')
    cmd.color('gray65', 'oval and chain A')
    color_full_glycan()
    add_rg_sphere(job)
    if job.get('is_focus'):
        add_focus_glycan_protein_distance(job)
    cmd.orient('oval and chain B')
    cmd.turn('x', job['overview_turns'][0])
    cmd.turn('y', job['overview_turns'][1])
    cmd.turn('z', job['overview_turns'][2])
    if job.get('is_focus'):
        cmd.zoom('oval and chain B', buffer=3, complete=1)
        cmd.clip('slab', 125)
    else:
        cmd.zoom('oval and chain A', buffer=46, complete=1)
        cmd.clip('slab', 420)
        add_camera_circle('glycan_locator', job['glycan_center'], max(9.0, job['glycan_radius'] * 1.75), color=(0.18, 0.18, 0.18))
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
    cmd.zoom('oval and chain B', buffer=10, complete=1)
    cmd.clip('slab', 160)

    if show_metrics:
        for index, metric in enumerate(job['metrics']):
            if metric['name'] == 'Glycan-Protein':
                add_line('metric_' + str(index), metric['start'], metric['end'], metric['color'], radius=0.012)
            else:
                add_arrow('metric_' + str(index), metric['start'], metric['end'], metric['color'])

    cmd.png(out_path, width=2200, height=2200, dpi=300, ray=1)

for item in JOBS:
    scene_overview(item)
cmd.quit()
