"""
species_selection_avonet.py — Two-panel figure using AVONET (Tobias et al. 2022)
Panel A: 2D scatter with k=3 clusters
Panel B: Stacked percentage bars showing cluster membership of key orders

Data sources:
  X axis: PC1 of PCA on three AVONET fields (Primary.Lifestyle, Habitat, Trophic.Niche)
           encoded on aquatic-dependency gradient, accounting for 71.7% of variance
  Y axis: developmental mode (order-level, Starck & Ricklefs 1998)
  AVONET citation: Tobias JA et al. (2022) Ecology Letters 25:581-597
"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
matplotlib.rcParams["font.size"] = 16
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ============================================================
# 1. Load pre-processed AVONET scores (aquatic_score, dev_score, cluster)
# ============================================================
_data_xlsx = r'D:\system_folder\Desktop\Work On\01_数据与计算\物种选择_完整版\analysis_data.xlsx'
df = pd.read_excel(_data_xlsx, sheet_name='AVONET_species_scores', engine='openpyxl')
df.rename(columns={'Species': 'Species1', 'Order': 'Order1', 'Family': 'Family1',
                    'Lifestyle': 'Primary.Lifestyle'}, inplace=True)
df['pc2_score'] = df['discordance_score']
df['aq_rank'] = df['aquatic_score'].rank(pct=True)
X2 = df[['aquatic_score', 'dev_score']].values  # KMeans on (PC1, dev_score)

# ============================================================
# 2. K-means k=3
# ============================================================
km3 = KMeans(n_clusters=3, random_state=42, n_init=100, max_iter=500)
df['cluster'] = km3.fit_predict(X2)
sc3 = silhouette_score(X2, df['cluster'])

focal_sp = {
    'Anas platyrhynchos': None,
    'Columba livia':      None,
    'Gallus gallus':      None,
}
for sp in focal_sp:
    focal_sp[sp] = df[df['Species1'] == sp].iloc[0]

anas_cl = focal_sp['Anas platyrhynchos']['cluster']
col_cl  = focal_sp['Columba livia']['cluster']
gal_cl  = focal_sp['Gallus gallus']['cluster']
assert len({anas_cl, col_cl, gal_cl}) == 3, "Focal species not in 3 separate clusters!"

cl_colors = {anas_cl: '#93AACD', gal_cl: '#C46B83', col_cl: '#F3CE9D'}
cl_ec     = {anas_cl: '#4A6080', gal_cl: '#7A1A30', col_cl: '#A07828'}
cl_labels = {
    anas_cl: 'Aquatic foragers\n(n=%d sp.)' % (df['cluster'] == anas_cl).sum(),
    gal_cl:  'Terrestrial precocial\n(n=%d sp.)' % (df['cluster'] == gal_cl).sum(),
    col_cl:  'Terrestrial altricial\n(n=%d sp.)' % (df['cluster'] == col_cl).sum(),
}
focal_cfg = {
    'Anas platyrhynchos': ('Anas',    '#93AACD', 'o', 260),
    'Columba livia':      ('Columba', '#F3CE9D', 's', 240),
    'Gallus gallus':      ('Gallus',  '#C46B83', '^', 240),
}

# ---- Order color palette ----
ORDER_COLORS = {
    # focal — fixed, do not change
    'Anseriformes':        '#93AACD',
    'Galliformes':         '#C46B83',
    'Columbiformes':       '#F3CE9D',
    # aquatic belt
    'Charadriiformes':     '#70A850',  # was #6BAED6 blue → conflicts in R7 (Gallus zone)
    'Procellariiformes':   '#4A7BB5',
    'Suliformes':          '#5B9DC2',
    'Pelecaniformes':      '#B07840',  # was #4C9BAA teal-blue → conflicts in R16 (Columba zone)
    'Gaviiformes':         '#3D6E99',
    'Podicipediformes':    '#74B9DC',
    'Sphenisciformes':     '#3D7A7A',
    'Phoenicopteriformes': '#D47A9A',
    # terrestrial precocial / ratites
    'Gruiformes':          '#D48A40',
    'Tinamiformes':        '#D47A5A',
    'Otidiformes':         '#A06030',  # was #C8A830 golden → conflicts in R7 (Gallus zone)
    'Struthioniformes':    '#A04455',
    'Rheiformes':          '#88BB55',
    'Casuariiformes':      '#4A9955',
    'Apterygiformes':      '#8855AA',
    'Pterocliformes':      '#C88840',
    'Mesitornithiformes':  '#5DAA55',  # was #55AABB blue-teal → conflicts in R7 (Gallus zone)
    'Cariamiformes':       '#BB66CC',
    'Eurypygiformes':      '#55BB99',
    # terrestrial altricial
    'Passeriformes':       '#8855AA',
    'Psittaciformes':      '#44AA77',
    'Apodiformes':         '#CC8833',
    'Piciformes':          '#3A8868',  # was #CC5533 orange-red → conflicts in R16 (Columba zone)
    'Coraciiformes':       '#9A7540',  # was #3399AA teal-blue → conflicts in R16 (Columba zone)
    'Cuculiformes':        '#6A9A50',  # was #BB8822 golden → conflicts in R16 (Columba zone)
    'Caprimulgiformes':    '#5A9050',  # was #BB4444 red → conflicts in R16 (Columba zone)
    'Strigiformes':        '#6655AA',
    'Accipitriformes':     '#7A7025',  # was #4455AA blue → conflicts in R16 (Columba zone)
    'Cathartiformes':      '#5A8840',  # was #5566BB blue → conflicts in R16 (Columba zone)
    'Falconiformes':       '#907A40',  # was #6644BB blue-purple → conflicts in R16 (Columba zone)
    'Bucerotiformes':      '#2D9060',  # was #BB3333 red → conflicts in R16 (Columba zone)
    'Trogoniformes':       '#44AAAA',
    'Musophagiformes':     '#88AA44',  # was #BB4477 pink-red → conflicts in R16 (Columba zone)
    'Ciconiiformes':       '#4A8855',  # was #CC5522 orange-red → conflicts in R16 (Columba zone)
    'Phaethontiformes':    '#BB6688',
    'Coliiformes':         '#9933BB',
    'Opisthocomiformes':   '#99BB33',
    'Leptosomiformes':     '#8A7240',  # was #4499BB blue → conflicts in R16 (Columba zone)
}

# ============================================================
# 3. Figure geometry
# ============================================================
fig = plt.figure(figsize=(10, 10))
ax1 = fig.add_axes([0.05, 0.05, 0.9, 0.9], projection='3d')  # Panel A — 3D

# ============================================================
# Panel A — scatter per-order colors
# ============================================================
rng = np.random.default_rng(0)
jitter_dev = rng.normal(0, 0.018, len(df))
jitter_aq  = rng.normal(0, 0.010, len(df))
jitter_pc2 = rng.normal(0, 0.010, len(df))
df = df.copy()
df['dev_jit'] = (df['dev_score'] + jitter_dev).clip(-0.05, 1.05)
df['aq_jit']  = (df['aquatic_score'] + jitter_aq).clip(-0.05, 1.05)
df['pc2_jit'] = (df['pc2_score']    + jitter_pc2).clip(-0.05, 1.05)

focal_orders = {'Anseriformes', 'Galliformes', 'Columbiformes'}
all_orders_sorted = (
    [o for o in df['Order1'].unique() if o not in focal_orders]
    + list(focal_orders)
)
_focal_names_set = set(focal_cfg.keys())
_non_focal_mask  = ~df['Species1'].isin(_focal_names_set)

for order in all_orders_sorted:
    mask = (df['Order1'] == order) & _non_focal_mask
    if not mask.any():
        continue
    color    = ORDER_COLORS.get(order, '#AAAAAA')
    is_focal = order in focal_orders
    ax1.scatter(df.loc[mask, 'aq_jit'],
                df.loc[mask, 'pc2_jit'],
                df.loc[mask, 'dev_jit'],
                c=color,
                alpha=1.0 if is_focal else 0.25,
                s=10 if is_focal else 5,
                linewidths=0,
                depthshade=True,
                zorder=3 if is_focal else 2)

# 3D axes appearance — transparent panes, no grid
ax1.xaxis.pane.fill = False
ax1.yaxis.pane.fill = False
ax1.zaxis.pane.fill = False
ax1.xaxis.pane.set_edgecolor('#BBBBBB')
ax1.yaxis.pane.set_edgecolor('#BBBBBB')
ax1.zaxis.pane.set_edgecolor('#BBBBBB')
ax1.grid(False)

# Compute cluster-boundary split lines from k-means centroids
_centroids = km3.cluster_centers_   # (3,2): cols = [aquatic_score, dev_score]
_aq_lo_cent = max(_centroids[gal_cl, 0], _centroids[col_cl, 0])  # terrestrial centroid X
_aq_hi_cent = _centroids[anas_cl, 0]                              # aquatic centroid X
# Two PC1 boundaries defining: fully-terrestrial | transitional | fully-aquatic
_aq_lo  = _aq_lo_cent + (_aq_hi_cent - _aq_lo_cent) / 3.0
_aq_hi  = _aq_lo_cent + (_aq_hi_cent - _aq_lo_cent) * 2.0 / 3.0
# Developmental mode zone boundaries (Starck & Ricklefs 1998)
_dev_lo = 0.2   # precocial | transitional
_dev_hi = 0.7   # transitional | altricial
_disc_lo = 1/3.0
_disc_hi = 2/3.0

# Region 7 fill: X=[0,_aq_lo], Y=[0,_disc_lo], Z=[0,_dev_lo]  (terrestrial, low-discord, precocial)
_r7_col = '#C4C4C4'
_r7_alpha = 0.20
# Top face (Z = _dev_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(0,0,_dev_lo), (_aq_lo,0,_dev_lo), (_aq_lo,_disc_lo,_dev_lo), (0,_disc_lo,_dev_lo)]],
    facecolors=_r7_col, edgecolors='none', alpha=_r7_alpha, zorder=0))
# Front wall (Y = _disc_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(0,_disc_lo,0), (_aq_lo,_disc_lo,0), (_aq_lo,_disc_lo,_dev_lo), (0,_disc_lo,_dev_lo)]],
    facecolors=_r7_col, edgecolors='none', alpha=_r7_alpha, zorder=0))
# Right wall (X = _aq_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(_aq_lo,0,0), (_aq_lo,_disc_lo,0), (_aq_lo,_disc_lo,_dev_lo), (_aq_lo,0,_dev_lo)]],
    facecolors=_r7_col, edgecolors='none', alpha=_r7_alpha, zorder=0))

# Region 9: X=[_aq_hi,1], Y=[0,_disc_lo], Z=[0,_dev_lo]  (aquatic, low-discord, precocial — Anas)
_r9_col = '#C4C4C4'
_r9_alpha = 0.20
# Top face (Z = _dev_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(_aq_hi,0,_dev_lo), (1,0,_dev_lo), (1,_disc_lo,_dev_lo), (_aq_hi,_disc_lo,_dev_lo)]],
    facecolors=_r9_col, edgecolors='none', alpha=_r9_alpha, zorder=0))
# Front wall (Y = _disc_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(_aq_hi,_disc_lo,0), (1,_disc_lo,0), (1,_disc_lo,_dev_lo), (_aq_hi,_disc_lo,_dev_lo)]],
    facecolors=_r9_col, edgecolors='none', alpha=_r9_alpha, zorder=0))
# Left wall (X = _aq_hi)
ax1.add_collection3d(Poly3DCollection(
    [[(_aq_hi,0,0), (_aq_hi,_disc_lo,0), (_aq_hi,_disc_lo,_dev_lo), (_aq_hi,0,_dev_lo)]],
    facecolors=_r9_col, edgecolors='none', alpha=_r9_alpha, zorder=0))

# Region 16: X=[0,_aq_lo], Y=[0,_disc_lo], Z=[_dev_hi,1]  (terrestrial, low-discord, altricial — Columba)
_r16_col = '#C4C4C4'
_r16_alpha = 0.20
# Front wall (Y = _disc_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(0,_disc_lo,_dev_hi), (_aq_lo,_disc_lo,_dev_hi), (_aq_lo,_disc_lo,1.05), (0,_disc_lo,1.05)]],
    facecolors=_r16_col, edgecolors='none', alpha=_r16_alpha, zorder=0))
# Right wall (X = _aq_lo)
ax1.add_collection3d(Poly3DCollection(
    [[(_aq_lo,0,_dev_hi), (_aq_lo,_disc_lo,_dev_hi), (_aq_lo,_disc_lo,1.05), (_aq_lo,0,1.05)]],
    facecolors=_r16_col, edgecolors='none', alpha=_r16_alpha, zorder=0))
# Bottom face (Z = _dev_hi)
ax1.add_collection3d(Poly3DCollection(
    [[(0,0,_dev_hi), (_aq_lo,0,_dev_hi), (_aq_lo,_disc_lo,_dev_hi), (0,_disc_lo,_dev_hi)]],
    facecolors=_r16_col, edgecolors='none', alpha=_r16_alpha, zorder=0))

# Focal species markers + arrow annotations
_arrow_cfg = {
    'Anas platyrhynchos': (( 52, -38),  0.20),
    'Columba livia':      ((-58,  42), -0.20),
    'Gallus gallus':      ((-58, -38),  0.20),
}
# Record 3D coordinates for each focal species (used for 2D overlay below)
for sp, (short, col, mrkr, sz) in focal_cfg.items():
    r = focal_sp[sp]
    x0 = r['aquatic_score']
    y0 = r['pc2_score']
    z0 = r['dev_score']
    focal_cfg[sp] = (short, col, mrkr, sz, x0, y0, z0)

# Legend
legend_groups = [
    ('\u2500\u2500 Focal species \u2500\u2500\u2500\u2500\u2500\u2500', '#FFFFFF'),
    (r'Anseriformes  ($\it{Anas}$)',    '#93AACD'),
    (r'Galliformes  ($\it{Gallus}$)',   '#C46B83'),
    (r'Columbiformes  ($\it{Columba}$)','#F3CE9D'),
    ('\u2500\u2500 Aquatic \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500', '#FFFFFF'),
    ('Charadriiformes',   '#6BAED6'),
    ('Procellariiformes', '#4A7BB5'),
    ('Pelecaniformes',    '#4C9BAA'),
    ('Suliformes',        '#5B9DC2'),
    ('Podicipediformes',  '#74B9DC'),
    ('Sphenisciformes',   '#3D7A7A'),
    ('Gaviiformes',       '#3D6E99'),
    ('Phoenicopterif.',   '#D47A9A'),
    ('\u2500\u2500 Precocial \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500', '#FFFFFF'),
    ('Gruiformes',        '#D48A40'),
    ('Tinamiformes',      '#D47A5A'),
    ('Otidiformes',       '#C8A830'),
    ('Struthionif.',      '#A04455'),
    ('\u2500\u2500 Altricial \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500', '#FFFFFF'),
    ('Passeriformes',     '#8855AA'),
    ('Psittaciformes',    '#44AA77'),
    ('Apodiformes',       '#CC8833'),
    ('Piciformes',        '#CC5533'),
    ('Accipitriformes',   '#4455AA'),
    ('Cathartiformes',    '#5566BB'),
    ('Strigiformes',      '#6655AA'),
    ('Falconiformes',     '#6644BB'),
    ('Coraciiformes',     '#3399AA'),
    ('Cuculiformes',      '#BB8822'),
    ('Bucerotiformes',    '#BB3333'),
    ('Caprimulgiformes',  '#BB4444'),
    ('Trogoniformes',     '#44AAAA'),
    ('Ciconiiformes',     '#CC5522'),
    ('Musophagiformes',   '#BB4477'),
]
legend_handles = []
for lbl, col in legend_groups:
    if lbl.startswith('\u2500\u2500'):
        legend_handles.append(mpatches.Patch(fc='none', ec='none', label=lbl))
    else:
        legend_handles.append(mpatches.Patch(fc=col, ec='none', label=lbl, linewidth=0))

ax1.legend(handles=legend_handles,
           loc='upper left', bbox_to_anchor=(1.05, 1.0),
           fontsize=14, framealpha=0.93,
           ncol=1, handlelength=0.9, handleheight=0.85,
           borderpad=0.5, labelspacing=0.25,
           title='Taxonomic order', title_fontsize=15)

ax1.text2D(0.05, 0.05, 'k-means k=3\nSilhouette = %.3f' % sc3,
           transform=ax1.transAxes,
           ha='left', va='bottom', fontsize=15, color='#444444',
           bbox=dict(fc='white', ec='#AAAAAA', alpha=0.80, pad=3, lw=0.8))

ax1.set_xlim(0, 1)
ax1.set_ylim(1, 0)
ax1.set_zlim(-0.05, 1.05)
ax1.set_xlabel('Aquatic association (PC1)', fontsize=18, labelpad=12)
ax1.set_ylabel('Lifestyle-habitat discordance', fontsize=18, labelpad=12)
ax1.set_zlabel('Developmental mode', fontsize=18, labelpad=12)
ax1.view_init(elev=25, azim=40)

# fig.suptitle(
#     'Unsupervised k-means clustering (k=3, silhouette=%.3f) separates waterbird / '
#     'terrestrial-precocial / terrestrial-altricial functional groups\n'
#     'G. gallus, A. platyrhynchos, and C. livia each represent one cluster  |  '
#     'dots colored by taxonomic order  |  %d bird species  |  '
#     'AVONET: Tobias et al. (2022)' % (sc3, len(df)),
#     fontsize=11, fontweight='bold', y=1.01)

# Focal species text labels
_lbl_pos = {
    'Anas platyrhynchos': (0.50, 0.13),
    'Gallus gallus':      (0.80, 0.28),
    'Columba livia':      (0.90, 0.55),
}
for sp, val in focal_cfg.items():
    short, col = val[0], val[1]
    xf, yf = _lbl_pos.get(sp, (0.5, 0.5))
    ax1.text2D(xf, yf, short,
               transform=ax1.transAxes,
               fontsize=18, fontweight='bold', fontstyle='italic', color=col,
               ha='center', va='bottom', clip_on=False,
               bbox=dict(fc='white', ec=col, lw=1.5, alpha=0.92,
                         boxstyle='round,pad=0.3'))
# 2D overlay: draw focal markers on top of 3D scene (bypasses 3D depth sorting)
fig.canvas.draw()  # finalise layout / 3D projection
from mpl_toolkits.mplot3d import proj3d
import matplotlib.patches as mpatches
# Transparent 2D axes at the same position — avoids Axes3D's do_3d_projection call
_pos = ax1.get_position()
_ax_ov = fig.add_axes([_pos.x0, _pos.y0, _pos.width, _pos.height],
                       frameon=False, label='_focal_overlay',
                       zorder=ax1.get_zorder() + 10)
_ax_ov.set_xlim(0, 1); _ax_ov.set_ylim(0, 1); _ax_ov.axis('off')
for sp, val in focal_cfg.items():
    col = val[1]
    x0, y0, z0 = val[4], val[5], val[6]
    x2d, y2d, _ = proj3d.proj_transform(x0, y0, z0, ax1.get_proj())
    x_px, y_px = ax1.transData.transform((x2d, y2d))
    x_ax = (x_px - ax1.bbox.x0) / ax1.bbox.width
    y_ax = (y_px - ax1.bbox.y0) / ax1.bbox.height
    # data coords = axes fraction (xlim/ylim both [0,1])
    _ax_ov.plot([x_ax], [y_ax], 'o',
                markersize=9, markerfacecolor='white',
                markeredgecolor=col, markeredgewidth=2.5,
                zorder=500, clip_on=False)

save_fig(plt.gcf(), 'Fig1A', dpi=160)

# ============================================================
# Console stats
# ============================================================
print('\n=== Key statistics ===')
print('Total species: %d' % len(df))
print('k=3 Silhouette coefficient: %.4f  (>0.7 = strong structure)' % sc3)
print()
for sp, r in focal_sp.items():
    cl = r['cluster']
    n  = (df['cluster'] == cl).sum()
    print('%s -> %s (n=%d sp., aquatic=%.2f dev=%.2f)' % (
        sp, cl_labels[cl].split('\n')[0], n,
        r['aquatic_score'], r['dev_score']))
print()
print('Cluster purity for focal orders:')
for order, sp in [('Anseriformes','Anas platyrhynchos'),
                   ('Galliformes','Gallus gallus'),
                   ('Columbiformes','Columba livia')]:
    expected_cl = focal_sp[sp]['cluster']
    n_order = (df['Order1'] == order).sum()
    n_match = ((df['Order1'] == order) & (df['cluster'] == expected_cl)).sum()
    print('  %s: %d/%d = %.1f%% in expected cluster' % (
        order, n_match, n_order, 100*n_match/n_order))
