#!/usr/bin/env python3
"""Tests for the session lifecycle hooks.

Run: `python3 hooks/test_hooks.py`  (or `python3 -m unittest` from hooks/).
Stdlib only — no external test runner.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import session_helpers  # noqa: E402
import session_start  # noqa: E402
import slug_rename  # noqa: E402


class PredicateTests(unittest.TestCase):
    def test_temp_or_task_dir_detection(self):
        self.assertTrue(session_helpers.is_temp_or_task_dir("/private/tmp/x/tasks/abc"))
        self.assertTrue(session_helpers.is_temp_or_task_dir(tempfile.gettempdir()))
        self.assertFalse(session_helpers.is_temp_or_task_dir("/Users/me/src/project"))
        self.assertFalse(session_helpers.is_temp_or_task_dir(None))

    def test_interactive_requires_tty(self):
        self.assertFalse(
            session_helpers.is_real_interactive_session(
                project_dir="/Users/me/src/project", tty_probe=lambda: False
            )
        )
        self.assertTrue(
            session_helpers.is_real_interactive_session(
                project_dir="/Users/me/src/project", tty_probe=lambda: True
            )
        )

    def test_temp_dir_overrides_tty(self):
        # Even with a TTY, a sub-agent/scheduled temp project dir is not interactive.
        self.assertFalse(
            session_helpers.is_real_interactive_session(
                project_dir="/private/tmp/run/tasks/abc", tty_probe=lambda: True
            )
        )

    def test_non_prompt_text(self):
        self.assertTrue(session_helpers.is_non_prompt_text(""))
        self.assertTrue(session_helpers.is_non_prompt_text("   "))
        self.assertTrue(session_helpers.is_non_prompt_text(None))
        self.assertTrue(
            session_helpers.is_non_prompt_text(
                "Generate a concise 3-4 word title for a coding session"
            )
        )
        self.assertTrue(session_helpers.is_non_prompt_text("<task-notification>\nx"))
        self.assertTrue(session_helpers.is_non_prompt_text("<system-reminder>x"))
        self.assertTrue(session_helpers.is_non_prompt_text("Scheduledtask Name=..."))
        self.assertFalse(session_helpers.is_non_prompt_text("Build the auth flow"))


class SessionStartGateTests(unittest.TestCase):
    def _month_dirs(self, root: Path):
        sessions = root / ".ai" / "sessions"
        return list(sessions.glob("*/")) if sessions.is_dir() else []

    def test_no_dir_when_not_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                session_start, "is_real_interactive_session", return_value=False
            ):
                result = session_start.handle_session_start(
                    {"session_id": "abcdef1234"}, project_dir=tmp
                )
            self.assertEqual(result, {})
            self.assertEqual(self._month_dirs(Path(tmp)), [])

    def test_dir_created_when_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                session_start, "is_real_interactive_session", return_value=True
            ):
                result = session_start.handle_session_start(
                    {"session_id": "abcdef1234"}, project_dir=tmp
                )
            self.assertIn("systemMessage", result)
            months = self._month_dirs(Path(tmp))
            self.assertEqual(len(months), 1)
            pending = list(months[0].glob("*_pending_*"))
            self.assertEqual(len(pending), 1)
            self.assertTrue((pending[0] / "SESSION.md").is_file())


class SlugTests(unittest.TestCase):
    def test_deterministic_slug_no_subprocess(self):
        self.assertFalse(hasattr(slug_rename, "_generate_slug_haiku"))
        self.assertFalse(hasattr(slug_rename, "subprocess"))
        self.assertEqual(slug_rename._make_slug("Build the auth flow"), "Build-Auth-Flow")

    def test_slug_strips_wrapper_blocks(self):
        text = "<system-reminder>noise here</system-reminder>Refactor error handling"
        self.assertEqual(slug_rename._make_slug(text), "Refactor-Error-Handling")


class SlugRenameGuardTests(unittest.TestCase):
    def _pending(self, tmp: str) -> Path:
        month = Path(tmp) / ".ai" / "sessions" / "2026-06"
        month.mkdir(parents=True)
        pending = month / "26-1200_pending_abcd1234"
        pending.mkdir()
        (pending / "SESSION.md").write_text("---\n---\n")
        return pending

    def test_skips_when_not_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending = self._pending(tmp)
            with mock.patch.object(
                slug_rename, "is_real_interactive_session", return_value=False
            ):
                result = slug_rename.handle_slug_rename(
                    {"prompt": "Build the auth flow"},
                    session_dir=str(pending),
                    project_dir=tmp,
                )
            self.assertEqual(result, {})
            self.assertTrue(pending.is_dir())  # not renamed

    def test_skips_non_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending = self._pending(tmp)
            with mock.patch.object(
                slug_rename, "is_real_interactive_session", return_value=True
            ):
                result = slug_rename.handle_slug_rename(
                    {"prompt": "<task-notification>\nfoo"},
                    session_dir=str(pending),
                    project_dir=tmp,
                )
            self.assertEqual(result, {})
            self.assertTrue(pending.is_dir())  # not renamed

    def test_renames_real_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pending = self._pending(tmp)
            with mock.patch.object(
                slug_rename, "is_real_interactive_session", return_value=True
            ):
                result = slug_rename.handle_slug_rename(
                    {"prompt": "Fix the TRUST-1377 login bug"},
                    session_dir=str(pending),
                    project_dir=tmp,
                )
            self.assertIn("systemMessage", result)
            self.assertFalse(pending.is_dir())
            renamed = list(pending.parent.glob("26-1200_TRUST-1377_*"))
            self.assertEqual(len(renamed), 1)


if __name__ == "__main__":
    unittest.main()
