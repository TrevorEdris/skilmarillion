#!/usr/bin/env python3
"""UserPromptSubmit hook — renames pending session dir with a slug from the user's prompt.

Primary: uses claude CLI + Haiku to generate a concise 3-4 word slug.
Fallback: deterministic extraction if CLI is unavailable.

Fast path: if $SKILMARILLION_SESSION_DIR doesn't contain '_pending_', exits immediately.
Slow path: scans the current month's subdir for pending dirs via $CLAUDE_PROJECT_DIR.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from session_helpers import is_non_prompt_text, is_real_interactive_session

TICKET_RE = re.compile(r"([A-Z][A-Za-z]+-\d+)")

# Harness-injected wrapper blocks stripped before slugifying a real prompt.
WRAPPER_BLOCK_RE = re.compile(
    r"<(system-reminder|task-notification|command-message|command-name|command-args)>"
    r".*?</\1>",
    re.DOTALL,
)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "be", "as", "do", "im", "its",
    "i", "we", "you", "my", "our", "this", "that", "here", "well", "lets",
    "want", "going", "just", "really", "very", "also", "about", "some",
}
MAX_SLUG_WORDS = 4


def _make_slug(text: str) -> str:
    """Extract 3-4 meaningful words as a Title-Case slug, deterministically."""
    cleaned = WRAPPER_BLOCK_RE.sub("", text)
    cleaned = TICKET_RE.sub("", cleaned).strip()
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
    words = [w for w in cleaned.split() if w.lower() not in STOP_WORDS]
    words = words[:MAX_SLUG_WORDS]
    slug = "-".join(w.capitalize() for w in words if w)
    return slug if slug else "Session"


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


def _resolve_sessions_dir(project_dir: str | None) -> Path | None:
    """Resolve the sessions root directory."""
    if project_dir:
        return Path(project_dir) / ".ai" / "sessions"
    return None


def handle_slug_rename(
    payload: dict,
    *,
    session_dir: str | None = None,
    project_dir: str | None = None,
    env_file_path: str | None = None,
) -> dict:
    """Handle a UserPromptSubmit event. Returns JSON-serializable dict for stdout."""
    # Defense in depth: never rename for non-interactive (headless / sub-agent /
    # scheduled) sessions. session_start gates dir creation on the same predicate,
    # so the two hooks' notion of "real session" cannot drift.
    if not is_real_interactive_session(project_dir=project_dir):
        return {}

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
        root = _resolve_sessions_dir(project_dir)
        if root:
            now = datetime.now()
            month_dir = root / now.strftime("%Y-%m")
            pending = _find_pending_dir(month_dir)

    if pending is None:
        return {}

    # Extract prompt and build new name
    user_prompt = payload.get("prompt", "") or payload.get("user_prompt", "")
    # Skip harness-injected non-prompts (slug-gen sentinel, task/system reminders,
    # scheduled-task payloads, empty) so they never name a session dir.
    if is_non_prompt_text(user_prompt):
        return {}

    ticket = _extract_ticket(user_prompt)
    slug = _make_slug(user_prompt)

    # Build new dir name: preserve the DD-HHMM prefix
    old_name = pending.name
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
        "systemMessage": f"[plan] Session renamed: {new_path}",
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
        project_dir=os.environ.get("CLAUDE_PROJECT_DIR") or None,
        env_file_path=os.environ.get("CLAUDE_ENV_FILE") or None,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
