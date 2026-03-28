"""Tests for session_start hook."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from dream.hooks.session_start import handle_session_start


@pytest.fixture
def tmp_sessions(tmp_path):
    """Provide a temporary sessions root directory."""
    return tmp_path / "sessions"


@pytest.fixture
def env_file(tmp_path):
    """Provide a temporary CLAUDE_ENV_FILE path."""
    return tmp_path / "env_file"


@pytest.fixture
def stdin_payload():
    """Build a minimal SessionStart stdin payload."""
    return {
        "session_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
        "cwd": "/some/project",
        "hook_event_name": "SessionStart",
    }


class TestCreatesSessionDir:
    def test_creates_month_subdir_and_session_dir(
        self, tmp_sessions, env_file, stdin_payload
    ):
        """Creates YYYY-MM/DD-HHMM_pending_xxx/ with SESSION.md when none exists."""
        result = handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        # Month subdir should exist
        month_dirs = list(tmp_sessions.iterdir())
        assert len(month_dirs) == 1
        month_dir = month_dirs[0]
        assert month_dir.name == datetime.now().strftime("%Y-%m")

        # Session dir should exist inside month dir
        session_dirs = list(month_dir.iterdir())
        assert len(session_dirs) == 1
        session_dir = session_dirs[0]
        assert "_pending_" in session_dir.name
        assert session_dir.name.startswith(datetime.now().strftime("%d-"))

        # SESSION.md should exist with frontmatter
        session_md = session_dir / "SESSION.md"
        assert session_md.exists()
        content = session_md.read_text()
        assert "status: active" in content
        assert "date:" in content

    def test_session_md_has_prompts_section(
        self, tmp_sessions, env_file, stdin_payload
    ):
        """SESSION.md contains an empty Prompts & Responses section."""
        handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=str(env_file),
        )

        month_dir = next(tmp_sessions.iterdir())
        session_dir = next(month_dir.iterdir())
        content = (session_dir / "SESSION.md").read_text()
        assert "## Prompts & Responses" in content


class TestIdempotent:
    def test_reuses_existing_pending_dir(
        self, tmp_sessions, env_file, stdin_payload
    ):
        """If a pending dir already exists in current month, reuses it."""
        # First call creates the dir
        handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=str(env_file),
        )

        month_dir = next(tmp_sessions.iterdir())
        first_dirs = list(month_dir.iterdir())
        assert len(first_dirs) == 1
        first_session_md_content = (first_dirs[0] / "SESSION.md").read_text()

        # Second call should reuse, not create a new dir
        handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=str(env_file),
        )

        session_dirs = list(month_dir.iterdir())
        assert len(session_dirs) == 1
        # SESSION.md content should be unchanged
        assert (session_dirs[0] / "SESSION.md").read_text() == first_session_md_content


class TestEnvVarRouting:
    def test_uses_skilmarillion_sessions_dir(
        self, tmp_sessions, env_file, stdin_payload
    ):
        """Uses $SKILMARILLION_SESSIONS_DIR when set."""
        custom_dir = tmp_sessions / "custom"
        result = handle_session_start(
            stdin_payload,
            sessions_dir=str(custom_dir),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        assert custom_dir.exists()
        month_dirs = list(custom_dir.iterdir())
        assert len(month_dirs) == 1

    def test_falls_back_to_project_dir(self, tmp_path, env_file, stdin_payload):
        """Falls back to $CLAUDE_PROJECT_DIR/.ai/sessions when env var unset."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        stdin_payload["cwd"] = str(project_dir)

        result = handle_session_start(
            stdin_payload,
            sessions_dir=None,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        expected = project_dir / ".ai" / "sessions"
        assert expected.exists()


class TestEnvFile:
    def test_writes_session_dir_to_env_file(
        self, tmp_sessions, env_file, stdin_payload
    ):
        """Writes SKILMARILLION_SESSION_DIR=<path> to $CLAUDE_ENV_FILE."""
        handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=str(env_file),
        )

        assert env_file.exists()
        content = env_file.read_text()
        assert content.startswith("SKILMARILLION_SESSION_DIR=")
        path_value = content.split("=", 1)[1].strip()
        assert "_pending_" in path_value
        assert Path(path_value).exists()


class TestGracefulDegradation:
    def test_no_project_dir_no_sessions_dir(self, env_file, stdin_payload):
        """Exits 0 with no dir created when neither env var is set."""
        result = handle_session_start(
            stdin_payload,
            sessions_dir=None,
            project_dir=None,
            env_file_path=str(env_file),
        )

        assert result == {}
        # env_file should not be written
        assert not env_file.exists()

    def test_unwritable_env_file_does_not_crash(
        self, tmp_sessions, stdin_payload
    ):
        """Handles missing/unwritable CLAUDE_ENV_FILE gracefully."""
        result = handle_session_start(
            stdin_payload,
            sessions_dir=str(tmp_sessions),
            env_file_path=None,
        )

        assert "systemMessage" in result
        # Session dir should still be created
        month_dirs = list(tmp_sessions.iterdir())
        assert len(month_dirs) == 1
