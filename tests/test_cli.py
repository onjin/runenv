import os
import sys
from textwrap import dedent

import pytest

from runenv.cli import run

from . import TESTS_DIR

TEST_FILE = os.path.join(TESTS_DIR, "env.test")


def test_list_shows_env(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("ALREADY_SET", "external-var")
    run(["list", "--env-file", TEST_FILE])
    out = capsys.readouterr().out

    assert (
        out.strip()
        == dedent(
            """\
        DOUBLE_QUOTE=so'me
        DOUBLE_QUOTED_WITH_HASH=some#one
        DOUBLE_QUOTE_WITH_COMMENT=so'me either
        EMPTY=
        FLOAT=11.11
        FROM_ENV=MAYBE-external-var
        NUMBER=12
        QUOTED_WITH_HASH=some#one
        SINGLE_QUOTE=so"me
        SPACED=  spaced
        STRING=some string with spaces
        VARIABLED=some_lazy_variable_12
    """
        ).strip()
    )


def test_run_sets_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALREADY_SET", "external-var-run")
    run(["run", "--env-file", TEST_FILE, sys.executable])

    assert os.environ.get("_RUNENV_WRAPPED") == "1"

    # check variables
    assert os.environ.get("VARIABLED") == "some_lazy_variable_12"
    assert os.environ.get("STRING") == "some string with spaces"
    assert os.environ.get("NUMBER") == "12"
    assert os.environ.get("FLOAT") == "11.11"
    assert os.environ.get("EMPTY") == ""
    assert os.environ.get("SPACED") == "  spaced"
    assert os.environ.get("SINGLE_QUOTE") == 'so"me'
    assert os.environ.get("DOUBLE_QUOTE") == "so'me"
    assert os.environ.get("DOUBLE_QUOTE_WITH_COMMENT") == "so'me either"

    assert os.environ.get("QUOTED_WITH_HASH") == "some#one"
    assert os.environ.get("DOUBLE_QUOTED_WITH_HASH") == "some#one"

    assert "COMMENTED" not in os.environ
    assert "# COMMENTED" not in os.environ

    # external variable is loaded into our interpolation
    assert os.environ.get("FROM_ENV") == "MAYBE-external-var-run"
