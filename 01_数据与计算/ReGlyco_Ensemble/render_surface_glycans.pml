reinitialize
set ray_opaque_background, on
set ray_shadows, off
set ray_trace_mode, 1
set antialias, 2
set surface_quality, 2
set ambient, 0.55
set direct, 0.35
set specular, 0.12
set shininess, 10
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
bond gallus and chain A and resi 293 and name ND2, gallus and chain B and resi 2 and name C1
set stick_radius, 0.20, gallus and (chain A and resi 293 and name ND2 or chain B and resi 2 and name C1)
orient gallus and chain A
zoom gallus, 3
turn y, -135
png surface_glycan_png/Gallus_N293_high_mannose_surface.png, 1800, 1800, 300, 1
delete gallus

load PDB_first_model/Anas_G20030CU.pdb, anas
remove anas and solvent
hide everything, anas
show surface, anas and chain A
color gray90, anas and chain A
show sticks, anas and chain A and resi 96-98
color gray60, anas and chain A and resi 96-98
set stick_radius, 0.14, anas and chain A and resi 96-98
hide surface, anas and chain A and resi 96-98
show sticks, anas and chain B
show spheres, anas and chain B
color orange, anas and chain B
set stick_radius, 0.16, anas and chain B
set sphere_scale, 0.25, anas and chain B
bond anas and chain A and resi 97 and name ND2, anas and chain B and resi 2 and name C1
set stick_radius, 0.20, anas and (chain A and resi 97 and name ND2 or chain B and resi 2 and name C1)
orient anas and chain A
zoom anas, 3
turn y, -90
png surface_glycan_png/Anas_N97_neutral_complex_surface.png, 1800, 1800, 300, 1
delete anas

load PDB_first_model/Columba_NeuAc1_GS00061.pdb, columba
remove columba and solvent
hide everything, columba
show surface, columba and chain A
color gray90, columba and chain A
show sticks, columba and chain A and resi 96-98
color gray60, columba and chain A and resi 96-98
set stick_radius, 0.14, columba and chain A and resi 96-98
hide surface, columba and chain A and resi 96-98
show sticks, columba and chain B
show spheres, columba and chain B
color orange, columba and chain B
set stick_radius, 0.16, columba and chain B
set sphere_scale, 0.25, columba and chain B
bond columba and chain A and resi 97 and name ND2, columba and chain B and resi 2 and name C1
set stick_radius, 0.20, columba and (chain A and resi 97 and name ND2 or chain B and resi 2 and name C1)
orient columba and chain A
zoom columba, 3
turn y, -90
png surface_glycan_png/Columba_N97_sialylated_complex_surface.png, 1800, 1800, 300, 1
quit
