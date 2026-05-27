
from pathlib import Path
import json
import pymol

pymol.finish_launching(['pymol', '-cq'])
from pymol import cmd

HERE = Path(__file__).resolve().parent
JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

def set_color(name, rgb):
    cmd.set_color(name, [float(x) for x in rgb])

def midpoint(a, b):
    return [(float(a[i]) + float(b[i])) / 2.0 for i in range(3)]

def base_scene(job):
    cmd.reinitialize()
    set_color('species_color', job['species_color'])
    cmd.load(job['pdb'], 'oval')
    cmd.remove('hydrogens')
    cmd.hide('everything')
    cmd.bg_color('white')
    cmd.set('opaque_background', 1)
    cmd.set('ray_opaque_background', 1)
    cmd.set('antialias', 2)
    cmd.set('ambient', 0.55)
    cmd.set('specular', 0.25)
    cmd.set('shininess', 18)
    cmd.set('depth_cue', 0)
    cmd.show('cartoon', 'oval and chain A')
    cmd.color('gray80', 'oval and chain A')
    cmd.set('cartoon_transparency', 0.18, 'oval and chain A')
    cmd.show('sticks', 'oval and chain B')
    cmd.show('spheres', 'oval and chain B')
    cmd.color('species_color', 'oval and chain B')
    cmd.set('stick_radius', 0.20, 'oval and chain B')
    cmd.set('sphere_scale', 0.34, 'oval and chain B')
    cmd.orient('oval')
    cmd.turn('x', -14)
    cmd.turn('y', 28)
    cmd.turn('z', -8)
    cmd.zoom('oval', 8)

def render_metric(job):
    base_scene(job)
    set_color('metric_color', job['metric_color'])
    cmd.pseudoatom('metric_a', pos=job['point_a'])
    cmd.pseudoatom('metric_b', pos=job['point_b'])
    cmd.show('spheres', 'metric_a or metric_b')
    cmd.color('metric_color', 'metric_a or metric_b')
    cmd.set('sphere_scale', 0.56, 'metric_a or metric_b')
    cmd.distance('metric_line', 'metric_a', 'metric_b')
    cmd.hide('labels', 'metric_line')
    cmd.set('dash_color', 'metric_color', 'metric_line')
    cmd.set('dash_width', 4.5, 'metric_line')
    cmd.set('dash_gap', 0.20, 'metric_line')
    cmd.png(job['out'], width=1800, height=1250, dpi=300, ray=0)

def add_points(object_name, points, color_name, scale):
    for point in points:
        cmd.pseudoatom(object_name, pos=point)
    if points:
        cmd.show('spheres', object_name)
        cmd.color(color_name, object_name)
        cmd.set('sphere_scale', scale, object_name)

def render_shielding(job):
    base_scene(job)
    set_color('accessible_red', [0.82, 0.12, 0.10])
    set_color('shielded_black', [0.05, 0.05, 0.05])
    add_points('accessible_hotspots', job.get('accessible', []), 'accessible_red', 0.62)
    add_points('shielded_hotspots', job.get('shielded', []), 'shielded_black', 0.70)
    cmd.png(job['out'], width=1800, height=1250, dpi=300, ray=0)

for item in JOBS['dg']:
    render_metric(item)
for item in JOBS['hk']:
    render_shielding(item)
cmd.quit()
