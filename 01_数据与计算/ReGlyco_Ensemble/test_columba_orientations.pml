reinitialize
set ray_opaque_background, on
set ray_shadows, off
set ray_trace_mode, 1
set surface_quality, 1
set ambient, 0.55
set direct, 0.35
set specular, 0.12
set two_sided_lighting, on
bg_color white

load PDB_first_model/Columba_NeuAc1_GS00061.pdb, columba
hide everything, columba
show surface, columba and chain A
color gray90, columba and chain A
show sticks, columba and chain B
show spheres, columba and chain B
color orange, columba and chain B
set stick_radius, 0.16, columba and chain B
set sphere_scale, 0.25, columba and chain B
orient columba and chain A
zoom columba, 3
turn y, -90
png orientation_test/columba_y-90.png, 600, 600, 150, 1
orient columba and chain A
zoom columba, 3
turn y, -45
png orientation_test/columba_y-45.png, 600, 600, 150, 1
orient columba and chain A
zoom columba, 3
turn y, 45
png orientation_test/columba_y45.png, 600, 600, 150, 1
orient columba and chain A
zoom columba, 3
turn y, 90
png orientation_test/columba_y90.png, 600, 600, 150, 1
quit
