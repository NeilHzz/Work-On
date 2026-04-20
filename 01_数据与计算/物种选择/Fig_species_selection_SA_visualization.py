"""
Science Advances 格式 — 物种选择双图
Panel A (Fig_species_selection_scatter.png): 3D k-means scatter
Panel B (Fig_species_selection_phylo.png):   Phylogenetic tree + heatmap

数据源: analysis_data.xlsx (pre-computed AVONET scores)
字体: Times New Roman (SA requirement)
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
matplotlib.rcParams["font.size"] = 10
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as _mcolors
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# ─────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR    = r"D:\system_folder\Desktop\Work On\02_可视化\Sci_Adv_Figure"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_A = os.path.join(OUT_DIR, "Fig_species_selection_scatter.png")
OUT_B = os.path.join(OUT_DIR, "Fig_species_selection_phylo.png")

# ─────────────────────────────────────────────────────────────
# Load pre-computed data
# ─────────────────────────────────────────────────────────────
XLSX = os.path.join(SCRIPT_DIR, "analysis_data.xlsx")
df = pd.read_excel(XLSX, sheet_name="AVONET_species_scores", engine="openpyxl")
# Columns: Species, Order, Family, Lifestyle, Habitat,
#          aquatic_score, dev_score, discordance_score, cluster

# Re-fit k-means to get consistent cluster assignments
X2 = df[['aquatic_score', 'dev_score']].values
km3 = KMeans(n_clusters=3, random_state=42, n_init=100, max_iter=500)
df['cluster'] = km3.fit_predict(X2)
sc3 = silhouette_score(X2, df['cluster'])

# Identify focal species
focal_names = ['Anas platyrhynchos', 'Columba livia', 'Gallus gallus']
focal_rows = {sp: df[df['Species'] == sp].iloc[0] for sp in focal_names}

anas_cl = focal_rows['Anas platyrhynchos']['cluster']
col_cl  = focal_rows['Columba livia']['cluster']
gal_cl  = focal_rows['Gallus gallus']['cluster']

CL_COLORS = {anas_cl: '#7895C1', gal_cl: '#B54664', col_cl: '#F0C284'}

focal_cfg = {
    'Anas platyrhynchos': ('Anas',    '#7895C1', 'o'),
    'Columba livia':      ('Columba', '#F0C284', 's'),
    'Gallus gallus':      ('Gallus',  '#B54664', '^'),
}

ORDER_COLORS = {
    'Anseriformes': '#7895C1', 'Galliformes': '#B54664', 'Columbiformes': '#F0C284',
    'Charadriiformes': '#70A850', 'Procellariiformes': '#4A7BB5', 'Suliformes': '#5B9DC2',
    'Pelecaniformes': '#B07840', 'Gaviiformes': '#3D6E99', 'Podicipediformes': '#74B9DC',
    'Sphenisciformes': '#3D7A7A', 'Phoenicopteriformes': '#D47A9A',
    'Gruiformes': '#D48A40', 'Tinamiformes': '#D47A5A', 'Otidiformes': '#A06030',
    'Struthioniformes': '#A04455', 'Rheiformes': '#88BB55', 'Casuariiformes': '#4A9955',
    'Apterygiformes': '#8855AA', 'Pterocliformes': '#C88840', 'Mesitornithiformes': '#5DAA55',
    'Cariamiformes': '#BB66CC', 'Eurypygiformes': '#55BB99',
    'Passeriformes': '#8855AA', 'Psittaciformes': '#44AA77', 'Apodiformes': '#CC8833',
    'Piciformes': '#3A8868', 'Coraciiformes': '#9A7540', 'Cuculiformes': '#6A9A50',
    'Caprimulgiformes': '#5A9050', 'Strigiformes': '#6655AA', 'Accipitriformes': '#7A7025',
    'Cathartiformes': '#5A8840', 'Falconiformes': '#907A40', 'Bucerotiformes': '#2D9060',
    'Trogoniformes': '#44AAAA', 'Musophagiformes': '#88AA44', 'Ciconiiformes': '#4A8855',
    'Phaethontiformes': '#BB6688', 'Coliiformes': '#9933BB', 'Opisthocomiformes': '#99BB33',
    'Leptosomiformes': '#8A7240',
}

# ─────────────────────────────────────────────────────────────
# Panel A — 3D scatter
# ─────────────────────────────────────────────────────────────
rng = np.random.default_rng(0)
jitter_dev = rng.normal(0, 0.018, len(df))
jitter_aq  = rng.normal(0, 0.010, len(df))
jitter_pc2 = rng.normal(0, 0.010, len(df))
df = df.copy()
df['dev_jit'] = (df['dev_score']        + jitter_dev).clip(-0.05, 1.05)
df['aq_jit']  = (df['aquatic_score']    + jitter_aq).clip(-0.05, 1.05)
df['pc2_jit'] = (df['discordance_score'] + jitter_pc2).clip(-0.05, 1.05)

_focal_orders = {'Anseriformes', 'Galliformes', 'Columbiformes'}
_focal_set = set(focal_names)
_non_focal_mask = ~df['Species'].isin(_focal_set)

fig_a = plt.figure(figsize=(10, 10))
ax1 = fig_a.add_axes([0.05, 0.05, 0.9, 0.9], projection='3d')

all_orders_sorted = (
    [o for o in df['Order'].unique() if o not in _focal_orders]
    + list(_focal_orders)
)

for order in all_orders_sorted:
    mask = (df['Order'] == order) & _non_focal_mask
    if not mask.any():
        continue
    color = ORDER_COLORS.get(order, '#AAAAAA')
    is_focal = order in _focal_orders
    ax1.scatter(df.loc[mask, 'aq_jit'],
                df.loc[mask, 'pc2_jit'],
                df.loc[mask, 'dev_jit'],
                c=color,
                alpha=0.65 if is_focal else 0.25,
                s=10 if is_focal else 5,
                linewidths=0, depthshade=True,
                zorder=3 if is_focal else 2)

ax1.xaxis.pane.fill = ax1.yaxis.pane.fill = ax1.zaxis.pane.fill = False
for _pane in [ax1.xaxis.pane, ax1.yaxis.pane, ax1.zaxis.pane]:
    _pane.set_facecolor('white')
    _pane.set_edgecolor('#BBBBBB')
ax1.grid(False)

# Cluster zone boundaries
_centroids = km3.cluster_centers_
_aq_lo_cent = max(_centroids[gal_cl, 0], _centroids[col_cl, 0])
_aq_hi_cent = _centroids[anas_cl, 0]
_aq_lo  = _aq_lo_cent + (_aq_hi_cent - _aq_lo_cent) / 3.0
_aq_hi  = _aq_lo_cent + (_aq_hi_cent - _aq_lo_cent) * 2.0 / 3.0
_dev_lo, _dev_hi = 0.2, 0.7
_disc_lo, _disc_hi = 1/3.0, 2/3.0
_gray = '#C4C4C4'; _alpha = 0.20

for (x0, x1, z0, z1), disc in [
    ((0, _aq_lo, 0, _dev_lo), _disc_lo),
    ((_aq_hi, 1.0, 0, _dev_lo), _disc_lo),
    ((0, _aq_lo, _dev_hi, 1.05), _disc_lo),
]:
    ax1.add_collection3d(Poly3DCollection(
        [[(x0, 0, z0), (x1, 0, z0), (x1, disc, z0), (x0, disc, z0)]],
        facecolors=_gray, edgecolors='none', alpha=_alpha, zorder=0))
    ax1.add_collection3d(Poly3DCollection(
        [[(x0, disc, z0), (x1, disc, z0), (x1, disc, z1), (x0, disc, z1)]],
        facecolors=_gray, edgecolors='none', alpha=_alpha, zorder=0))

ax1.text2D(0.05, 0.05, f'k-means k=3\nSilhouette = {sc3:.3f}',
           transform=ax1.transAxes, ha='left', va='bottom', fontsize=8.5,
           color='#444444',
           bbox=dict(fc='white', ec='#AAAAAA', alpha=0.80, pad=3, lw=0.8))

ax1.set_xlim(0, 1); ax1.set_ylim(1, 0); ax1.set_zlim(-0.05, 1.05)
ax1.set_xlabel('Aquatic association (PC1)', fontsize=10, labelpad=10)
ax1.set_ylabel('Lifestyle–habitat discordance', fontsize=10, labelpad=10)
ax1.set_zlabel('Developmental mode', fontsize=10, labelpad=10)
ax1.view_init(elev=25, azim=40)

# Legend
legend_groups = [
    ('─── Focal species ───────', '#FFFFFF'),
    ('Anseriformes  (Anas)',    '#7895C1'),
    ('Galliformes  (Gallus)',   '#B54664'),
    ('Columbiformes  (Columba)', '#F0C284'),
    ('─── Aquatic ─────────────', '#FFFFFF'),
    ('Charadriiformes',   '#70A850'), ('Procellariiformes', '#4A7BB5'),
    ('Pelecaniformes',    '#B07840'), ('Suliformes',        '#5B9DC2'),
    ('Podicipediformes',  '#74B9DC'), ('Sphenisciformes',   '#3D7A7A'),
    ('Gaviiformes',       '#3D6E99'), ('Phoenicopterif.',   '#D47A9A'),
    ('─── Precocial ───────────', '#FFFFFF'),
    ('Gruiformes',        '#D48A40'), ('Tinamiformes',      '#D47A5A'),
    ('Otidiformes',       '#A06030'), ('Struthionif.',      '#A04455'),
    ('─── Altricial ───────────', '#FFFFFF'),
    ('Passeriformes',     '#8855AA'), ('Psittaciformes',    '#44AA77'),
    ('Apodiformes',       '#CC8833'), ('Piciformes',        '#3A8868'),
    ('Accipitriformes',   '#7A7025'), ('Strigiformes',      '#6655AA'),
    ('Falconiformes',     '#907A40'), ('Coraciiformes',     '#9A7540'),
    ('Cuculiformes',      '#6A9A50'), ('Bucerotiformes',    '#2D9060'),
]
handles = []
for lbl, col in legend_groups:
    if lbl.startswith('───'):
        handles.append(mpatches.Patch(fc='none', ec='none', label=lbl))
    else:
        handles.append(mpatches.Patch(fc=col, ec='none', label=lbl, linewidth=0))

ax1.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.05, 1.0),
           fontsize=7.5, framealpha=0.93, ncol=1,
           handlelength=0.9, handleheight=0.85,
           borderpad=0.5, labelspacing=0.25,
           title='Taxonomic order', title_fontsize=8.0)

# Focal labels overlay
fig_a.canvas.draw()
_pos = ax1.get_position()
_ax_ov = fig_a.add_axes([_pos.x0, _pos.y0, _pos.width, _pos.height],
                         frameon=False, label='_overlay',
                         zorder=ax1.get_zorder() + 10)
_ax_ov.set_xlim(0, 1); _ax_ov.set_ylim(0, 1); _ax_ov.axis('off')

_lbl_pos2d = {
    'Anas platyrhynchos': (0.50, 0.13),
    'Gallus gallus':      (0.80, 0.28),
    'Columba livia':      (0.90, 0.55),
}
for sp, (short, col, mrkr) in focal_cfg.items():
    r = focal_rows[sp]
    x0 = r['aquatic_score']
    y0 = r['discordance_score']
    z0 = r['dev_score']
    x2d, y2d, _ = proj3d.proj_transform(x0, y0, z0, ax1.get_proj())
    x_px, y_px = ax1.transData.transform((x2d, y2d))
    x_ax = (x_px - ax1.bbox.x0) / ax1.bbox.width
    y_ax = (y_px - ax1.bbox.y0) / ax1.bbox.height
    _ax_ov.plot([x_ax], [y_ax], mrkr, markersize=9,
                markerfacecolor='white', markeredgecolor=col,
                markeredgewidth=2.5, zorder=500, clip_on=False)
    xf, yf = _lbl_pos2d.get(sp, (0.5, 0.5))
    ax1.text2D(xf, yf, short, transform=ax1.transAxes,
               fontsize=11, fontweight='bold', fontstyle='italic', color=col,
               ha='center', va='bottom', clip_on=False,
               bbox=dict(fc='white', ec=col, lw=1.5, alpha=0.92, boxstyle='round,pad=0.3'))

plt.savefig(OUT_A, dpi=180, bbox_inches='tight')
plt.close('all')
print(f'[OK] Panel A: {OUT_A}')

# ─────────────────────────────────────────────────────────────
# Panel B — Phylogenetic tree + heatmap
# ─────────────────────────────────────────────────────────────
_order_means = df.groupby('Order')[['aquatic_score', 'discordance_score', 'dev_score']].mean()
_order_n     = df.groupby('Order').size()

# Build tree
def _tip(name): return [name, []]
def _nd(ch):    return ['', ch]

_TREE = _nd([
    _nd([
        _tip('Tinamiformes'),
        _nd([_tip('Struthioniformes'),
             _nd([_tip('Rheiformes'),
                  _nd([_tip('Casuariiformes'), _tip('Apterygiformes')])])])]),
    _nd([_tip('Anseriformes'), _tip('Galliformes')]),
    _nd([
        _nd([_tip('Columbiformes'),
             _nd([_tip('Pterocliformes'), _tip('Mesitornithiformes')])]),
        _nd([_tip('Phoenicopteriformes'), _tip('Podicipediformes')]),
        _nd([
            _nd([_tip('Gruiformes'), _tip('Charadriiformes')]),
            _nd([
                _tip('Gaviiformes'),
                _nd([_tip('Sphenisciformes'),
                     _nd([_tip('Procellariiformes'),
                          _nd([_tip('Ciconiiformes'),
                               _nd([_tip('Phaethontiformes'),
                                    _nd([_tip('Suliformes'), _tip('Pelecaniformes')])])])])])]),
            _nd([
                _nd([_tip('Otidiformes'),
                     _nd([_tip('Cuculiformes'), _tip('Musophagiformes')])]),
                _tip('Opisthocomiformes'),
                _nd([_tip('Caprimulgiformes'), _tip('Apodiformes')]),
                _nd([
                    _nd([_tip('Coraciiformes'),
                         _nd([_tip('Trogoniformes'),
                              _nd([_tip('Leptosomiformes'),
                                   _nd([_tip('Bucerotiformes'), _tip('Piciformes')])])])]),
                    _nd([_tip('Eurypygiformes'),
                         _nd([_tip('Cariamiformes'),
                              _nd([_nd([_tip('Accipitriformes'), _tip('Cathartiformes')]),
                                   _nd([_tip('Strigiformes'), _tip('Coliiformes')])])])]),
                    _nd([_tip('Falconiformes'),
                         _nd([_tip('Psittaciformes'), _tip('Passeriformes')])])
                ])
            ])
        ])
    ])
])

_tc = [0]
def _apos(n, d=0):
    n.append({})
    n[2]['d'] = d
    if not n[1]:
        n[2]['y'] = _tc[0]; n[2]['x'] = d; _tc[0] += 1
    else:
        for c in n[1]: _apos(c, d + 1)
        ys = [c[2]['y'] for c in n[1]]
        n[2]['y'] = (min(ys) + max(ys)) / 2; n[2]['x'] = d
_apos(_TREE)
_NT = _tc[0]

def _mxd(n): return n[2]['d'] if not n[1] else max(_mxd(c) for c in n[1])
_MD = _mxd(_TREE)
def _ftx(n):
    if not n[1]: n[2]['x'] = _MD
    else:
        for c in n[1]: _ftx(c)
_ftx(_TREE)

def _cltips(n, lst):
    if not n[1]: lst.append((n[0], n[2]['x'], n[2]['y']))
    else:
        for c in n[1]: _cltips(c, lst)
_tl = []; _cltips(_TREE, _tl)

fig_b, ax2 = plt.subplots(1, 1, figsize=(12, 16))
fig_b.patch.set_facecolor('white')
ax2.set_facecolor('white')

def _dbr(n, ax):
    if n[1]:
        ys = [c[2]['y'] for c in n[1]]
        ax.plot([n[2]['x']]*2, [min(ys), max(ys)],
                color='#555555', lw=0.9, solid_capstyle='round', zorder=2)
        for c in n[1]:
            ax.plot([n[2]['x'], c[2]['x']], [c[2]['y']]*2,
                    color='#555555', lw=0.9, solid_capstyle='round', zorder=2)
            _dbr(c, ax)
_dbr(_TREE, ax2)

_cm_aq = _mcolors.LinearSegmentedColormap.from_list('aq', ['#EEF4FF', '#1A4F9A'])
_cm_dv = _mcolors.LinearSegmentedColormap.from_list('dv', ['#FFF5EB', '#B03010'])
_cm_ds = _mcolors.LinearSegmentedColormap.from_list('ds', ['#F0FFF8', '#146B50'])

_BW = 1.40; _BH = 0.72; _BG = 0.20
_BS = _MD + 0.55

for _i, (_lbl, _col) in enumerate([('Aquatic (X)', '#1A4F9A'),
                                     ('Dev. mode (Z)', '#B03010'),
                                     ('Discord. (Y)', '#146B50')]):
    ax2.text(_BS + _i*(_BW + _BG) + _BW/2, _NT + 0.3, _lbl,
             ha='center', va='bottom', fontsize=8.5, color=_col, fontweight='bold',
             rotation=90, clip_on=False)

_FOCAL_O = {'Anseriformes', 'Galliformes', 'Columbiformes'}
for (_order, _tx, _ty) in _tl:
    if _order not in _order_means.index:
        ax2.text(_BS + 3*(_BW + _BG) + 0.25, _ty, _order, va='center', ha='left',
                 fontsize=8, color='#AAAAAA', fontstyle='italic')
        continue
    _aq  = float(_order_means.loc[_order, 'aquatic_score'])
    _dev = float(_order_means.loc[_order, 'dev_score'])
    _dis = float(_order_means.loc[_order, 'discordance_score'])
    _n_o = int(_order_n[_order])
    for _i, (_val, _cm) in enumerate([(_aq, _cm_aq), (_dev, _cm_dv), (_dis, _cm_ds)]):
        ax2.add_patch(mpatches.FancyBboxPatch(
            (_BS + _i*(_BW + _BG), _ty - _BH/2), _BW, _BH,
            boxstyle='square,pad=0', fc=_cm(_val), ec='none', zorder=3))
    _oc = ORDER_COLORS.get(_order, '#555555')
    _wt = 'bold' if _order in _FOCAL_O else 'normal'
    ax2.text(_BS + 3*(_BW + _BG) + 0.25, _ty,
             f'{_order}  n={_n_o}',
             va='center', ha='left', fontsize=8.5, color=_oc, fontweight=_wt)

# Gradient scales
for _i, (_cm, _col) in enumerate([(_cm_aq, '#1A4F9A'), (_cm_dv, '#B03010'), (_cm_ds, '#146B50')]):
    _xb = _BS + _i*(_BW + _BG)
    for _j in range(20):
        _v = _j / 19
        ax2.add_patch(mpatches.FancyBboxPatch(
            (_xb + _j*_BW/20, -1.8), _BW/20, 0.45,
            boxstyle='square,pad=0', fc=_cm(_v), ec='none', zorder=3))
    ax2.text(_xb,      -2.35, '0', ha='left',  va='top', fontsize=6.5, color=_col)
    ax2.text(_xb+_BW,  -2.35, '1', ha='right', va='top', fontsize=6.5, color=_col)

# Clade brackets
_TY = {nm: ty for nm, _, ty in _tl}
_CLADES_B = [
    ({'Tinamiformes','Struthioniformes','Rheiformes','Casuariiformes','Apterygiformes'},
     'Palaeognathae', '#777777'),
    ({'Anseriformes','Galliformes'}, 'Galloanserae', '#777777'),
    ({'Gaviiformes','Sphenisciformes','Procellariiformes','Ciconiiformes',
      'Phaethontiformes','Suliformes','Pelecaniformes'}, 'Aequornithia', '#3A6FA5'),
    ({'Coraciiformes','Trogoniformes','Leptosomiformes','Bucerotiformes','Piciformes'},
     'Coraciimorphae', '#A0701A'),
    ({'Eurypygiformes','Cariamiformes','Accipitriformes','Cathartiformes',
      'Strigiformes','Coliiformes'}, 'Afroaves', '#557030'),
    ({'Falconiformes','Psittaciformes','Passeriformes'}, 'Australaves', '#7048A0'),
]
for _ts, _lbl, _col in _CLADES_B:
    _ys = [_TY[t] for t in _ts if t in _TY]
    if not _ys: continue
    _ylo, _yhi = min(_ys), max(_ys)
    ax2.plot([-0.35]*2, [_ylo - 0.3, _yhi + 0.3],
             lw=2.5, color=_col, solid_capstyle='butt', alpha=0.8, zorder=1)
    ax2.text(-0.45, (_ylo + _yhi)/2, _lbl,
             ha='right', va='center', rotation=90,
             fontsize=7, color=_col, fontweight='bold')

ax2.set_xlim(-1.8, _MD + 18)
ax2.set_ylim(-3, _NT + 5)
ax2.axis('off')

plt.savefig(OUT_B, dpi=180, bbox_inches='tight', facecolor='white')
plt.close('all')
print(f'[OK] Panel B: {OUT_B}')
print(f'\nSilhouette score: {sc3:.4f}')
print(f'Total species: {len(df)}')
