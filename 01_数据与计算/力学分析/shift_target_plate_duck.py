"""
LS-DYNA 靶板水平位置批量偏移脚本（鸭蛋版）
基于 Duck2_20260324 的 input.k，将 Part 2（靶板）在 XZ 平面内按网格偏移
网格精度：0.5 mm / 格，共 9 组工况（含中心位置）

9 组模拟位置（网格坐标 → 实际偏移量）：
  ( 1, 1) → dx=+0.5mm, dz=+0.5mm
  ( 1,-1) → dx=+0.5mm, dz=-0.5mm
  (-1, 1) → dx=-0.5mm, dz=+0.5mm
  (-1,-1) → dx=-0.5mm, dz=-0.5mm
  ( 0, 1) → dx= 0.0mm, dz=+0.5mm
  ( 0,-1) → dx= 0.0mm, dz=-0.5mm
  ( 1, 0) → dx=+0.5mm, dz= 0.0mm
  (-1, 0) → dx=-0.5mm, dz= 0.0mm
  ( 0, 0) → dx= 0.0mm, dz= 0.0mm  (中心参照)
"""

import os
import re

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
SRC_FILE   = r"D:\system_folder\Desktop\LS-DYNA\Duck2_20260324_files\dp0\SYS\MECH\input.k"
OUTPUT_DIR = r"D:\system_folder\Desktop\LS-DYNA\duck_parametric"
TARGET_PID = 2          # 靶板的 Part ID（与 Chicken/Pigeon 相同）
GRID_SIZE  = 0.5        # mm / 格

# 9 组网格坐标
POSITIONS = [
    ( 1,  1),
    ( 1, -1),
    (-1,  1),
    (-1, -1),
    ( 0,  1),
    ( 0, -1),
    ( 1,  0),
    (-1,  0),
    ( 0,  0),   # 中心
]

def folder_name(gx, gz):
    def tag(v):
        return f"p{abs(v)}" if v >= 0 else f"n{abs(v)}"
    return f"pos_{tag(gx)}_{tag(gz)}"


# ─────────────────────────────────────────
# 第一步：读取全部行
# ─────────────────────────────────────────
print(f"读取文件：{SRC_FILE}")
with open(SRC_FILE, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
print(f"  共 {len(lines):,} 行")


# ─────────────────────────────────────────
# 第二步：定位 *NODE 和 *ELEMENT_SOLID 段
# ─────────────────────────────────────────
node_start       = None
node_end         = None
elem_solid_start = None
elem_solid_end   = None

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("*NODE") and node_start is None:
        node_start = i
    elif node_start is not None and node_end is None and stripped.startswith("*") and i > node_start:
        node_end = i

    if stripped.startswith("*ELEMENT_SOLID") and elem_solid_start is None:
        elem_solid_start = i
    elif elem_solid_start is not None and elem_solid_end is None and stripped.startswith("*") and i > elem_solid_start:
        elem_solid_end = i

print(f"  *NODE 段：行 {node_start+1} ~ {node_end}")
print(f"  *ELEMENT_SOLID 段：行 {elem_solid_start+1} ~ {elem_solid_end}")


# ─────────────────────────────────────────
# 第三步：解析 ELEMENT_SOLID，收集 Part 2 节点 ID
# ─────────────────────────────────────────
part2_nodes = set()

i = elem_solid_start + 1
while i < elem_solid_end:
    line_a = lines[i].strip()
    if not line_a or line_a.startswith("$"):
        i += 1
        continue
    tokens_a = line_a.split()
    if len(tokens_a) == 2:
        try:
            pid = int(tokens_a[1])
        except ValueError:
            i += 1
            continue
        i += 1
        if i >= elem_solid_end:
            break
        line_b = lines[i].strip()
        if pid == TARGET_PID and line_b and not line_b.startswith("$"):
            for tok in line_b.split():
                try:
                    part2_nodes.add(int(tok))
                except ValueError:
                    pass
    else:
        if len(tokens_a) >= 10:
            try:
                pid = int(tokens_a[1])
                if pid == TARGET_PID:
                    for tok in tokens_a[2:]:
                        part2_nodes.add(int(tok))
            except ValueError:
                pass
    i += 1

print(f"  Part {TARGET_PID} 包含 {len(part2_nodes):,} 个不重复节点")


# ─────────────────────────────────────────
# 第四步：定位 NODE 段中 Part 2 节点的行
# ─────────────────────────────────────────
NODE_LINE_RE = re.compile(
    r'^(\s*\d+)'
    r'(\s+[-+]?\d+\.\d+)'
    r'(\s+[-+]?\d+\.\d+)'
    r'(\s+[-+]?\d+\.\d+)'
    r'(.*\n?)$'
)

part2_node_lines = {}
for idx in range(node_start + 1, node_end):
    line = lines[idx]
    m = NODE_LINE_RE.match(line)
    if m:
        try:
            nid = int(m.group(1))
        except ValueError:
            continue
        if nid in part2_nodes:
            part2_node_lines[idx] = (
                nid,
                float(m.group(2)),
                float(m.group(3)),
                float(m.group(4)),
                m,
            )

print(f"  在 NODE 段中匹配到 {len(part2_node_lines):,} 行 Part 2 节点")


# ─────────────────────────────────────────
# 第五步：批量生成 9 组 input.k
# ─────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

for gx, gz in POSITIONS:
    dx = gx * GRID_SIZE
    dz = gz * GRID_SIZE
    fname = folder_name(gx, gz)
    out_folder = os.path.join(OUTPUT_DIR, fname)
    os.makedirs(out_folder, exist_ok=True)
    out_file = os.path.join(out_folder, "input.k")

    print(f"  生成 [{fname}]  dx={dx:+.1f}mm  dz={dz:+.1f}mm  →  {out_file}")

    with open(out_file, "w", encoding="utf-8", errors="replace") as fout:
        for idx, line in enumerate(lines):
            if idx in part2_node_lines:
                nid, ox, oy, oz, m = part2_node_lines[idx]
                new_x = ox + dx
                new_z = oz + dz
                id_str  = m.group(1)
                y_str   = m.group(3)
                tail    = m.group(5)
                x_width = len(m.group(2))
                z_width = len(m.group(4))
                x_fmt   = f"{new_x:{x_width}.8f}"
                z_fmt   = f"{new_z:{z_width}.8f}"
                fout.write(id_str + x_fmt + y_str + z_fmt + tail)
            else:
                fout.write(line)

print("\n全部完成！")
print(f"输出目录：{OUTPUT_DIR}")
for gx, gz in POSITIONS:
    dx = gx * GRID_SIZE
    dz = gz * GRID_SIZE
    tag = folder_name(gx, gz)
    print(f"  {tag:15s}  ({gx:+d},{gz:+d})  dx={dx:+.1f}mm  dz={dz:+.1f}mm")
