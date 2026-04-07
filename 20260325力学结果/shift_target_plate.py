"""
LS-DYNA 靶板水平位置批量偏移脚本
基于 chicken260122 的 input.k，将 Part 2（靶板）在 XZ 平面内按网格偏移
网格精度：0.5 mm / 格

8 组模拟位置（网格坐标 → 实际偏移量）：
  (1, 1)  → dx=+0.5mm, dz=+0.5mm
  (1,-1)  → dx=+0.5mm, dz=-0.5mm
  (-1, 1) → dx=-0.5mm, dz=+0.5mm
  (-1,-1) → dx=-0.5mm, dz=-0.5mm
  (0, 1)  → dx= 0.0mm, dz=+0.5mm
  (0,-1)  → dx= 0.0mm, dz=-0.5mm
  (1, 0)  → dx=+0.5mm, dz= 0.0mm
  (-1, 0) → dx=-0.5mm, dz= 0.0mm
"""

import os
import re

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
SRC_FILE   = r"D:\system_folder\Desktop\LS-DYNA\chicken260122_files\dp0\SYS-1\MECH\input.k"
OUTPUT_DIR = r"D:\system_folder\Desktop\LS-DYNA\chicken_parametric"
TARGET_PID = 2          # 靶板的 Part ID
GRID_SIZE  = 0.5        # mm / 格

# 网格坐标 (gx, gz) → 文件夹名
POSITIONS = [
    ( 1,  1),
    ( 1, -1),
    (-1,  1),
    (-1, -1),
    ( 0,  1),
    ( 0, -1),
    ( 1,  0),
    (-1,  0),
]

def folder_name(gx, gz):
    """将网格坐标转换为合法文件夹名，例如 pos_p1_p1、pos_n1_p1"""
    def tag(v):
        return f"p{abs(v)}" if v >= 0 else f"n{abs(v)}"
    return f"pos_{tag(gx)}_{tag(gz)}"


# ─────────────────────────────────────────
# 第一步：读取全部行（一次 I/O）
# ─────────────────────────────────────────
print(f"读取文件：{SRC_FILE}")
with open(SRC_FILE, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
print(f"  共 {len(lines):,} 行")


# ─────────────────────────────────────────
# 第二步：找到各关键段的行范围
#   - *NODE
#   - *ELEMENT_SOLID
# ─────────────────────────────────────────
node_start       = None   # *NODE 行的索引
node_end         = None   # *NODE 段结束（下一个 * 关键字）
elem_solid_start = None   # *ELEMENT_SOLID 行的索引
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
#
# 格式（每元素 2 行）：
#   行A：  eid   pid            （纯整数，空格分隔）
#   行B：  n1 n2 n3 n4 n5 n6 n7 n8
# 注释行以 $ 开头，跳过
# ─────────────────────────────────────────
part2_nodes = set()

i = elem_solid_start + 1           # 跳过 *ELEMENT_SOLID 关键字行
while i < elem_solid_end:
    line_a = lines[i].strip()
    if not line_a or line_a.startswith("$"):
        i += 1
        continue
    tokens_a = line_a.split()
    # 行A：两个整数 eid pid
    if len(tokens_a) == 2:
        try:
            pid = int(tokens_a[1])
        except ValueError:
            i += 1
            continue
        # 下一行是节点
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
        # 某些格式 eid pid n1..n8 全在一行（8+8 格式），兼容处理
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
# 第四步：预先定位 NODE 段中每行的节点 ID
#   只记录属于 Part 2 的行索引，加速写出
# ─────────────────────────────────────────
# 每行格式：  8位整数节点ID  + 3×16位浮点坐标（固定宽度）
# 用正则兼容空格变宽情形
NODE_LINE_RE = re.compile(
    r'^(\s*\d+)'           # 节点 ID（含前导空格）
    r'(\s+[-+]?\d+\.\d+)'  # x
    r'(\s+[-+]?\d+\.\d+)'  # y
    r'(\s+[-+]?\d+\.\d+)'  # z
    r'(.*\n?)$'            # 尾部（tc/rc 约束等可选字段）
)

# 构建索引：行文件索引 → (node_id, x_col_start, y_col_start, z_col_start)
# 以便写出时直接替换 x/z
part2_node_lines = {}  # index in `lines` → (node_id, orig_x, orig_y, orig_z, prefix_len, full_match)
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
                float(m.group(2)),  # x
                float(m.group(3)),  # y
                float(m.group(4)),  # z
                m,                  # 正则匹配对象，保留原始分组供重建
            )

print(f"  在 NODE 段中匹配到 {len(part2_node_lines):,} 行 Part 2 节点")


# ─────────────────────────────────────────
# 第五步：批量生成 8 组 input.k
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
                # 重建该行，保持与原文件相同宽度格式
                # 原始分组：g1=nid_str, g2=x_str, g3=y_str, g4=z_str, g5=tail
                id_str = m.group(1)           # 原始 nid 字段（含前导空格）
                y_str  = m.group(3)           # y 不变，保留原始字符串宽度
                tail   = m.group(5)           # 尾部字段及换行

                # 用原字段宽度格式化 x 和 z
                x_width = len(m.group(2))
                z_width = len(m.group(4))
                x_fmt = f"{new_x:{x_width}.8f}"
                z_fmt = f"{new_z:{z_width}.8f}"

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
