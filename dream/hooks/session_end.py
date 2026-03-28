#!/usr/bin/env python3
"""SessionEnd hook — marks session completed and updates INDEX.md.

Fires on: SessionEnd (clear, resume, logout, prompt_input_exit, etc.)
Updates SESSION.md frontmatter: status -> completed, adds ended timestamp.
Appends a deterministic row to {sessions_root}/INDEX.md.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

TICKET_RE = re.compile(r"([A-Z][A-Za-z]+-\d+)")

INDEX_HEADER = """\
# Session Index

| Date | Ticket | Title | Discovery | Plan | Session |
|------|--------|-------|-----------|------|---------|
"""


def _update_session_md(session_md: Path) -> None:
    """Update SESSION.md frontmatter to mark session completed."""
    content = session_md.read_text()
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    content = content.replace("status: active", "status: completed")
    content = content.replace(
        "status: completed",
        f"status: completed\nended: {now_iso}",
    )

    session_md.write_text(content)


def _parse_session_dir_name(dir_name: str) -> tuple[str, str, str]:
    """Parse DD-HHMM_TICKET_Slug or DD-HHMM_Slug into (date_prefix, ticket, title).

    Returns (date_prefix, ticket_or_empty, title_with_spaces).
    """
    parts = dir_name.split("_", 1)
    date_prefix = parts[0] if parts else dir_name
    remainder = parts[1] if len(parts) > 1 else ""

    ticket_match = TICKET_RE.match(remainder)
    if ticket_match:
        ticket = ticket_match.group(1)
        title = remainder[ticket_match.end():].lstrip("_").replace("-", " ").replace("_", " ").strip()
    else:
        ticket = ""
        title = remainder.replace("-", " ").replace("_", " ").strip()

    return date_prefix, ticket, title


def _build_index_row(session_dir: Path) -> str:
    """Build a single INDEX.md table row for a session dir."""
    dir_name = session_dir.name
    month_name = session_dir.parent.name  # YYYY-MM

    date_prefix, ticket, title = _parse_session_dir_name(dir_name)

    # Full date: YYYY-MM-DD from month dir + DD from session dir
    dd = date_prefix.split("-")[0] if "-" in date_prefix else date_prefix
    full_date = f"{month_name}-{dd}"

    has_discovery = "Y" if (session_dir / "DISCOVERY.md").is_file() else ""
    has_plan = "Y" if (session_dir / "PLAN.md").is_file() else ""
    has_session = "Y" if (session_dir / "SESSION.md").is_file() else ""

    return f"| {full_date} | {ticket} | {title} | {has_discovery} | {has_plan} | {has_session} |"


def _append_index(sessions_root: Path, session_dir: Path) -> None:
    """Append a row to INDEX.md, creating it if needed. Deduplicates by dir name."""
    index_path = sessions_root / "INDEX.md"

    if index_path.is_file():
        content = index_path.read_text()
    else:
        content = INDEX_HEADER

    # Dedup: build the row first, check if it (minus trailing file flags) already exists
    row = _build_index_row(session_dir)
    # Extract the stable portion (date + ticket + title) for matching
    row_key = "|".join(row.split("|")[:4])  # "| date | ticket | title "
    if row_key in content:
        return

    content = content.rstrip("\n") + "\n" + row + "\n"
    index_path.write_text(content)


def handle_session_end(
    payload: dict,
    *,
    session_dir: str | None = None,
    sessions_root: str | None = None,
) -> dict:
    """Handle a SessionEnd event. Returns JSON-serializable dict for stdout."""
    if not session_dir:
        return {}

    sdir = Path(session_dir)
    if not sdir.is_dir():
        return {}

    session_md = sdir / "SESSION.md"
    if not session_md.is_file():
        return {}

    _update_session_md(session_md)

    if sessions_root:
        try:
            _append_index(Path(sessions_root), sdir)
        except OSError:
            pass

    return {}


def main() -> None:
    """Entry point when invoked as a hook command."""
    import os

    stdin_data = sys.stdin.read()
    try:
        payload = json.loads(stdin_data)
    except (json.JSONDecodeError, TypeError):
        payload = {}

    result = handle_session_end(
        payload,
        session_dir=os.environ.get("SKILMARILLION_SESSION_DIR") or None,
        sessions_root=os.environ.get("SKILMARILLION_SESSIONS_DIR") or None,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
