import os
from unittest import mock

import pytest

from runenv import create_env, load_env
from runenv.api import find_env_file, lint_env

from . import TESTS_DIR


class TestApi:

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_create_env(self) -> None:
        os.environ["ALREADY_SET"] = "YES"

        environ = create_env(os.path.join(TESTS_DIR, "env.test"))
        assert environ.get("VARIABLED") == "some_lazy_variable_12"
        assert environ.get("STRING") == "some string with spaces"
        assert environ.get("NUMBER") == "12"
        assert environ.get("FLOAT") == "11.11"
        assert environ.get("EMPTY") == ""
        assert environ.get("SPACED") == "  spaced"
        assert environ.get("SINGLE_QUOTE") == 'so"me'
        assert environ.get("DOUBLE_QUOTE") == "so'me"
        assert environ.get("DOUBLE_QUOTE_WITH_COMMENT") == "so'me either"

        assert environ.get("QUOTED_WITH_HASH") == "some#one"
        assert environ.get("DOUBLE_QUOTED_WITH_HASH") == "some#one"

        assert "COMMENTED" not in environ
        assert "# COMMENTED" not in environ

        # external variable is not visible
        assert environ.get("ALREADY_SET", None) is None
        # but is loaded into our interpolation
        assert environ.get("FROM_ENV") == "MAYBE-YES"

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_from_default_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENV_STRING" not in os.environ
        assert "RUNENV_NUMBER" not in os.environ
        assert "RUNENV_FLOAT" not in os.environ

        load_env()

        assert "RUNENV_STRING" in os.environ
        assert "RUNENV_NUMBER" in os.environ
        assert "RUNENV_FLOAT" in os.environ
        assert os.environ.get("RUNENV_STRING") == "some string"
        assert os.environ.get("RUNENV_NUMBER") == "13"
        assert os.environ.get("RUNENV_FLOAT") == "12.12"

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_only_prefixed_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom", prefix="RUNENVC_S")

        assert "TRING" in os.environ
        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_only_prefixed_variables_without_strip_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom", prefix="RUNENVC_S", strip_prefix=False)

        assert "RUNENVC_STRING" in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_from_custom_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom")

        assert "RUNENVC_STRING" in os.environ
        assert "RUNENVC_NUMBER" in os.environ
        assert "RUNENVC_FLOAT" in os.environ
        assert os.environ.get("RUNENVC_STRING") == "custom string"
        assert os.environ.get("RUNENVC_NUMBER") == "14"
        assert os.environ.get("RUNENVC_FLOAT") == "14.14"

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_skip_if_wrapped_by_runenv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        # mark as runned by `envfile` wrapper
        os.environ["_RUNENV_WRAPPED"] = "1"

        load_env(env_file="env.custom")

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_force_even_wrapped_by_runenv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        os.environ["_RUNENV_WRAPPED"] = "1"

        load_env(env_file="env.custom", force=True)

        assert "RUNENVC_STRING" in os.environ
        assert "RUNENVC_NUMBER" in os.environ
        assert "RUNENVC_FLOAT" in os.environ
        assert os.environ.get("RUNENVC_STRING") == "custom string"
        assert os.environ.get("RUNENVC_NUMBER") == "14"
        assert os.environ.get("RUNENVC_FLOAT") == "14.14"

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_from_missing_file(self) -> None:
        load_env(env_file="env.missing")

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_search_parent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env_file = "env.search_parent"
        monkeypatch.chdir(os.path.join(TESTS_DIR, "search_parent", "project"))

        load_env(env_file=env_file)
        assert "PARENT" not in os.environ

        load_env(env_file=env_file)
        assert "PARENT" not in os.environ

        load_env(env_file=env_file, search_parent=1)
        assert "PARENT" in os.environ
        assert os.environ.get("PARENT") == "2"

        load_env(env_file=env_file, search_parent=2)
        assert "PARENT" in os.environ
        assert os.environ.get("PARENT") == "2"

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_search_grand_parent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        env_file = "env.search_grandparent"
        monkeypatch.chdir(os.path.join(TESTS_DIR, "search_grandparent", "project"))

        load_env(env_file=env_file)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file, search_parent=1)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file, search_parent=2)
        assert "GRAND_PARENT" in os.environ
        assert os.environ.get("GRAND_PARENT") == "3"


class TestFindEnvFile:
    def test_finds_dotenv(self, tmp_path):
        (tmp_path / ".env").write_text("A=1\n")
        result = find_env_file(tmp_path)
        assert result == tmp_path / ".env"

    def test_finds_json_when_no_dotenv(self, tmp_path):
        (tmp_path / ".env.json").write_text('{"A": "1"}')
        result = find_env_file(tmp_path)
        assert result == tmp_path / ".env.json"

    def test_finds_toml_when_no_dotenv_or_json(self, tmp_path):
        (tmp_path / ".env.toml").write_text('A = "1"\n')
        result = find_env_file(tmp_path)
        assert result == tmp_path / ".env.toml"

    def test_finds_yaml_last(self, tmp_path):
        (tmp_path / ".env.yaml").write_text("A: 1\n")
        result = find_env_file(tmp_path)
        assert result == tmp_path / ".env.yaml"

    def test_dotenv_takes_priority_over_json(self, tmp_path):
        (tmp_path / ".env").write_text("A=1\n")
        (tmp_path / ".env.json").write_text('{"A": "2"}')
        result = find_env_file(tmp_path)
        assert result == tmp_path / ".env"

    def test_returns_none_when_nothing_found(self, tmp_path):
        result = find_env_file(tmp_path)
        assert result is None

    def test_custom_filename(self, tmp_path):
        (tmp_path / "prod.env").write_text("A=1\n")
        result = find_env_file(tmp_path, filename="prod.env")
        assert result == tmp_path / "prod.env"

    def test_custom_filename_not_found_returns_none(self, tmp_path):
        result = find_env_file(tmp_path, filename="missing.env")
        assert result is None

    def test_search_parent_finds_file_in_parent(self, tmp_path):
        child = tmp_path / "sub"
        child.mkdir()
        (tmp_path / ".env").write_text("A=1\n")
        result = find_env_file(child, search_parent=1)
        assert result == tmp_path / ".env"

    def test_search_parent_zero_does_not_search_up(self, tmp_path):
        child = tmp_path / "sub"
        child.mkdir()
        (tmp_path / ".env").write_text("A=1\n")
        result = find_env_file(child, search_parent=0)
        assert result is None

    def test_search_parent_finds_in_current_dir_first(self, tmp_path):
        child = tmp_path / "sub"
        child.mkdir()
        (tmp_path / ".env").write_text("PARENT=1\n")
        (child / ".env").write_text("CHILD=1\n")
        result = find_env_file(child, search_parent=1)
        assert result == child / ".env"


class TestCreateEnvAdditional:
    def test_raises_value_error_when_no_file_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No env file found"):
            create_env()

    def test_raises_value_error_with_explicit_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No env file found"):
            create_env(env_file="nonexistent.env")

    def test_strict_mode_passes_through(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("KEY=${UNDEFINED_VAR}\n")
        from runenv.parser import ParseMessage
        result = create_env()
        assert result["KEY"] == ""

    def test_search_parent_resolves_file(self, tmp_path, monkeypatch):
        child = tmp_path / "app"
        child.mkdir()
        (tmp_path / ".env").write_text("APP_PORT=9000\n")
        monkeypatch.chdir(child)
        result = create_env(search_parent=1)
        assert result["APP_PORT"] == "9000"


class TestLoadEnvAdditional:
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_require_env_file_raises_when_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No env file found"):
            load_env(require_env_file=True)

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_file_without_require_silently_returns(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        load_env()
        assert "_RUNENV_WRAPPED" not in os.environ


class TestLintEnv:
    def test_returns_messages_list(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=value\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env()
        assert isinstance(messages, list)

    def test_clean_file_returns_no_errors(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=value\nOTHER=123\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env()
        assert not any(m.level == "error" for m in messages)

    def test_duplicate_key_returns_warning(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=a\nKEY=b\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env()
        assert any(m.level == "warning" and "duplicated" in m.message for m in messages)

    def test_raises_when_no_file_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No env file found"):
            lint_env()

    def test_explicit_file_path(self, tmp_path):
        env_file = tmp_path / "check.env"
        env_file.write_text("A=1\nA=2\n")
        messages = lint_env(env_file=str(env_file))
        assert any("duplicated" in m.message for m in messages)

    def test_strict_mode_warns_on_undefined_ref(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=${TOTALLY_MISSING_VAR}\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env(strict=True)
        assert any("undefined" in m.message for m in messages)

    def test_non_strict_silent_on_undefined_ref(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=${TOTALLY_MISSING_VAR}\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env(strict=False)
        assert not any("undefined" in m.message for m in messages)

    def test_prefix_filters_keys(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("APP_KEY=a\nOTHER=b\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env(prefix="APP_")
        info_msgs = [m for m in messages if "skip OTHER" in m.message]
        assert len(info_msgs) == 1

    def test_search_parent_finds_file(self, tmp_path, monkeypatch):
        child = tmp_path / "sub"
        child.mkdir()
        (tmp_path / ".env").write_text("KEY=value\n")
        monkeypatch.chdir(child)
        messages = lint_env(search_parent=1)
        assert isinstance(messages, list)

    def test_message_has_line_number(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("KEY=a\nKEY=b\n")
        monkeypatch.chdir(tmp_path)
        messages = lint_env()
        dup = [m for m in messages if "duplicated" in m.message]
        assert dup[0].line_number == 2
