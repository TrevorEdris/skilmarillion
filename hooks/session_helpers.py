#!/usr/bin/env python3
"""Shared helpers for the session lifecycle hooks.

The single source of truth for "is this a genuine interactive top-level
session?" — the predicate both session_start and slug_rename use to avoid
creating session directories for headless (`claude -p`), sub-agent, and
scheduled/cron invocations, which are non-interactive children that should not
mint session docs.
"""

import os
import tempfile

# Prompt wrappers and sentinels that mark a UserPromptSubmit payload as NOT a
# genuine human prompt. Used by slug_rename's content guard.
SLUG_SENTINEL = "Generate a concise 3-4 word title"
NON_PROMPT_PREFIXES = (
    SLUG_SENTINEL,
    "<task-notification>",
    "<system-reminder>",
    "<command-message>",
    "Scheduledtask",
    "ScheduledTask",
)

_TEMP_ROOTS = (
    tempfile.gettempdir(),
    "/tmp",
    "/private/tmp",
    "/private/var/folders",
)


def _has_controlling_terminal() -> bool:
    """True if the process is attached to a controlling terminal.

    Checks stderr (fd 2), which an interactive Claude Code session inherits
    from the user's terminal. Falls back to opening /dev/tty for the case where
    the harness redirects stderr but a controlling terminal still exists.
    Headless, sub-agent, and scheduled invocations have no controlling
    terminal, so both checks fail for them.
    """
    try:
        if os.isatty(2):
            return True
    except OSError:
        pass
    try:
        with open("/dev/tty"):
            return True
    except OSError:
        return False


def is_temp_or_task_dir(project_dir: str | None) -> bool:
    """True if project_dir lives under a temp root or a sub-agent tasks path."""
    if not project_dir:
        return False
    resolved = os.path.realpath(project_dir)
    if "/tasks/" in resolved or "/.claude/scheduled-tasks/" in resolved:
        return True
    return any(resolved.startswith(os.path.realpath(root)) for root in _TEMP_ROOTS)


def is_real_interactive_session(
    *,
    project_dir: str | None,
    tty_probe=_has_controlling_terminal,
) -> bool:
    """True only for a genuine interactive top-level session.

    ``tty_probe`` is injectable so tests can stub the terminal check
    deterministically.
    """
    if is_temp_or_task_dir(project_dir):
        return False
    return bool(tty_probe())


def is_non_prompt_text(text: str | None) -> bool:
    """True if the prompt text is empty or a harness-injected non-prompt."""
    if text is None:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    return any(stripped.startswith(prefix) for prefix in NON_PROMPT_PREFIXES)
