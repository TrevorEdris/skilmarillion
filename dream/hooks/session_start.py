#!/usr/bin/env python3
"""SessionStart hook — creates session directory and SESSION.md.

Fires on: startup, resume, clear, compact.
Creates: {sessions_root}/YYYY-MM/DD-HHMM_pending_{session_id[:8]}/SESSION.md
Writes SKILMARILLION_SESSION_DIR to $CLAUDE_ENV_FILE for downstream hooks.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def _find_existing_pending(month_dir: Path) -> Path | None:
    """Find an existing _pending_ dir in the month subdir."""
    if not month_dir.is_dir():
        return None
    for entry in month_dir.iterdir():
        if entry.is_dir() and "_pending_" in entry.name:
            return entry
    return None


def _build_session_md(now: datetime) -> str:
    """Build SESSION.md content with YAML frontmatter."""
    date_str = now.strftime("%Y-%m-%d")
    return f"""---
date: {date_str}
status: active
---

# Session

## Prompts & Responses
"""


def _resolve_sessions_dir(
    sessions_dir: str | None, project_dir: str | None
) -> Path | None:
    """Resolve the sessions root directory."""
    if sessions_dir:
        return Path(sessions_dir)
    if project_dir:
        return Path(project_dir) / ".ai" / "sessions"
    return None


def handle_session_start(
    payload: dict,
    *,
    sessions_dir: str | None = None,
    project_dir: str | None = None,
    env_file_path: str | None = None,
) -> dict:
    """Handle a SessionStart event. Returns JSON-serializable dict for stdout."""
    root = _resolve_sessions_dir(sessions_dir, project_dir)
    if root is None:
        return {}

    now = datetime.now()
    month_dir = root / now.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    existing = _find_existing_pending(month_dir)
    if existing:
        session_dir = existing
    else:
        session_id = payload.get("session_id", "unknown")
        short_id = session_id[:8]
        day_time = now.strftime("%d-%H%M")
        dir_name = f"{day_time}_pending_{short_id}"
        session_dir = month_dir / dir_name
        session_dir.mkdir(parents=True, exist_ok=True)

        session_md = session_dir / "SESSION.md"
        session_md.write_text(_build_session_md(now))

    if env_file_path:
        try:
            Path(env_file_path).write_text(
                f"SKILMARILLION_SESSION_DIR={session_dir}\n"
            )
        except OSError:
            pass

    return {
        "systemMessage": f"[dream] Session directory: {session_dir}",
    }


def main() -> None:
    """Entry point when invoked as a hook command."""
    stdin_data = sys.stdin.read()
    try:
        payload = json.loads(stdin_data)
    except (json.JSONDecodeError, TypeError):
        payload = {}

    import os

    result = handle_session_start(
        payload,
        sessions_dir=os.environ.get("SKILMARILLION_SESSIONS_DIR") or None,
        project_dir=os.environ.get("CLAUDE_PROJECT_DIR") or None,
        env_file_path=os.environ.get("CLAUDE_ENV_FILE") or None,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
