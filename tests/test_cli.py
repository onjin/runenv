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


def test_run_nonexistent_command_shows_backtick_wrapped_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        run(["run", "--env-file", TEST_FILE, "--", "nonexistent_cmd_xyz"])
    out = capsys.readouterr().out
    assert "does not exist" in out
    assert "`" in out


def test_run_default_is_silent(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_file = tmp_path / "test.env"
    env_file.write_text("TEST=3\nTEST=2\n")
    monkeypatch.chdir(tmp_path)
    ret = run(["run", "--env-file", str(env_file), sys.executable])
    captured = capsys.readouterr()
    assert captured.err == ""
    assert ret == 0


def test_lint_warning_level_shows_warnings_on_stderr(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=3\nTEST=2\n")
    run(["lint", "--env-file", str(env_file), "--lint-level", "warning"])
    captured = capsys.readouterr()
    assert "[warning]" in captured.err


def test_lint_fail_on_warning_exits_nonzero(
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=3\nTEST=2\n")
    ret = run(["lint", "--env-file", str(env_file), "--lint-level", "warning", "--fail-on", "warning"])
    assert ret == 1


def test_lint_none_level_suppresses_output(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=3\nTEST=2\n")
    run(["lint", "--env-file", str(env_file), "--lint-level", "none"])
    captured = capsys.readouterr()
    assert captured.err == ""


def test_run_fail_on_warning_aborts_before_running(
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=3\nTEST=2\n")
    ret = run(["run", "--env-file", str(env_file), "--fail-on", "warning", sys.executable])
    assert ret == 1


def test_lint_exits_nonzero_on_error_by_default(
    tmp_path: pytest.TempPathFactory,
) -> None:
    env_file = tmp_path / "test.json"
    env_file.write_text("[1,2,3]")
    ret = run(["lint", "--env-file", str(env_file)])
    assert ret == 1


def test_lint_exits_zero_on_warnings_by_default(
    tmp_path,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=3\nTEST=2\n")
    ret = run(["lint", "--env-file", str(env_file)])
    assert ret == 0


def test_lint_info_level_shows_info_messages(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    env_file = tmp_path / "test.env"
    env_file.write_text("APP_FOO=bar\nOTHER=val\n")
    monkeypatch.chdir(tmp_path)
    run(["lint", "--env-file", str(env_file), "--prefix", "APP_", "--lint-level", "info"])
    captured = capsys.readouterr()
    assert "[info]" in captured.err


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


@pytest.mark.parametrize("subcommand", ["run", "list", "lint"])
def test_missing_explicit_env_file_shows_filename(
    subcommand: str,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run([subcommand, "--env-file", "missing.env", sys.executable] if subcommand == "run" else [subcommand, "--env-file", "missing.env"])
    out = capsys.readouterr().out
    assert "missing.env" in out
    assert "None" not in out


def test_bare_runenv_prints_help(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rc = run([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "usage" in out.lower()


@pytest.mark.parametrize("subcommand", ["run", "list", "lint"])
def test_no_env_file_found_shows_searched_names(
    subcommand: str,
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run([subcommand, sys.executable] if subcommand == "run" else [subcommand])
    out = capsys.readouterr().out
    assert ".env" in out
    assert "None" not in out


def test_value_error_from_api_caught_at_cli_boundary(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import runenv.cli as cli_module

    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    monkeypatch.chdir(tmp_path)

    def _raise(*args, **kwargs):
        raise ValueError("No env file found")

    monkeypatch.setattr(cli_module, "create_env", _raise)

    with pytest.raises(SystemExit) as exc_info:
        run(["list", "--env-file", str(env_file)])

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "No env file found" in out
