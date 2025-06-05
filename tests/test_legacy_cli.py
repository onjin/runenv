import os

import pytest

from runenv.legacy import run_legacy

from . import TESTS_DIR

TEST_FILE = os.path.join(TESTS_DIR, "env.test")


class TestLegacyCli:

    def test_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert run_legacy([TEST_FILE, "/bin/true"]) == 0
        assert run_legacy([TEST_FILE, "/bin/false"]) == 1
        assert os.environ.get("_RUNENV_WRAPPED") == "1"

    def test_run_from_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert run_legacy([TEST_FILE, "true"]) == 0
        assert run_legacy([TEST_FILE, "false"]) == 1
        assert os.environ.get("_RUNENV_WRAPPED") == "1"
