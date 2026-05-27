
from pathlib import Path
import json
import math
import pymol
from pymol.cgo import CYLINDER, CONE, BEGIN, LINES, VERTEX, END

pymol.finish_launching(['pymol', '-cq'])
from pymol import cmd

HERE = Path(__file__).resolve().parent
JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

def set_color(name, rgb):
    cmd.set_color(name, [float(x) for x in rgb])

def add_arrow(name, start, end, color, radius=0.055, head_radius=0.22, head_length=0.75):
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

def add_line(name, start, end, color, radius=0.045):
    sx, sy, sz = [float(v) for v in start]
    ex, ey, ez = [float(v) for v in end]
    r, g, b = [float(c) for c in color]
    cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name)

def midpoint(a, b):
    return [(float(a[i]) + float(b[i])) / 2.0 for i in range(3)]

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
    cmd.set('orthoscopic', 1)
    cmd.set('two_sided_lighting', 1)
    cmd.set('transparency_mode', 3)

    cmd.select('protein_context', 'byres (oval and chain A within 10 of (oval and chain B))')
    cmd.show('lines', 'protein_context')
    cmd.color('gray70', 'protein_context')
    cmd.set('line_width', 1.8, 'protein_context')
    cmd.show('sticks', 'oval and chain B')
    cmd.show('spheres', 'oval and chain B')
    cmd.color('species_color', 'oval and chain B and elem C')
    cmd.color('red', 'oval and chain B and elem O')
    cmd.color('blue', 'oval and chain B and elem N')
    cmd.color('white', 'oval and chain B and elem H')
    cmd.set('stick_radius', 0.13, 'oval and chain B')
    cmd.set('sphere_scale', 0.16, 'oval and chain B')
    cmd.set('stick_ball', 1, 'oval and chain B')
    cmd.set('stick_ball_ratio', 1.55, 'oval and chain B')

    cmd.orient('oval and chain B')
    cmd.turn('x', -16)
    cmd.turn('y', 22)
    cmd.turn('z', -12)
    cmd.zoom('oval and chain B', 16)
    cmd.clip('slab', 120)

    for index, metric in enumerate(job['metrics']):
        if metric['name'] == 'Glycan-Protein':
            add_line('metric_' + str(index), metric['start'], metric['end'], metric['color'], radius=0.040)
        else:
            add_arrow('metric_' + str(index), metric['start'], metric['end'], metric['color'])

    cmd.png(job['out'], width=2600, height=2100, dpi=300, ray=0)

for item in JOBS:
    scene(item)
cmd.quit()
