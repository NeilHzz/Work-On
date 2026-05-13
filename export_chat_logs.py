"""
export_chat_logs.py
将 VS Code Copilot Chat 的 JSONL transcript 导出为每个对话一个 MD 文件。
每次运行会全量更新（覆盖写入），保证内容最新。
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

# ── 路径配置 ──────────────────────────────────────────────────
TRANSCRIPT_DIR = Path(r"C:\Users\NeilHz\AppData\Roaming\Code\User\workspaceStorage\4ce2c8362a127d461afa13ee8e75fcc5\GitHub.copilot-chat\transcripts")
OUTPUT_DIR = Path(__file__).parent / "chat_logs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 辅助函数 ──────────────────────────────────────────────────

def parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()


def load_events(jsonl_path: Path) -> list:
    events = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def build_md(session_id: str, events: list) -> str:
    # 基本信息
    session_start = None
    for e in events:
        if e.get("type") == "session.start":
            session_start = e.get("timestamp", "")
            break

    start_dt = parse_timestamp(session_start) if session_start else None
    date_str = start_dt.strftime("%Y-%m-%d") if start_dt else "unknown"
    time_str = start_dt.strftime("%H:%M") if start_dt else ""

    lines = [
        f"# 对话记录 {date_str}",
        "",
        f"- **Session ID**: `{session_id}`",
        f"- **开始时间**: {date_str} {time_str}",
        f"- **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    # 按 turn 组织：user → assistant（收集所有 assistant.message 的 content）
    i = 0
    while i < len(events):
        e = events[i]
        etype = e.get("type", "")

        if etype == "user.message":
            content = e.get("data", {}).get("content", "").strip()
            if content:
                lines.append("### 🙋 用户")
                lines.append("")
                lines.append(content)
                lines.append("")

        elif etype == "assistant.turn_start":
            # 收集这个 turn 内所有 assistant.message 的文字
            turn_id = e.get("data", {}).get("turnId")
            text_chunks = []
            i += 1
            while i < len(events):
                ae = events[i]
                atype = ae.get("type", "")
                if atype == "assistant.turn_end":
                    break
                if atype == "assistant.message":
                    chunk = ae.get("data", {}).get("content", "")
                    if chunk:
                        text_chunks.append(chunk)
                i += 1
            full_text = "".join(text_chunks).strip()
            if full_text:
                lines.append("### 🤖 助手")
                lines.append("")
                lines.append(full_text)
                lines.append("")

        i += 1

    return "\n".join(lines)


# ── 主逻辑 ────────────────────────────────────────────────────

def main():
    if not TRANSCRIPT_DIR.exists():
        print(f"[错误] transcript 目录不存在: {TRANSCRIPT_DIR}")
        return

    jsonl_files = list(TRANSCRIPT_DIR.glob("*.jsonl"))
    print(f"找到 {len(jsonl_files)} 个对话文件")

    for jf in jsonl_files:
        session_id = jf.stem
        events = load_events(jf)
        if not events:
            continue
        md_content = build_md(session_id, events)
        out_path = OUTPUT_DIR / f"{session_id}.md"
        out_path.write_text(md_content, encoding="utf-8")
        print(f"  ✓ {out_path.name}")

    print("导出完成。")


if __name__ == "__main__":
    main()
