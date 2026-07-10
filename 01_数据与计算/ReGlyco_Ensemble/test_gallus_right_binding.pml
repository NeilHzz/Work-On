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
load PDB_first_model/Gallus_G80966KZ.pdb, gallus
hide everything, gallus
show surface, gallus and chain A
color gray90, gallus and chain A
show sticks, gallus and chain A and resi 292-294
color gray60, gallus and chain A and resi 292-294
set stick_radius, 0.14, gallus and chain A and resi 292-294
hide surface, gallus and chain A and resi 292-294
show sticks, gallus and chain B
show spheres, gallus and chain B
color orange, gallus and chain B
set stick_radius, 0.16, gallus and chain B
set sphere_scale, 0.25, gallus and chain B
orient gallus and chain A
zoom gallus, 3
turn y, 45
turn z, 180
png orientation_test/gallus_right_binding.png, 600, 600, 150, 1
quit
