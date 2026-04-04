"""Tests for session_start hook."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from plan.hooks.session_start import handle_session_start


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
        self, tmp_sessions, env_file, stdin_payload, tmp_path
    ):
        """Creates YYYY-MM/DD-HHMM_pending_xxx/ with SESSION.md when none exists."""
        # Create a project dir whose .ai/sessions points to tmp_sessions
        project_dir = tmp_path / "project"
        ai_sessions = project_dir / ".ai" / "sessions"
        ai_sessions.mkdir(parents=True)
        # Symlink so _resolve_sessions_dir finds it
        import shutil
        shutil.rmtree(str(ai_sessions))
        ai_sessions.symlink_to(tmp_sessions)
        tmp_sessions.mkdir(parents=True, exist_ok=True)

        result = handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
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
        self, tmp_path, env_file, stdin_payload
    ):
        """SESSION.md contains an empty Prompts & Responses section."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        sessions_dir = project_dir / ".ai" / "sessions"
        month_dir = next(sessions_dir.iterdir())
        session_dir = next(month_dir.iterdir())
        content = (session_dir / "SESSION.md").read_text()
        assert "## Prompts & Responses" in content


class TestIdempotent:
    def test_reuses_existing_pending_dir(
        self, tmp_path, env_file, stdin_payload
    ):
        """If a pending dir already exists in current month, reuses it."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        # First call creates the dir
        handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        sessions_dir = project_dir / ".ai" / "sessions"
        month_dir = next(sessions_dir.iterdir())
        first_dirs = list(month_dir.iterdir())
        assert len(first_dirs) == 1
        first_session_md_content = (first_dirs[0] / "SESSION.md").read_text()

        # Second call should reuse, not create a new dir
        handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        session_dirs = list(month_dir.iterdir())
        assert len(session_dirs) == 1
        # SESSION.md content should be unchanged
        assert (session_dirs[0] / "SESSION.md").read_text() == first_session_md_content


class TestEnvVarRouting:
    def test_falls_back_to_project_dir(self, tmp_path, env_file, stdin_payload):
        """Uses $CLAUDE_PROJECT_DIR/.ai/sessions to resolve sessions root."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        stdin_payload["cwd"] = str(project_dir)

        result = handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        expected = project_dir / ".ai" / "sessions"
        assert expected.exists()


class TestEnvFile:
    def test_writes_session_dir_to_env_file(
        self, tmp_path, env_file, stdin_payload
    ):
        """Writes SKILMARILLION_SESSION_DIR=<path> to $CLAUDE_ENV_FILE."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        assert env_file.exists()
        content = env_file.read_text()
        assert content.startswith("SKILMARILLION_SESSION_DIR=")
        path_value = content.split("=", 1)[1].strip()
        assert "_pending_" in path_value
        assert Path(path_value).exists()


class TestGracefulDegradation:
    def test_no_project_dir(self, env_file, stdin_payload):
        """Exits 0 with no dir created when project dir is not set."""
        result = handle_session_start(
            stdin_payload,
            project_dir=None,
            env_file_path=str(env_file),
        )

        assert result == {}
        # env_file should not be written
        assert not env_file.exists()

    def test_unwritable_env_file_does_not_crash(
        self, tmp_path, stdin_payload
    ):
        """Handles missing/unwritable CLAUDE_ENV_FILE gracefully."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        result = handle_session_start(
            stdin_payload,
            project_dir=str(project_dir),
            env_file_path=None,
        )

        assert "systemMessage" in result
        # Session dir should still be created
        sessions_dir = project_dir / ".ai" / "sessions"
        month_dirs = list(sessions_dir.iterdir())
        assert len(month_dirs) == 1
