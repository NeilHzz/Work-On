import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

work_dir = Path(r'D:/system_folder/Desktop/Work On/01_数据与计算/Ortho/Expansions Contractions Results')

SPECIES_COLORS = {'Gallus': '#B54664', 'Anas': '#7895C1', 'Pigeon': '#F0C284'}
INTERACTION_COLORS = {'Expansion': '#D56661', 'Contraction': '#4D9A94'}
GO_TYPE_COLORS = {'P': '#8DA16B', 'C': '#9283AD', 'F': '#A69C95'}

species_names = ['Gallus', 'Anas', 'Pigeon']
interactions = ['Expansion', 'Contraction']

enrichment_files = {
    'Gallus_Expansions': work_dir / 'Gallus' / 'E_enrichment.txt',
    'Gallus_Contractions': work_dir / 'Gallus' / 'C_enrichment.txt',
    'Anas_Expansions': work_dir / 'Anas' / 'E_enrichment.txt',
    'Anas_Contractions': work_dir / 'Anas' / 'C_enrichment.txt',
    'Pigeon_Expansions': work_dir / 'Pigeon' / 'E_enrichment.txt',
    'Pigeon_Contractions': work_dir / 'Pigeon' / 'C_enrichment.txt',
}

def load_enrichment_data(filepath):
    enriched_gos = []
    if not filepath.exists(): return enriched_gos
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split('\t')
            if len(parts) >= 5:
                category = parts[3]
                go_type = 'P' if category == 'biological_process' else ('C' if category == 'cellular_component' else 'F')
                p_value = float(parts[4])
                enriched_gos.append({
                    'go_id': parts[0],
                    'protein_count': int(parts[1]),
                    'description': parts[2],
                    'go_type': go_type,
                    'p_value': p_value
                })
    return enriched_gos

all_gos_dict = {}
inter_sp_weight = {}
sp_go_inter_weight = {}

for sp in species_names:
    for inter in interactions:
        dataset_name = f"{sp}_{inter}s"
        enrich_file = enrichment_files.get(dataset_name)
        if enrich_file and enrich_file.exists():
            gos = load_enrichment_data(enrich_file)
            for go_item in gos:
                raw_desc = go_item['description']
                clean_desc = raw_desc.split(':')[-1].strip() if ':' in raw_desc else raw_desc
                go_t = go_item['go_type']
                pval = go_item['p_value']
                count = go_item['protein_count']
                
                if clean_desc not in all_gos_dict:
                    all_gos_dict[clean_desc] = {'p_value': pval, 'count': 0, 'go_type': go_t}
                else:
                    all_gos_dict[clean_desc]['p_value'] = min(all_gos_dict[clean_desc]['p_value'], pval)
                all_gos_dict[clean_desc]['count'] += count
                
                # 流动连接计算完美地总和了连线！
                inter_sp_weight[(inter, sp)] = inter_sp_weight.get((inter, sp), 0) + count
                sp_go_inter_weight[(inter, sp, clean_desc)] = sp_go_inter_weight.get((inter, sp, clean_desc), 0) + count



# ------------------ 注入的缩放 ------------------
family_changes = {
    ('Expansion', 'Gallus'): 6,
    ('Contraction', 'Gallus'): 64,
    ('Expansion', 'Anas'): 14,
    ('Contraction', 'Anas'): 30,
    ('Expansion', 'Pigeon'): 75,
    ('Contraction', 'Pigeon'): 8
}

sp_go_inter_weight_scaled = {}
for (i, s), expected_total in family_changes.items():
    orig_sum = sum(v for k, v in sp_go_inter_weight.items() if k[0] == i and k[1] == s)
    if orig_sum > 0:
        for (i_g, s_g, g), orig_c in list(sp_go_inter_weight.items()):
            if i_g == i and s_g == s:
                sp_go_inter_weight_scaled[(i, s, g)] = orig_c / orig_sum * expected_total

sp_go_inter_weight = sp_go_inter_weight_scaled
inter_sp_weight = family_changes

for g in all_gos_dict:
    all_gos_dict[g]['count'] = 0
for (i, s, g), v in sp_go_inter_weight.items():
    all_gos_dict[g]['count'] += v
# ------------------------------------------------------

# 使用形状直接创建自定义Sankey图，以绕开Plotly严格的布局限制
# 确定每个GO term的主要互作和物种，以防止物流线交叉
go_dominant_inter = {}
go_dominant_sp = {}
for (inter_val, sp_val, c_desc), c in sp_go_inter_weight.items():
    if c_desc not in go_dominant_inter:
        go_dominant_inter[c_desc] = {'Contraction': 0, 'Expansion': 0}
    go_dominant_inter[c_desc][inter_val] += c
    
    if c_desc not in go_dominant_sp:
        go_dominant_sp[c_desc] = {'Gallus': 0, 'Anas': 0, 'Pigeon': 0}
    go_dominant_sp[c_desc][sp_val] += c

go_best_i = {g: max(v, key=v.get) for g, v in go_dominant_inter.items()}
go_best_s = {g: max(v, key=v.get) for g, v in go_dominant_sp.items()}

valid_gos = [g for g, d in all_gos_dict.items() if d['count'] > 0]
# 严格排序：收缩(0)/扩展(1)分割以避免交叉，然后P值降序排列以将最小值放在顶部
valid_gos.sort(key=lambda g: -all_gos_dict[g]['p_value'])

W = 900
H = 1000
fig = go.Figure()

# 第一列不再绘制，仅保留两类标签用于第二列左侧小色块占比计算与第二列到第三列连线拆分
r1_interactions = ['Contraction', 'Expansion']

# --- 第二行：物种 ---
r2_gap = 15
r2_species = ['Gallus', 'Anas', 'Pigeon']
r2_counts = {s: sum(c for (it, sp), c in inter_sp_weight.items() if sp == s) for s in r2_species}
r2_total = sum(r2_counts.values())
r2_avail = W - r2_gap * 2
r2_nodes = {}
cx = 20
for s in r2_species:
    w = r2_counts[s] / max(1, r2_total) * r2_avail
    r2_nodes[s] = {'x': cx, 'w': w, 'in': cx, 'out': cx}
    cx += w + r2_gap

# 计算第二列每个物种节点来自第一列各类型的宽度占比（用于左侧色块）
r2_interaction_width = {s: {i: 0.0 for i in r1_interactions} for s in r2_species}
for s in r2_species:
    for i in r1_interactions:
        c = inter_sp_weight.get((i, s), 0)
        r2_interaction_width[s][i] = c / max(1, r2_total) * r2_avail

# --- 第三行：GO目标 ---
r3_N = len(valid_gos)
max_gap_total = W * 0.4
r3_gap = min(15, max_gap_total / max(1, r3_N - 1)) if r3_N > 1 else 0
r3_avail = W - r3_gap * max(1, r3_N - 1)
if r3_avail < W * 0.2: 
    r3_avail = W * 0.2
    r3_gap = (W - r3_avail) / max(1, r3_N - 1)

r3_total = sum(all_gos_dict[g]['count'] for g in valid_gos)
r3_nodes = {}
cx = 20
for g in valid_gos:
    w = all_gos_dict[g]['count'] / max(1, r3_total) * r3_avail
    r3_nodes[g] = {'x': cx, 'w': w, 'in': cx}
    cx += w + r3_gap

# 计算每个GO来自各物种的汇总流量（用于右侧物种色块）
go_species_width = {g: {s: 0.0 for s in r2_species} for g in valid_gos}
for (inter_val, sp_val, g_name), c in sp_go_inter_weight.items():
    if g_name in go_species_width:
        go_species_width[g_name][sp_val] += c / max(1, r3_total) * r3_avail

# 为第三列标签设置最小行间距，并同步移动GO节点，避免文字与节点重叠
min_label_spacing = 26
min_node_gap = 4
if valid_gos:
    adjusted_centers = {}
    prev_center = None
    prev_right = None
    for g in valid_gos:
        c0 = r3_nodes[g]['x'] + r3_nodes[g]['w'] / 2
        half_w = r3_nodes[g]['w'] / 2
        if prev_center is None:
            c_new = c0
        else:
            # 同时满足：标签最小间距 + 节点矩形边界不重叠
            c_new = max(c0, prev_center + min_label_spacing, prev_right + min_node_gap + half_w)
        adjusted_centers[g] = c_new
        prev_center = c_new
        prev_right = c_new + half_w

    min_left = min(adjusted_centers[g] - r3_nodes[g]['w'] / 2 for g in valid_gos)
    if min_left < 20:
        shift = 20 - min_left
        for g in valid_gos:
            adjusted_centers[g] += shift

    for g in valid_gos:
        r3_nodes[g]['x'] = adjusted_centers[g] - r3_nodes[g]['w'] / 2
        r3_nodes[g]['in'] = r3_nodes[g]['x']
else:
    pass

# 让第二列（物种）与第三列（GO）总体高度一致：仅调整列内空隙，不改节点厚度
def _column_span(nodes_dict, order):
    if not order:
        return 0.0, 0.0, 0.0
    x_min = min(nodes_dict[k]['x'] for k in order)
    x_max = max(nodes_dict[k]['x'] + nodes_dict[k]['w'] for k in order)
    return x_min, x_max, x_max - x_min

def _redistribute_with_target_span(nodes_dict, order, target_span, start_x=20.0):
    if not order:
        return
    n = len(order)
    total_w = sum(nodes_dict[k]['w'] for k in order)
    if n == 1:
        nodes_dict[order[0]]['x'] = start_x
        if 'in' in nodes_dict[order[0]]:
            nodes_dict[order[0]]['in'] = start_x
        if 'out' in nodes_dict[order[0]]:
            nodes_dict[order[0]]['out'] = start_x
        return

    gap = max(0.0, (target_span - total_w) / (n - 1))
    cx_col = start_x
    for key in order:
        nodes_dict[key]['x'] = cx_col
        if 'in' in nodes_dict[key]:
            nodes_dict[key]['in'] = cx_col
        if 'out' in nodes_dict[key]:
            nodes_dict[key]['out'] = cx_col
        cx_col += nodes_dict[key]['w'] + gap

r2_min, r2_max, r2_span_now = _column_span(r2_nodes, r2_species)
r3_min, r3_max, r3_span_now = _column_span(r3_nodes, valid_gos)
target_span = max(r2_span_now, r3_span_now)

if abs(r2_span_now - target_span) > 1e-9:
    _redistribute_with_target_span(r2_nodes, r2_species, target_span, start_x=20.0)
if abs(r3_span_now - target_span) > 1e-9:
    _redistribute_with_target_span(r3_nodes, valid_gos, target_span, start_x=20.0)

r2_min, r2_max, r2_span_now = _column_span(r2_nodes, r2_species)
r3_min, r3_max, r3_span_now = _column_span(r3_nodes, valid_gos)
r3_xmax = max(r2_max, r3_max)

y_range_max = max(950, int(r3_xmax + 120))
fig_height = y_range_max

# --- Coordinates ---
# Map original coordinates by rotating CCW 90 degrees:
# Original canvas was W=900, H=1000. New canvas is W=1000, H=950
H_orig = 1000

def rot_pt(x, y):
    # CCW 90 degrees around center maps: Top-Left (0, 1000) to Bottom-Left (0, 0)
    rx = H_orig - y
    ry = x
    # 记录所有绘制点的边界，以便后面把画布裁切为紧凑的边框
    global _draw_min_x, _draw_max_x, _draw_min_y, _draw_max_y
    try:
        _draw_min_x
    except NameError:
        _draw_min_x = float('inf')
        _draw_max_x = float('-inf')
        _draw_min_y = float('inf')
        _draw_max_y = float('-inf')
    if rx < _draw_min_x: _draw_min_x = rx
    if rx > _draw_max_x: _draw_max_x = rx
    if ry < _draw_min_y: _draw_min_y = ry
    if ry > _draw_max_y: _draw_max_y = ry
    return rx, ry

Y1_B, Y1_T = 880, 900
Y2_B, Y2_T = 700, 720
Y3_B, Y3_T = 160, 180

def get_rgb(hex_c, a=1.0):
    if not hex_c.startswith("#"): return hex_c
    h = hex_c.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def add_rotated_ribbon(xt, wt, xb, wb, yt, yb, color):
    line_w = 0 
    x_tr = xt + wt
    x_br = xb + wb
    ym = (yt + yb) / 2
    
    p1 = rot_pt(xt, yt)
    c1 = rot_pt(xt, ym)
    c2 = rot_pt(xb, ym)
    p2 = rot_pt(xb, yb)
    p3 = rot_pt(x_br, yb)
    c3 = rot_pt(x_br, ym)
    c4 = rot_pt(x_tr, ym)
    p4 = rot_pt(x_tr, yt)
    
    path = f"M {p1[0]} {p1[1]} C {c1[0]} {c1[1]}, {c2[0]} {c2[1]}, {p2[0]} {p2[1]} L {p3[0]} {p3[1]} C {c3[0]} {c3[1]}, {c4[0]} {c4[1]}, {p4[0]} {p4[1]} Z"
    fig.add_shape(type="path", path=path, fillcolor=color, line=dict(width=line_w), layer="below")


def add_gradient_rotated_ribbon(xt, wt, xb, wb, yt, yb, color_start, color_end, steps=72):
    def parse_hex(h):
        h = h.lstrip('#')
        if len(h) == 6:
            return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]
        return [0, 0, 0]

    c1 = parse_hex(color_start)
    c2 = parse_hex(color_end)
    ym = (yt + yb) / 2
    x_tr = xt + wt
    x_br = xb + wb

    def bezier(t, p0, p1, p2, p3):
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

    for i in range(steps):
        t1 = i / steps
        t2 = (i + 1) / steps

        xl1 = bezier(t1, xt, xt, xb, xb)
        y1 = bezier(t1, yt, ym, ym, yb)
        xl2 = bezier(t2, xt, xt, xb, xb)
        y2 = bezier(t2, yt, ym, ym, yb)

        xr1 = bezier(t1, x_tr, x_tr, x_br, x_br)
        xr2 = bezier(t2, x_tr, x_tr, x_br, x_br)

        p1 = rot_pt(xl1, y1)
        p2 = rot_pt(xl2, y2)
        p3 = rot_pt(xr2, y2)
        p4 = rot_pt(xr1, y1)

        tm = (t1 + t2) / 2

        # 使用“浅色”作为中间过渡，而不是纯白。
        mid_base = [
            round((c1[0] + c2[0]) / 2),
            round((c1[1] + c2[1]) / 2),
            round((c1[2] + c2[2]) / 2),
        ]
        light_ratio = 0.15
        mid_light = [
            round(mid_base[0] * (1 - light_ratio) + 255 * light_ratio),
            round(mid_base[1] * (1 - light_ratio) + 255 * light_ratio),
            round(mid_base[2] * (1 - light_ratio) + 255 * light_ratio),
        ]

        # 两端更贴近两侧节点颜色：起点色 -> 浅色中间 -> 终点色
        if tm <= 0.5:
            f = tm / 0.5
            r = round(c1[0] * (1 - f) + mid_light[0] * f)
            g = round(c1[1] * (1 - f) + mid_light[1] * f)
            b = round(c1[2] * (1 - f) + mid_light[2] * f)
        else:
            f = (tm - 0.5) / 0.5
            r = round(mid_light[0] * (1 - f) + c2[0] * f)
            g = round(mid_light[1] * (1 - f) + c2[1] * f)
            b = round(mid_light[2] * (1 - f) + c2[2] * f)

        # 保持中间更柔和、两侧略实，避免突兀
        dist = abs(tm - 0.5) / 0.5
        a = 0.28 + 0.12 * (dist ** 0.8)

        color = f"rgba({r},{g},{b},{a:.4f})"
        path = f"M {p1[0]} {p1[1]} L {p2[0]} {p2[1]} L {p3[0]} {p3[1]} L {p4[0]} {p4[1]} Z"
        fig.add_shape(type="path", path=path, fillcolor=color, line=dict(width=0, color='rgba(0,0,0,0)'), layer="below")

def add_rotated_rect(x, w, yB, yT, color):
    p1 = rot_pt(x, yT)
    p2 = rot_pt(x + w, yB)
    fig.add_shape(type="rect", x0=p1[0], y0=p1[1], x1=p2[0], y1=p2[1], fillcolor=color, line=dict(color="#555", width=1))

def add_rotated_rect_plain(x, w, yB, yT, color):
    p1 = rot_pt(x, yT)
    p2 = rot_pt(x + w, yB)
    fig.add_shape(type="rect", x0=p1[0], y0=p1[1], x1=p2[0], y1=p2[1], fillcolor=color, line=dict(width=0))

# --- Draw Ribbons Row 2 -> Row 3 ---
for s in r2_species:
    for i in r1_interactions:
        for g in valid_gos:
            c = sp_go_inter_weight.get((i, s, g), 0)
            if c <= 0: continue
            wt = c / max(1, r2_total) * r2_avail
            wb = c / max(1, r3_total) * r3_avail
            xt = r2_nodes[s]['out']; xb = r3_nodes[g]['in']
            r2_nodes[s]['out'] += wt; r3_nodes[g]['in'] += wb
            add_rotated_ribbon(xt, wt, xb, wb, Y2_B, Y3_T, get_rgb(INTERACTION_COLORS[i], 0.45))

# --- Draw Nodes & Labels ---
for name, node in r2_nodes.items():
    add_rotated_rect(node['x'], node['w'], Y2_B, Y2_T, SPECIES_COLORS[name])

    # 在第二列节点左侧添加按第一列占比分段的小色块（颜色使用第一列配色）
    r2_strip_gap = 0
    r2_strip_thick = Y2_T - Y2_B
    r2_strip_yB = Y2_T + r2_strip_gap
    r2_strip_yT = Y2_T + r2_strip_gap + r2_strip_thick
    seg_x = node['x']
    for i in r1_interactions:
        seg_w = r2_interaction_width[name].get(i, 0.0)
        if seg_w <= 0:
            continue
        add_rotated_rect_plain(seg_x, seg_w, r2_strip_yB, r2_strip_yT, INTERACTION_COLORS[i])
        seg_x += seg_w

    cx, cy = rot_pt(node['x']+node['w']/2, (Y2_B+Y2_T)/2)
    fig.add_annotation(x=cx, y=cy, text=name, showarrow=False, textangle=-90, font=dict(color='white', size=17, family='Arial', weight='bold'))

for name, node in r3_nodes.items():
    c = GO_TYPE_COLORS.get(all_gos_dict[name]['go_type'], '#CCC')
    add_rotated_rect(node['x'], node['w'], Y3_B, Y3_T, c)

    # 在GO节点左侧添加按物种分段的小色块（旋转后“左侧”需使用更大的原始y值）
    strip_gap = 1
    strip_thick = 5
    strip_yB = Y3_T + strip_gap
    strip_yT = Y3_T + strip_gap + strip_thick
    seg_x = node['x']
    # 注意：旋转后可见顺序会反转，因此这里使用反向绘制来匹配期望显示顺序
    strip_species_order = ['Gallus', 'Anas', 'Pigeon']
    for s in strip_species_order:
        seg_w = go_species_width[name].get(s, 0.0)
        if seg_w <= 0:
            continue
        add_rotated_rect_plain(seg_x, seg_w, strip_yB, strip_yT, SPECIES_COLORS[s])
        seg_x += seg_w

    # Vertically map to node center, horizontally gap by 10
    cx, cy = rot_pt(node['x'] + node['w']/2, Y3_B - 10)
    fig.add_annotation(x=cx, y=cy, text=name, showarrow=False, textangle=0, xanchor='left', yanchor='middle', font=dict(size=15, family='Arial'))

# 使用记录的绘图边界裁切画布，使画布恰好包住所有内容（加一点内边距）
pad = 12
try:
    _draw_min_x, _draw_max_x, _draw_min_y, _draw_max_y
except NameError:
    _draw_min_x = 0
    _draw_max_x = 1800
    _draw_min_y = 0
    _draw_max_y = y_range_max

min_x = max(0, int(_draw_min_x - pad))
max_x = int(_draw_max_x + pad)
min_y = max(0, int(_draw_min_y - pad))
max_y = int(_draw_max_y + pad)
width_px = max(300, max_x - min_x)
height_px = max(200, max_y - min_y)

fig.update_layout(
    xaxis=dict(range=[min_x, max_x], showgrid=False, zeroline=False, visible=False),
    yaxis=dict(range=[min_y, max_y], showgrid=False, zeroline=False, visible=False),
    plot_bgcolor='white', paper_bgcolor='white',
    width=width_px, height=height_px, margin=dict(l=0, r=0, t=0, b=0)
)

out_png = work_dir / "Fig.Expansions and Contractions.png"
out_pdf = work_dir / "Fig.Expansions and Contractions.pdf"
out_html = work_dir / "Fig.Expansions and Contractions.html"
export_pdf = True

fig.write_html(str(out_html))
# 与PDF保持同一逻辑尺寸，使用scale提高PNG清晰度，避免字体相对大小变化
base_width = 1800
base_height = fig_height
png_scale = 3.0  # 输出为 5400x2850，满足高分辨率需求
fig.write_image(str(out_png), width=base_width, height=base_height, scale=png_scale)

if export_pdf:
    fig.write_image(str(out_pdf), width=base_width, height=base_height)
print("SUCCESSfully generated PNG, PDF, and HTML!")
