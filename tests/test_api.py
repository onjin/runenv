import os
from unittest import mock

from runenv import create_env, load_env

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
    def test_load_env_from_default_file(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

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
    def test_load_env_only_prefixed_variables(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom", prefix="RUNENVC_S")

        assert "TRING" in os.environ
        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_only_prefixed_variables_without_strip_prefix(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom", prefix="RUNENVC_S", strip_prefix=False)

        assert "RUNENVC_STRING" in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_load_env_from_custom_file(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

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
    def test_load_env_skip_if_wrapped_by_runenv(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

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
    def test_load_env_force_even_wrapped_by_runenv(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

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
    def test_search_parent(self) -> None:
        env_file = "env.search_parent"
        os.chdir(os.path.join(TESTS_DIR, "search_parent", "project"))

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
    def test_search_grand_parent(self) -> None:
        env_file = "env.search_grandparent"
        os.chdir(os.path.join(TESTS_DIR, "search_grandparent", "project"))

        load_env(env_file=env_file)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file, search_parent=1)
        assert "GRAND_PARENT" not in os.environ

        load_env(env_file=env_file, search_parent=2)
        assert "GRAND_PARENT" in os.environ
        assert os.environ.get("GRAND_PARENT") == "3"
