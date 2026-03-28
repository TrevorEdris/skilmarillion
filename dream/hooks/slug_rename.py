#!/usr/bin/env python3
"""UserPromptSubmit hook — renames pending session dir with a slug from the user's prompt.

Primary: uses claude CLI + Haiku to generate a concise 3-4 word slug.
Fallback: deterministic extraction if CLI is unavailable.

Fast path: if $SKILMARILLION_SESSION_DIR doesn't contain '_pending_', exits immediately.
Slow path: scans the current month's subdir for pending dirs.
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TICKET_RE = re.compile(r"([A-Z][A-Za-z]+-\d+)")

SLUG_PROMPT = (
    "Generate a concise 3-4 word title for a coding session based on the user's "
    "first message. Output ONLY the title in Title-Case separated by hyphens. "
    "No explanation, no quotes, no punctuation. Examples: Build-Auth-Flow, "
    "Fix-Login-Bug, Refactor-Error-Handling, Add-Dashboard-UI\n\n"
    "User message: {prompt}"
)

# Deterministic fallback
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "be", "as", "do", "im", "its",
    "i", "we", "you", "my", "our", "this", "that", "here", "well", "lets",
    "want", "going", "just", "really", "very", "also", "about", "some",
}
MAX_SLUG_WORDS = 4


def _generate_slug_haiku(prompt: str) -> str | None:
    """Call claude CLI with Haiku to generate a slug. Returns None on failure."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None

    try:
        result = subprocess.run(
            [claude_bin, "-p", SLUG_PROMPT.format(prompt=prompt), "--model", "haiku"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None

        slug = result.stdout.strip()
        # Sanitize: keep only alphanumeric and hyphens
        slug = re.sub(r"[^a-zA-Z0-9\-]", "", slug)
        return slug if slug else None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _make_slug_deterministic(text: str) -> str:
    """Fallback: extract 3-4 meaningful words as a Title-Case slug."""
    cleaned = TICKET_RE.sub("", text).strip()
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned)
    words = [w for w in cleaned.split() if w.lower() not in STOP_WORDS]
    words = words[:MAX_SLUG_WORDS]
    slug = "-".join(w.capitalize() for w in words if w)
    return slug if slug else "Session"


def _make_slug(text: str) -> str:
    """Generate a slug: try Haiku first, fall back to deterministic."""
    slug = _generate_slug_haiku(text)
    if slug:
        return slug
    return _make_slug_deterministic(text)


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
    user_prompt = payload.get("prompt", "") or payload.get("user_prompt", "")
    if not user_prompt:
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
