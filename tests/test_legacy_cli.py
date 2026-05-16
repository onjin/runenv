import os
import sys

import pytest

from runenv.legacy import run_legacy

from . import TESTS_DIR

TEST_FILE = os.path.join(TESTS_DIR, "env.test")


class TestLegacyCli:

    def test_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert run_legacy([TEST_FILE, sys.executable, "-c", ""]) == 0
        assert run_legacy([TEST_FILE, sys.executable, "-c", "raise SystemExit(1)"]) == 1
        assert os.environ.get("_RUNENV_WRAPPED") == "1"

    def test_run_from_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert run_legacy([TEST_FILE, "true"]) == 0
        assert run_legacy([TEST_FILE, "false"]) == 1
        assert os.environ.get("_RUNENV_WRAPPED") == "1"

    def test_nonexistent_command_shows_backtick_wrapped_name(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit):
            run_legacy([TEST_FILE, "nonexistent_cmd_xyz"])
        out = capsys.readouterr().out
        assert "`nonexistent_cmd_xyz`" in out

    def test_search_parent_finds_env_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        parent_dir = tmp_path
        child_dir = tmp_path / "child"
        child_dir.mkdir()
        env_file_name = "test_parent.env"
        env_file = parent_dir / env_file_name
        env_file.write_text("SEARCH_PARENT_VAR=found\n")
        monkeypatch.chdir(child_dir)
        ret = run_legacy(["--search-parent", "1", env_file_name, "true"])
        assert ret == 0
