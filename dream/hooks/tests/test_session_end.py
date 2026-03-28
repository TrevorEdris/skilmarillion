"""Tests for session_end hook."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from dream.hooks.session_end import handle_session_end


@pytest.fixture
def sessions_root(tmp_path):
    """Provide the sessions root directory."""
    root = tmp_path / "sessions"
    root.mkdir()
    return root


@pytest.fixture
def session_dir(sessions_root):
    """Create a realistic session dir with SESSION.md."""
    month = sessions_root / datetime.now().strftime("%Y-%m")
    sdir = month / "28-1430_PROJ-123_Some-Feature"
    sdir.mkdir(parents=True)
    (sdir / "SESSION.md").write_text(
        "---\ndate: 2026-03-28\nstatus: active\n---\n\n# Session\n\n## Prompts & Responses\n"
    )
    return sdir


@pytest.fixture
def stdin_payload():
    return {
        "session_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
        "cwd": "/some/project",
        "hook_event_name": "SessionEnd",
    }


class TestUpdatesSessionMd:
    def test_updates_status_to_completed(self, session_dir, stdin_payload):
        """Updates SESSION.md frontmatter status from active to completed."""
        result = handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
        )

        assert result == {}
        content = (session_dir / "SESSION.md").read_text()
        assert "status: completed" in content
        assert "status: active" not in content

    def test_adds_ended_timestamp(self, session_dir, stdin_payload):
        """Adds an ended timestamp to SESSION.md frontmatter."""
        result = handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
        )

        assert result == {}
        content = (session_dir / "SESSION.md").read_text()
        assert "ended:" in content


class TestGracefulDegradation:
    def test_noop_if_no_session_dir(self, stdin_payload):
        """Exits 0 with no side effects when no session dir found."""
        result = handle_session_end(
            stdin_payload,
            session_dir=None,
        )
        assert result == {}

    def test_noop_if_session_dir_missing(self, tmp_path, stdin_payload):
        """Exits 0 when session dir path doesn't exist on disk."""
        result = handle_session_end(
            stdin_payload,
            session_dir=str(tmp_path / "nonexistent"),
        )
        assert result == {}

    def test_noop_if_no_session_md(self, tmp_path, stdin_payload):
        """Exits 0 when session dir exists but SESSION.md is missing."""
        empty_dir = tmp_path / "empty_session"
        empty_dir.mkdir()
        result = handle_session_end(
            stdin_payload,
            session_dir=str(empty_dir),
        )
        assert result == {}


class TestIndexMd:
    def test_creates_index_with_header_if_missing(
        self, session_dir, sessions_root, stdin_payload
    ):
        """Creates INDEX.md with header row if it doesn't exist."""
        handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
            sessions_root=str(sessions_root),
        )

        index_md = sessions_root / "INDEX.md"
        assert index_md.exists()
        content = index_md.read_text()
        assert "| Date" in content
        assert "| Ticket" in content

    def test_appends_row_with_correct_fields(
        self, session_dir, sessions_root, stdin_payload
    ):
        """Appends row with date, ticket, title, file existence flags."""
        # Add a DISCOVERY.md to test file detection
        (session_dir / "DISCOVERY.md").write_text("# Discovery\n")

        handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
            sessions_root=str(sessions_root),
        )

        content = (sessions_root / "INDEX.md").read_text()
        lines = [l for l in content.strip().split("\n") if l.startswith("| 2026")]
        assert len(lines) == 1
        row = lines[0]
        assert "PROJ-123" in row
        assert "Some-Feature" in row or "Some Feature" in row
        # SESSION.md exists (Y), DISCOVERY.md exists (Y), PLAN.md doesn't (empty)
        assert "| Y |" in row

    def test_does_not_duplicate_rows(
        self, session_dir, sessions_root, stdin_payload
    ):
        """Does not add duplicate rows for the same session dir."""
        handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
            sessions_root=str(sessions_root),
        )
        handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
            sessions_root=str(sessions_root),
        )

        content = (sessions_root / "INDEX.md").read_text()
        data_lines = [l for l in content.strip().split("\n") if l.startswith("| 2026")]
        assert len(data_lines) == 1

    def test_handles_missing_sessions_root(self, session_dir, stdin_payload):
        """Appends INDEX.md gracefully when sessions_root is None."""
        result = handle_session_end(
            stdin_payload,
            session_dir=str(session_dir),
            sessions_root=None,
        )
        # SESSION.md should still be updated even without INDEX
        content = (session_dir / "SESSION.md").read_text()
        assert "status: completed" in content
