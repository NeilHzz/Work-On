
from pathlib import Path
import json
import math
import pymol
from pymol.cgo import CYLINDER, CONE

pymol.finish_launching(['pymol', '-cq'])
from pymol import cmd

HERE = Path(__file__).resolve().parent
JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

def set_color(name, rgb):
    cmd.set_color(name, [float(x) for x in rgb])

def add_arrow(name, start, end, color, radius=0.24, head_radius=0.72, head_length=2.2):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    if length < 1e-6:
        return
    ux, uy, uz = vx / length, vy / length, vz / length
    shaft_end = [ex - ux * head_length, ey - uy * head_length, ez - uz * head_length]
    r, g, b = [float(c) for c in color]
    obj = [
        CYLINDER, sx, sy, sz, shaft_end[0], shaft_end[1], shaft_end[2], radius, r, g, b, r, g, b,
        CONE, shaft_end[0], shaft_end[1], shaft_end[2], ex, ey, ez, head_radius, 0.0, r, g, b, r, g, b, 1.0, 0.0,
    ]
    cmd.load_cgo(obj, name)

def midpoint(a, b):
    return [(float(a[i]) + float(b[i])) / 2.0 for i in range(3)]

def add_label(name, text, pos, color_name):
    cmd.pseudoatom(name, pos=pos)
    cmd.hide('nonbonded', name)
    cmd.set('label_font_id', 7, name)
    cmd.set('label_size', 22, name)
    cmd.set('label_color', color_name, name)
    cmd.label(name, repr(text))

def scene(job):
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

    cmd.show('cartoon', 'oval and chain A')
    cmd.color('gray85', 'oval and chain A')
    cmd.set('cartoon_transparency', 0.62, 'oval and chain A')
    cmd.show('sticks', 'oval and chain B')
    cmd.show('spheres', 'oval and chain B')
    cmd.color('species_color', 'oval and chain B')
    cmd.set('stick_radius', 0.28, 'oval and chain B')
    cmd.set('sphere_scale', 0.28, 'oval and chain B')

    cmd.orient('oval and chain B')
    cmd.zoom('oval and chain B', 9)
    cmd.turn('x', -18)
    cmd.turn('y', 24)
    cmd.turn('z', -8)

    for index, metric in enumerate(job['metrics']):
        color_name = 'metric_' + metric['name'].replace('-', '_').replace(' ', '_')
        add_arrow('arrow_' + str(index), metric['start'], metric['end'], metric['color'])
        label_pos = midpoint(metric['start'], metric['end'])
        label_pos[2] += 4.0 + index * 0.8
        add_label('label_' + str(index), metric['name'], label_pos, color_name)

    cmd.png(job['out'], width=2600, height=2100, dpi=300, ray=0)

for item in JOBS:
    scene(item)
cmd.quit()
