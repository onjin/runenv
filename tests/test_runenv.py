#!/usr/bin/env python

"""
test_runenv.
----------------------------------

Tests for `runenv` module.
"""

import os
import sys
import unittest
from contextlib import contextmanager
from io import StringIO

import pytest

from runenv import create_env, load_env, run

from . import TESTS_DIR


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


class TestRunenv(unittest.TestCase):
    def setUp(self) -> None:
        self.env_file = os.path.join(TESTS_DIR, "env.test")

    def tearDown(self) -> None:
        variables = (
            "VARIABLED",
            "STRING",
            "NUMBER",
            "FLOAT",
            "EMPTY",
            "SPACED",
            "COMMENTED",
            "RUNENV_STRING",
            "RUNENV_NUMBER",
            "RUNENV_FLOAT",
            "RUNENVC_STRING",
            "RUNENVC_NUMBER",
            "RUNENVC_FLOAT",
            "_RUNENV_WRAPPED",
            "SINGLE_QUOTE",
            "DOUBLE_QUOTE",
            "DOUBLE_QUOTE_WITH_COMMENT",
        )
        for k in variables:
            if k in os.environ:
                del os.environ[k]

    def test_create_env(self) -> None:
        environ = create_env(self.env_file)
        assert environ.get("VARIABLED") == "some_lazy_variable_12"
        assert environ.get("STRING") == "some string with spaces"
        assert environ.get("NUMBER") == "12"
        assert environ.get("FLOAT") == "11.11"
        assert environ.get("EMPTY") == ""
        assert environ.get("SPACED") == "  spaced"
        assert environ.get("SINGLE_QUOTE") == 'so"me'
        assert environ.get("DOUBLE_QUOTE") == "so'me"
        assert environ.get("DOUBLE_QUOTE_WITH_COMMENT") == "so'me either"
        assert "COMMENTED" not in environ
        assert "# COMMENTED" not in environ

    @pytest.mark.skipif(
        "linux" not in sys.platform,
        reason="works on linux",
    )
    def test_run(self) -> None:
        assert run([self.env_file, "/bin/true"]) == 0
        assert run([self.env_file, "/bin/false"]) == 1
        with capture(run, [self.env_file, "/usr/bin/env"]) as output:
            assert "_RUNENV_WRAPPED", output

    def test_run_from_path(self) -> None:
        assert run([self.env_file, "true"]) == 0
        assert run([self.env_file, "false"]) == 1
        with capture(run, [self.env_file, "env"]) as output:
            assert "_RUNENV_WRAPPED", output

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

    def test_load_env_only_prefixed_variables_without_strip_prefix(self) -> None:
        os.chdir(os.path.join(TESTS_DIR, "cwd"))

        assert "RUNENVC_STRING" not in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

        load_env(env_file="env.custom", prefix="RUNENVC_S", strip_prefix=False)

        assert "RUNENVC_STRING" in os.environ
        assert "RUNENVC_NUMBER" not in os.environ
        assert "RUNENVC_FLOAT" not in os.environ

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

    def test_load_env_from_missing_file(self) -> None:
        load_env(env_file="env.missing")

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


if __name__ == "__main__":
    unittest.main()
