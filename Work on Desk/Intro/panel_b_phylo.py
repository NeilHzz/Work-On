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
# 1. Load AVONET (Tobias et al. 2022) — BirdLife taxonomy
# ============================================================
avonet = pd.read_excel(
    r'd:\system_folder\Desktop\Work on Desk\Intro\AVONET_Supp1.xlsx',
    sheet_name='AVONET1_BirdLife', engine='openpyxl')

# ---- Y axis: developmental mode (Starck & Ricklefs 1998) ----
# 0 = fully precocial, 1 = fully altricial; order-level assignment
dev_map = {
    # ratites / paleognaths — fully precocial
    'Struthioniformes': 0.0, 'Rheiformes': 0.0, 'Casuariiformes': 0.0,
    'Apterygiformes': 0.0,   'Tinamiformes': 0.0,
    # waterfowl / gallinaceous — fully precocial
    'Anseriformes': 0.0, 'Galliformes': 0.0,
    # transitional precocial
    'Otidiformes': 0.0,  'Mesitornithiformes': 0.2,
    'Charadriiformes': 0.2, 'Gruiformes': 0.2, 'Pterocliformes': 0.1,
    'Phoenicopteriformes': 0.3, 'Gaviiformes': 0.3,
    'Podicipediformes': 0.4,   'Sphenisciformes': 0.5,
    # semi-altricial (seabirds, raptors)
    'Procellariiformes': 0.7, 'Suliformes': 0.7, 'Pelecaniformes': 0.7,
    'Ciconiiformes': 0.7,     'Accipitriformes': 0.7, 'Falconiformes': 0.7,
    'Cathartiformes': 0.7,
    'Cariamiformes': 0.6, 'Eurypygiformes': 0.6, 'Phaethontiformes': 0.6,
    # fully altricial
    'Strigiformes': 0.9,   'Caprimulgiformes': 0.8, 'Apodiformes': 1.0,
    'Opisthocomiformes': 0.9, 'Trogoniformes': 1.0,  'Coraciiformes': 1.0,
    'Bucerotiformes': 1.0, 'Piciformes': 1.0,       'Musophagiformes': 1.0,
    'Coliiformes': 1.0,    'Cuculiformes': 0.9,      'Columbiformes': 0.75,
    'Psittaciformes': 1.0, 'Leptosomiformes': 1.0,   'Passeriformes': 1.0,
}
avonet['dev_score'] = avonet['Order1'].map(dev_map)

# ---- X axis: PCA on three AVONET ecological fields ----
# PC1 = aquatic association axis  → X in 3D scatter
# PC2 = secondary ecological variation → Y in 3D scatter
# dev_score = developmental mode       → Z in 3D scatter

lifestyle_w = {
    'Aquatic':     1.00, 'Generalist':  0.40, 'Terrestrial': 0.15,
    'Insessorial': 0.05, 'Aerial':      0.00,
}
habitat_w = {
    'Marine': 1.00, 'Wetland': 0.95, 'Riverine': 0.85, 'Coastal': 0.75,
    'Grassland': 0.18, 'Desert': 0.10, 'Rock': 0.12,
    'Human Modified': 0.15, 'Shrubland': 0.12, 'Woodland': 0.08, 'Forest': 0.05,
}
trophic_w = {
    'Herbivore aquatic': 1.00, 'Aquatic predator': 0.95,
    'Omnivore': 0.30, 'Invertivore': 0.20, 'Vertivore': 0.10,
    'Scavenger': 0.15, 'Granivore': 0.10, 'Frugivore': 0.08,
    'Herbivore terrestrial': 0.05, 'Nectarivore': 0.05,
}
avonet['ls_enc']  = avonet['Primary.Lifestyle'].map(lifestyle_w).fillna(0.25)
avonet['hab_enc'] = avonet['Habitat'].map(habitat_w).fillna(0.15)
avonet['tr_enc']  = avonet['Trophic.Niche'].map(trophic_w).fillna(0.15)

# ---- Assemble modelling dataframe ----
df = avonet[['Species1', 'Order1', 'Family1', 'ls_enc', 'hab_enc', 'tr_enc', 'dev_score',
             'Primary.Lifestyle', 'Habitat', 'Trophic.Niche']].dropna().copy()

# PCA: standardise → extract PC1 (X) and PC2 (Y)
_X3  = StandardScaler().fit_transform(df[['ls_enc', 'hab_enc', 'tr_enc']].values)
_pca = PCA(n_components=3, random_state=42)
_pcs = _pca.fit_transform(_X3)
print('PCA explained variance: %s' % _pca.explained_variance_ratio_.round(4))
print('PC1 loadings (lifestyle, habitat, trophic): %s' % _pca.components_[0].round(4))
print('PC2 loadings (lifestyle, habitat, trophic): %s' % _pca.components_[1].round(4))

# Orient PC1 so Aquatic species score highest (rightmost on X axis)
_anas_idx = df.index.get_loc(df[df['Species1'] == 'Anas platyrhynchos'].index[0])
_gal_idx  = df.index.get_loc(df[df['Species1'] == 'Gallus gallus'].index[0])
_flip1 = -1 if _pcs[_anas_idx, 0] < _pcs[_gal_idx, 0] else 1
_pc1 = _pcs[:, 0] * _flip1
_pc2 = _pcs[:, 1]

# X = PC1 (aquatic association, normalised)
# Y = |ls_enc - mean(hab_enc, tr_enc)| normalised → lifestyle vs habitat/trophic discordance
df['aquatic_score'] = (_pc1 - _pc1.min()) / (_pc1.max() - _pc1.min())
_discord = np.abs(df['ls_enc'].values - (df['hab_enc'].values + df['tr_enc'].values) / 2.0)
df['pc2_score'] = (_discord - _discord.min()) / (_discord.max() - _discord.min())
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

cl_colors = {anas_cl: '#7895C1', gal_cl: '#B54664', col_cl: '#F0C284'}
cl_ec     = {anas_cl: '#4A6080', gal_cl: '#7A1A30', col_cl: '#A07828'}
cl_labels = {
    anas_cl: 'Aquatic foragers\n(n=%d sp.)' % (df['cluster'] == anas_cl).sum(),
    gal_cl:  'Terrestrial precocial\n(n=%d sp.)' % (df['cluster'] == gal_cl).sum(),
    col_cl:  'Terrestrial altricial\n(n=%d sp.)' % (df['cluster'] == col_cl).sum(),
}
focal_cfg = {
    'Anas platyrhynchos': ('Anas',    '#7895C1', 'o', 260),
    'Columba livia':      ('Columba', '#F0C284', 's', 240),
    'Gallus gallus':      ('Gallus',  '#B54664', '^', 240),
}

# ---- Order color palette ----
ORDER_COLORS = {
    # focal — fixed, do not change
    'Anseriformes':        '#7895C1',
    'Galliformes':         '#B54664',
    'Columbiformes':       '#F0C284',
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
fig = plt.figure(figsize=(12, 16))
ax2 = fig.add_axes([0.1, 0.05, 0.8, 0.9])                   # Panel B — phylo

# ============================================================
# Panel B — order-level phylogenetic tree (Prum et al. 2015)
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


# ============================================================
# Panel B — order-level phylogenetic tree (Prum et al. 2015)
# ============================================================
import matplotlib.colors as _mcolors

# ---- per-order mean trait values ----
_order_means = df.groupby('Order1')[['aquatic_score', 'pc2_score', 'dev_score']].mean()
_order_n     = df.groupby('Order1').size()

# ---- nested-list tree (Prum et al. 2015; Jarvis et al. 2014) ----
# Format: [name, [children]] — tips have empty children list
def _tip(name): return [name, []]
def _nd(ch):    return ['',   ch]

_TREE = _nd([
    _nd([                                    # Palaeognathae
        _tip('Tinamiformes'),
        _nd([_tip('Struthioniformes'),
             _nd([_tip('Rheiformes'),
                  _nd([_tip('Casuariiformes'), _tip('Apterygiformes')])])])]),
    _nd([_tip('Anseriformes'), _tip('Galliformes')]),   # Galloanserae
    _nd([                                    # Neoaves
        _nd([_tip('Columbiformes'),           # Columbimorphae
             _nd([_tip('Pterocliformes'), _tip('Mesitornithiformes')])]),
        _nd([_tip('Phoenicopteriformes'), _tip('Podicipediformes')]),  # Mirandornithes
        _nd([
            _nd([_tip('Gruiformes'), _tip('Charadriiformes')]),        # Gruae
            _nd([                                                        # Aequornithia
                _tip('Gaviiformes'),
                _nd([_tip('Sphenisciformes'),
                     _nd([_tip('Procellariiformes'),
                          _nd([_tip('Ciconiiformes'),
                               _nd([_tip('Phaethontiformes'),
                                    _nd([_tip('Suliformes'),
                                         _tip('Pelecaniformes')])])])])])]),
            _nd([                                                        # Inopinaves
                _nd([_tip('Otidiformes'),
                     _nd([_tip('Cuculiformes'), _tip('Musophagiformes')])]),
                _tip('Opisthocomiformes'),
                _nd([_tip('Caprimulgiformes'), _tip('Apodiformes')]),   # Strisores
                _nd([
                    _nd([_tip('Coraciiformes'),                         # Coraciimorphae
                         _nd([_tip('Trogoniformes'),
                              _nd([_tip('Leptosomiformes'),
                                   _nd([_tip('Bucerotiformes'),
                                        _tip('Piciformes')])])])]),
                    _nd([_tip('Eurypygiformes'),                        # Afroaves
                         _nd([_tip('Cariamiformes'),
                              _nd([_nd([_tip('Accipitriformes'),
                                        _tip('Cathartiformes')]),
                                   _nd([_tip('Strigiformes'),
                                        _tip('Coliiformes')])])])]),
                    _nd([_tip('Falconiformes'),                         # Australaves
                         _nd([_tip('Psittaciformes'), _tip('Passeriformes')])])
                ])
            ])
        ])
    ])
])

# ---- assign y-positions (tips) and depth (x) ----
_tc = [0]
def _apos(n, d=0):
    n.append({})
    n[2]['d'] = d
    if not n[1]:
        n[2]['y'] = _tc[0]; n[2]['x'] = d; _tc[0] += 1
    else:
        for c in n[1]: _apos(c, d+1)
        ys = [c[2]['y'] for c in n[1]]
        n[2]['y'] = (min(ys)+max(ys))/2; n[2]['x'] = d
_apos(_TREE)
_NT = _tc[0]   # number of tips

def _mxd(n): return n[2]['d'] if not n[1] else max(_mxd(c) for c in n[1])
_MD = _mxd(_TREE)   # max depth
def _ftx(n):         # align all tips to max depth
    if not n[1]: n[2]['x'] = _MD
    else:
        for c in n[1]: _ftx(c)
_ftx(_TREE)

# ---- collect tips ----
def _cltips(n, lst):
    if not n[1]: lst.append((n[0], n[2]['x'], n[2]['y']))
    else:
        for c in n[1]: _cltips(c, lst)
_tl = []; _cltips(_TREE, _tl)

# ---- draw tree branches ----
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

# ---- colormaps for 3 axes ----
_cm_aq = _mcolors.LinearSegmentedColormap.from_list('aq', ['#EEF4FF', '#1A4F9A'])
_cm_dv = _mcolors.LinearSegmentedColormap.from_list('dv', ['#FFF5EB', '#B03010'])
_cm_ds = _mcolors.LinearSegmentedColormap.from_list('ds', ['#F0FFF8', '#146B50'])

_BW = 1.40; _BH = 0.72; _BG = 0.20   # box width / height / gap
_BS = _MD + 0.55                       # x-start of colored boxes

# ---- column headers (vertical) ----
for _i, (_lbl, _col) in enumerate([('Aquatic (X)', '#1A4F9A'),
                                     ('Dev. mode (Z)', '#B03010'),
                                     ('Discord. (Y)', '#146B50')]):
    ax2.text(_BS + _i*(_BW+_BG) + _BW/2, _NT + 0.3, _lbl,
             ha='center', va='bottom', fontsize=8.5, color=_col, fontweight='bold',
             rotation=90, clip_on=False)

# ---- tip boxes + order name labels ----
_FOCAL_O = {'Anseriformes', 'Galliformes', 'Columbiformes'}
for (_order, _tx, _ty) in _tl:
    if _order not in _order_means.index:
        ax2.text(_BS+3*(_BW+_BG)+0.25, _ty, _order, va='center', ha='left',
                 fontsize=8, color='#AAAAAA', fontstyle='italic')
        continue
    _aq  = float(_order_means.loc[_order, 'aquatic_score'])
    _dev = float(_order_means.loc[_order, 'dev_score'])
    _dis = float(_order_means.loc[_order, 'pc2_score'])
    _n_o = int(_order_n[_order])
    for _i, (_val, _cm) in enumerate([(_aq, _cm_aq), (_dev, _cm_dv), (_dis, _cm_ds)]):
        ax2.add_patch(mpatches.FancyBboxPatch(
            (_BS+_i*(_BW+_BG), _ty-_BH/2), _BW, _BH,
            boxstyle='square,pad=0', fc=_cm(_val), ec='none', zorder=3))
    _oc = ORDER_COLORS.get(_order, '#555555')
    _wt = 'bold' if _order in _FOCAL_O else 'normal'
    ax2.text(_BS+3*(_BW+_BG)+0.25, _ty,
             '%s  n=%d' % (_order, _n_o),
             va='center', ha='left', fontsize=8.5, color=_oc, fontweight=_wt)

# ---- gradient scale bars (below tips) ----
for _i, (_cm, _col) in enumerate([(_cm_aq, '#1A4F9A'), (_cm_dv, '#B03010'), (_cm_ds, '#146B50')]):
    _xb = _BS + _i*(_BW+_BG)
    for _j in range(20):
        _v = _j / 19
        ax2.add_patch(mpatches.FancyBboxPatch(
            (_xb+_j*_BW/20, -1.8), _BW/20, 0.45,
            boxstyle='square,pad=0', fc=_cm(_v), ec='none', zorder=3))
    ax2.text(_xb,        -2.35, '0', ha='left',  va='top', fontsize=6.5, color=_col)
    ax2.text(_xb+_BW,    -2.35, '1', ha='right', va='top', fontsize=6.5, color=_col)

# ---- clade bracket lines (left of root) ----
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
    ax2.plot([-0.35]*2, [_ylo-0.3, _yhi+0.3],
             lw=2.5, color=_col, solid_capstyle='butt', alpha=0.8, zorder=1)
    ax2.text(-0.45, (_ylo+_yhi)/2, _lbl,
             ha='right', va='center', rotation=90,
             fontsize=7, color=_col, fontweight='bold')

ax2.set_xlim(-1.8, _MD + 18)
ax2.set_ylim(-3, _NT + 5)
ax2.axis('off')

# fig.suptitle(
#     'Unsupervised k-means clustering (k=3, silhouette=%.3f) separates waterbird / '
#     'terrestrial-precocial / terrestrial-altricial functional groups\n'
#     'G. gallus, A. platyrhynchos, and C. livia each represent one cluster  |  '
#     'dots colored by taxonomic order  |  %d bird species  |  '
#     'AVONET: Tobias et al. (2022)' % (sc3, len(df)),
#     fontsize=11, fontweight='bold', y=1.01)

out = 'panel_b_phylo.png'
# Focal species text labels
plt.savefig(out, dpi=160, bbox_inches='tight')
print('Saved:', out)

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
