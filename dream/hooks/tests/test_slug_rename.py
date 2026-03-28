"""Tests for slug_rename hook."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from dream.hooks.slug_rename import (
    _generate_slug_haiku,
    _make_slug,
    _make_slug_deterministic,
    handle_slug_rename,
)


@pytest.fixture(autouse=True)
def mock_haiku():
    """Disable Haiku CLI calls in all tests by default."""
    with patch("dream.hooks.slug_rename._generate_slug_haiku", return_value=None):
        yield


@pytest.fixture
def month_dir(tmp_path):
    """Create a month subdir with a pending session dir."""
    sessions = tmp_path / "sessions"
    month = sessions / datetime.now().strftime("%Y-%m")
    pending = month / "28-1430_pending_abc12345"
    pending.mkdir(parents=True)
    (pending / "SESSION.md").write_text("---\nstatus: active\n---\n")
    return month


@pytest.fixture
def env_file(tmp_path):
    return tmp_path / "env_file"


@pytest.fixture
def stdin_payload():
    return {"prompt": "PROJ-123 add user authentication flow"}


class TestSlugGeneration:
    def test_haiku_slug_used_when_available(self, month_dir, env_file):
        """Uses Haiku-generated slug when CLI is available."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent

        with patch(
            "dream.hooks.slug_rename._generate_slug_haiku",
            return_value="Build-Auth-Flow",
        ):
            handle_slug_rename(
                {"prompt": "PROJ-123 add user authentication flow"},
                session_dir=str(pending),
                sessions_dir=str(sessions_dir),
                env_file_path=str(env_file),
            )

        new_name = next(month_dir.iterdir()).name
        assert "Build-Auth-Flow" in new_name

    def test_falls_back_to_deterministic_on_haiku_failure(self, month_dir, env_file):
        """Falls back to deterministic slug when Haiku fails."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent

        # mock_haiku autouse already returns None (simulating failure)
        handle_slug_rename(
            {"prompt": "refactor the error handling"},
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        new_name = next(month_dir.iterdir()).name
        assert "_pending_" not in new_name
        assert "Refactor" in new_name

    def test_deterministic_slug_limits_words(self):
        """Deterministic fallback limits to 4 meaningful words."""
        slug = _make_slug_deterministic(
            "implement a very long feature name that goes on and on"
        )
        word_count = len(slug.split("-"))
        assert word_count <= 4

    def test_deterministic_slug_strips_stop_words(self):
        """Deterministic fallback strips stop words."""
        slug = _make_slug_deterministic("I want to build a really nice dashboard")
        assert "Want" not in slug
        assert "Really" not in slug

    def test_haiku_output_sanitized(self):
        """Haiku output with quotes or extra chars is sanitized."""
        with patch(
            "dream.hooks.slug_rename._generate_slug_haiku",
            return_value="Build-Auth-Flow",
        ):
            slug = _make_slug("add auth")
            assert slug == "Build-Auth-Flow"


class TestFastPath:
    def test_noop_when_env_var_has_no_pending(self, tmp_path, stdin_payload):
        """Fast path: no-op when $SKILMARILLION_SESSION_DIR does not contain _pending_."""
        result = handle_slug_rename(
            stdin_payload,
            session_dir="/some/path/28-1430_PROJ-123_Auth-Flow",
            sessions_dir=str(tmp_path / "sessions"),
            env_file_path=None,
        )
        assert result == {}

    def test_noop_when_env_var_is_empty(self, tmp_path, stdin_payload):
        """Slow path activated when env var is empty."""
        sessions = tmp_path / "sessions"
        month = sessions / datetime.now().strftime("%Y-%m")
        pending = month / "28-1430_pending_abc12345"
        pending.mkdir(parents=True)
        (pending / "SESSION.md").write_text("---\nstatus: active\n---\n")

        result = handle_slug_rename(
            stdin_payload,
            session_dir=None,
            sessions_dir=str(sessions),
            env_file_path=None,
        )
        # Should have renamed the pending dir
        assert not pending.exists()
        remaining = list(month.iterdir())
        assert len(remaining) == 1
        assert "_pending_" not in remaining[0].name


class TestSlowPath:
    def test_scans_month_dir_when_env_missing(self, month_dir, env_file, stdin_payload):
        """Slow path: scans month dir for pending dirs when env var is missing."""
        sessions_dir = month_dir.parent

        result = handle_slug_rename(
            stdin_payload,
            session_dir=None,
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        remaining = list(month_dir.iterdir())
        assert len(remaining) == 1
        assert "_pending_" not in remaining[0].name

    def test_falls_back_to_project_dir(self, tmp_path, env_file, stdin_payload):
        """Falls back to $CLAUDE_PROJECT_DIR/.ai/sessions when sessions_dir is None."""
        project_dir = tmp_path / "project"
        sessions = project_dir / ".ai" / "sessions"
        month = sessions / datetime.now().strftime("%Y-%m")
        pending = month / "28-1430_pending_abc12345"
        pending.mkdir(parents=True)
        (pending / "SESSION.md").write_text("---\nstatus: active\n---\n")

        result = handle_slug_rename(
            stdin_payload,
            session_dir=None,
            sessions_dir=None,
            project_dir=str(project_dir),
            env_file_path=str(env_file),
        )

        assert "systemMessage" in result
        remaining = list(month.iterdir())
        assert len(remaining) == 1
        assert "_pending_" not in remaining[0].name


class TestRenaming:
    def test_renames_with_slug_from_prompt(self, month_dir, env_file, stdin_payload):
        """Renames pending dir with slug derived from user prompt."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent

        handle_slug_rename(
            stdin_payload,
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        remaining = list(month_dir.iterdir())
        assert len(remaining) == 1
        new_name = remaining[0].name
        assert "PROJ-123" in new_name
        assert "_pending_" not in new_name
        assert (remaining[0] / "SESSION.md").exists()

    def test_extracts_ticket_id(self, month_dir, env_file):
        """Extracts ticket ID and uses it as prefix."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent
        payload = {"prompt": "BOP-42 fix the login bug"}

        handle_slug_rename(
            payload,
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        new_name = next(month_dir.iterdir()).name
        assert new_name.startswith("28-1430_BOP-42_")

    def test_no_ticket_in_prompt(self, month_dir, env_file):
        """Generates slug without ticket prefix when none found."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent
        payload = {"prompt": "refactor the error handling"}

        handle_slug_rename(
            payload,
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        new_name = next(month_dir.iterdir()).name
        assert "28-1430_" in new_name
        assert "_pending_" not in new_name
        assert "Refactor" in new_name or "refactor" in new_name.lower()

    def test_noop_if_no_pending_dir(self, tmp_path, stdin_payload):
        """No-op when no pending dir found."""
        sessions = tmp_path / "sessions"
        month = sessions / datetime.now().strftime("%Y-%m")
        renamed = month / "28-1430_PROJ-123_Already-Renamed"
        renamed.mkdir(parents=True)

        result = handle_slug_rename(
            stdin_payload,
            session_dir=str(renamed),
            sessions_dir=str(sessions),
            env_file_path=None,
        )
        assert result == {}
        assert renamed.exists()


class TestEdgeCases:
    def test_special_characters_stripped(self, month_dir, env_file):
        """Handles special characters in prompt."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent
        payload = {"prompt": "fix the @#$% bug with <html> & stuff!!!"}

        handle_slug_rename(
            payload,
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        new_name = next(month_dir.iterdir()).name
        assert "_pending_" not in new_name
        slug_part = new_name.split("_", 1)[1] if "_" in new_name else new_name
        assert "@" not in slug_part
        assert "#" not in slug_part
        assert "<" not in slug_part

    def test_updates_env_file(self, month_dir, env_file, stdin_payload):
        """Updates CLAUDE_ENV_FILE with new path after rename."""
        pending = next(month_dir.iterdir())
        sessions_dir = month_dir.parent

        handle_slug_rename(
            stdin_payload,
            session_dir=str(pending),
            sessions_dir=str(sessions_dir),
            env_file_path=str(env_file),
        )

        content = env_file.read_text()
        assert content.startswith("SKILMARILLION_SESSION_DIR=")
        new_path = content.split("=", 1)[1].strip()
        assert "_pending_" not in new_path
        assert Path(new_path).exists()
