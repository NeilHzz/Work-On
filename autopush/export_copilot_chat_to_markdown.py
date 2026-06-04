from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export VS Code Copilot Chat transcripts to daily Markdown files."
    )
    parser.add_argument("--transcripts-dir", help="Directory containing transcript JSONL files.")
    parser.add_argument("--output-dir", help="Directory for generated Markdown files.")
    parser.add_argument("--workspace-name", help="Workspace key used in the export metadata.")
    parser.add_argument("--machine", default="", help="Machine name used in the export metadata.")
    return parser.parse_args()


def file_uri_to_path(value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path).lstrip("/"))


def infer_transcripts_dir(workspace_dir: Path) -> Path | None:
    storage_root = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage"
    if not storage_root.exists():
        return None

    resolved_workspace = workspace_dir.resolve()
    for storage_dir in storage_root.iterdir():
        workspace_json = storage_dir / "workspace.json"
        if not workspace_json.exists():
            continue

        try:
            workspace_data = json.loads(workspace_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        folder = workspace_data.get("folder")
        if not isinstance(folder, str):
            continue

        folder_path = file_uri_to_path(folder)
        if folder_path is None or folder_path.resolve() != resolved_workspace:
            continue

        transcripts_dir = storage_dir / "GitHub.copilot-chat" / "transcripts"
        if transcripts_dir.exists():
            return transcripts_dir

    return None


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def parse_timestamp(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone()


def format_timestamp(value: dt.datetime | None) -> str:
    if value is None:
        return "unknown"
    return value.strftime("%Y-%m-%d %H:%M:%S %Z")


def clean_text(value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def choose_title(messages: list[dict], fallback: str) -> str:
    for message in messages:
        if message["role"] != "user":
            continue
        content = message["content"]
        if not content:
            continue
        first_line = clean_text(content).splitlines()[0].strip()
        if first_line:
            return first_line[:80]
    return fallback


def file_slug(started_at: dt.datetime | None, session_id: str) -> str:
    if started_at is None:
        prefix = "unknown-time"
    else:
        prefix = started_at.strftime("%Y-%m-%d_%H%M%S")
    return f"{prefix}_{session_id[:8]}"


def collect_messages(records: list[dict]) -> list[dict]:
    messages: list[dict] = []
    for record in records:
        record_type = record.get("type")
        if record_type not in {"user.message", "assistant.message"}:
            continue

        data = record.get("data") or {}
        content = data.get("content")
        if not isinstance(content, str):
            continue

        text = clean_text(content)
        if not text:
            continue

        role = "user" if record_type == "user.message" else "assistant"
        timestamp = parse_timestamp(record.get("timestamp"))
        messages.append(
            {
                "role": role,
                "content": text,
                "timestamp": timestamp,
            }
        )

    return messages


def render_session_markdown(
    session_id: str,
    session_title: str,
    workspace_name: str,
    machine_name: str,
    transcript_name: str,
    started_at: dt.datetime | None,
    updated_at: dt.datetime | None,
    messages: list[dict],
) -> str:
    lines = [
        f"# {session_title}",
        "",
        "## Metadata",
        f"- Session ID: {session_id}",
        f"- Workspace: {workspace_name}",
        f"- Machine: {machine_name or 'unknown'}",
        f"- Started: {format_timestamp(started_at)}",
        f"- Updated: {format_timestamp(updated_at)}",
        f"- Source transcript: {transcript_name}",
        f"- Message count: {len(messages)}",
        "",
        "## Conversation",
        "",
    ]

    for index, message in enumerate(messages, start=1):
        role_label = "User" if message["role"] == "user" else "Assistant"
        header = f"### {index}. {role_label}"
        if message["timestamp"] is not None:
            header += f" ({format_timestamp(message['timestamp'])})"
        lines.append(header)
        lines.append("")
        lines.append(message["content"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_daily_index(date_label: str, sessions: list[dict]) -> str:
    lines = [
        f"# Chat Archive for {date_label}",
        "",
        "This folder contains one Markdown file per Copilot Chat session for the day.",
        "",
    ]

    for session in sorted(sessions, key=lambda item: item["started_sort"]):
        started_text = format_timestamp(session["started_at"])
        lines.append(f"- [{session['title']}]({session['filename']}) | {started_text} | {session['session_id']}")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    workspace_dir = Path.cwd()
    inferred_transcripts_dir = infer_transcripts_dir(workspace_dir)
    transcripts_dir = Path(args.transcripts_dir) if args.transcripts_dir else inferred_transcripts_dir
    output_dir = Path(args.output_dir) if args.output_dir else workspace_dir / "chat_logs"
    workspace_name = args.workspace_name or workspace_dir.name

    if transcripts_dir is None or not transcripts_dir.exists():
        print(f"[chat-md] transcript directory not found: {transcripts_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    daily_sessions: dict[str, list[dict]] = {}
    exported_count = 0

    for transcript_path in sorted(transcripts_dir.glob("*.jsonl")):
        records = read_jsonl(transcript_path)
        if not records:
            continue

        session_start = next((record for record in records if record.get("type") == "session.start"), None)
        session_data = session_start.get("data") if isinstance(session_start, dict) else {}
        session_id = session_data.get("sessionId") or transcript_path.stem
        started_at = parse_timestamp(session_data.get("startTime"))
        updated_at = parse_timestamp(records[-1].get("timestamp")) if records else None

        messages = collect_messages(records)
        if not messages:
            continue

        date_label = (started_at or updated_at or dt.datetime.now().astimezone()).strftime("%Y-%m-%d")
        session_title = choose_title(messages, f"Chat {session_id[:8]}")
        slug = file_slug(started_at or updated_at, session_id)
        day_dir = output_dir / date_label
        day_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{slug}.md"
        session_markdown = render_session_markdown(
            session_id=session_id,
            session_title=session_title,
            workspace_name=workspace_name,
            machine_name=args.machine,
            transcript_name=transcript_path.name,
            started_at=started_at,
            updated_at=updated_at,
            messages=messages,
        )
        (day_dir / filename).write_text(session_markdown, encoding="utf-8")

        daily_sessions.setdefault(date_label, []).append(
            {
                "title": session_title,
                "filename": filename,
                "session_id": session_id,
                "started_at": started_at,
                "started_sort": started_at or updated_at or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
            }
        )
        exported_count += 1

    for date_label, sessions in daily_sessions.items():
        index_content = render_daily_index(date_label, sessions)
        (output_dir / date_label / "README.md").write_text(index_content, encoding="utf-8")

    print(f"[chat-md] exported {exported_count} sessions to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
