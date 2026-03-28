#!/usr/bin/env python3
"""UserPromptSubmit hook — renames pending session dir with a slug from the user's prompt.

Fast path: if $SKILMARILLION_SESSION_DIR doesn't contain '_pending_', exits immediately.
Slow path: scans the current month's subdir for pending dirs.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

TICKET_RE = re.compile(r"([A-Z][A-Za-z]+-\d+)")
MAX_SLUG_LEN = 50


def _make_slug(text: str) -> str:
    """Convert free text to a filesystem-safe Title-Case slug."""
    # Strip ticket IDs (handled separately)
    cleaned = TICKET_RE.sub("", text).strip()
    # Keep only alphanumeric and spaces
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
    # Title case, replace spaces with hyphens
    words = cleaned.split()
    slug = "-".join(w.capitalize() for w in words if w)
    return slug[:MAX_SLUG_LEN] if slug else "Session"


def _extract_ticket(text: str) -> str | None:
    """Extract the first ticket ID (e.g. PROJ-123) from text."""
    m = TICKET_RE.search(text)
    return m.group(1) if m else None


def _find_pending_dir(month_dir: Path) -> Path | None:
    """Find a _pending_ dir in the month subdir."""
    if not month_dir.is_dir():
        return None
    for entry in month_dir.iterdir():
        if entry.is_dir() and "_pending_" in entry.name:
            return entry
    return None


def _resolve_sessions_dir(
    sessions_dir: str | None, project_dir: str | None
) -> Path | None:
    """Resolve the sessions root directory."""
    if sessions_dir:
        return Path(sessions_dir)
    if project_dir:
        return Path(project_dir) / ".ai" / "sessions"
    return None


def handle_slug_rename(
    payload: dict,
    *,
    session_dir: str | None = None,
    sessions_dir: str | None = None,
    project_dir: str | None = None,
    env_file_path: str | None = None,
) -> dict:
    """Handle a UserPromptSubmit event. Returns JSON-serializable dict for stdout."""
    # Fast path: env var set and dir name has no pending marker
    if session_dir and "_pending_" not in Path(session_dir).name:
        return {}

    # Locate the pending dir
    pending: Path | None = None

    if session_dir and "_pending_" in Path(session_dir).name:
        candidate = Path(session_dir)
        if candidate.is_dir():
            pending = candidate
    else:
        root = _resolve_sessions_dir(sessions_dir, project_dir)
        if root:
            now = datetime.now()
            month_dir = root / now.strftime("%Y-%m")
            pending = _find_pending_dir(month_dir)

    if pending is None:
        return {}

    # Extract prompt and build new name
    user_prompt = payload.get("user_prompt", "")
    if not user_prompt:
        return {}

    ticket = _extract_ticket(user_prompt)
    slug = _make_slug(user_prompt)

    # Build new dir name: preserve the DD-HHMM prefix
    old_name = pending.name
    # Extract prefix up to _pending_ (e.g. "28-1430")
    prefix = old_name.split("_pending_")[0]

    if ticket:
        new_name = f"{prefix}_{ticket}_{slug}"
    else:
        new_name = f"{prefix}_{slug}"

    new_path = pending.parent / new_name

    try:
        pending.rename(new_path)
    except OSError:
        return {}

    # Update env file with new path
    if env_file_path:
        try:
            Path(env_file_path).write_text(
                f"SKILMARILLION_SESSION_DIR={new_path}\n"
            )
        except OSError:
            pass

    return {
        "systemMessage": f"[dream] Session renamed: {new_path}",
    }


def main() -> None:
    """Entry point when invoked as a hook command."""
    import os

    stdin_data = sys.stdin.read()
    try:
        payload = json.loads(stdin_data)
    except (json.JSONDecodeError, TypeError):
        payload = {}

    result = handle_slug_rename(
        payload,
        session_dir=os.environ.get("SKILMARILLION_SESSION_DIR") or None,
        sessions_dir=os.environ.get("SKILMARILLION_SESSIONS_DIR") or None,
        project_dir=os.environ.get("CLAUDE_PROJECT_DIR") or None,
        env_file_path=os.environ.get("CLAUDE_ENV_FILE") or None,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
