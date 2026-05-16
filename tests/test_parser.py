import pytest

from runenv.parser import (
    EnvParser,
    ParseOptions,
    _json_line_numbers,
    _toml_line_numbers,
    _yaml_line_numbers,
    lint_env_file,
    parse_env_file,
    substitute_variables,
)


class TestStripPrefixEqualsPrefix:
    def test_key_equal_to_prefix_is_skipped(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("APP_=should_be_skipped\nAPP_FOO=bar\n")
        result = parse_env_file(env_file, ParseOptions(prefix="APP_", strip_prefix=True))
        assert "APP_" not in result
        assert "FOO" in result
        assert result["FOO"] == "bar"


class TestDuplicateKey:
    def test_last_value_wins(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("TEST=3\nTEST=2\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["TEST"] == "2"

    def test_duplicate_key_warning_message(self, tmp_path):
        env_file = tmp_path / "test.env"
        env_file.write_text("TEST=3\nTEST=2\n")
        messages = lint_env_file(env_file, ParseOptions())
        warnings = [m for m in messages if m.level == "warning"]
        assert len(warnings) >= 1
        assert any("last value wins" in m.message for m in warnings)


class TestStructuredLoaders:
    def test_empty_json_file_raises(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text("")
        with pytest.raises(Exception):
            parse_env_file(env_file, ParseOptions())

    def test_json_null_root_returns_empty_dict(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text("null")
        result = parse_env_file(env_file, ParseOptions())
        assert result == {}

    def test_json_list_root_raises_value_error(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text("[1,2,3]")
        with pytest.raises(ValueError, match="mapping"):
            parse_env_file(env_file, ParseOptions())

    def test_json_null_value_becomes_empty_string(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text('{"KEY": null}')
        result = parse_env_file(env_file, ParseOptions())
        assert result["KEY"] == ""

    def test_json_null_value_lint_warning(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text('{"KEY": null}')
        messages = lint_env_file(env_file, ParseOptions())
        warnings = [m for m in messages if m.level == "warning"]
        assert len(warnings) >= 1
        assert any("null value" in m.message for m in warnings)

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        env_file = tmp_path / "test.yaml"
        env_file.write_text("")
        result = parse_env_file(env_file, ParseOptions())
        assert result == {}

    def test_yaml_list_root_raises_value_error(self, tmp_path):
        env_file = tmp_path / "test.yaml"
        env_file.write_text("- foo\n- bar\n")
        with pytest.raises(ValueError, match="mapping"):
            parse_env_file(env_file, ParseOptions())

    def test_yaml_null_value_becomes_empty_string(self, tmp_path):
        env_file = tmp_path / "test.yaml"
        env_file.write_text("KEY:\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["KEY"] == ""

    def test_empty_toml_returns_empty_dict(self, tmp_path):
        env_file = tmp_path / "test.toml"
        env_file.write_bytes(b"")
        result = parse_env_file(env_file, ParseOptions())
        assert result == {}


class TestStructuredLoaderLineNumbers:
    def test_json_null_value_warning_has_real_line_number(self, tmp_path):
        env_file = tmp_path / "test.json"
        env_file.write_text('{\n  "A": "hello",\n  "B": null,\n  "C": "world"\n}')
        messages = lint_env_file(env_file, ParseOptions())
        null_warnings = [m for m in messages if "null value" in m.message]
        assert len(null_warnings) == 1
        assert null_warnings[0].line_number == 3

    def test_yaml_null_value_warning_has_real_line_number(self, tmp_path):
        env_file = tmp_path / "test.yaml"
        env_file.write_text("A: hello\nB: ~\nC: world\n")
        messages = lint_env_file(env_file, ParseOptions())
        null_warnings = [m for m in messages if "null value" in m.message]
        assert len(null_warnings) == 1
        assert null_warnings[0].line_number == 2

    def test_toml_prefix_skip_has_real_line_number(self, tmp_path):
        env_file = tmp_path / "test.toml"
        env_file.write_text('APP_FOO = "bar"\nAPP_BAR = "baz"\nOTHER = "x"\n')
        messages = lint_env_file(env_file, ParseOptions(prefix="APP_"))
        skip_infos = [m for m in messages if "skip OTHER" in m.message]
        assert len(skip_infos) == 1
        assert skip_infos[0].line_number == 3

    def test_json_line_numbers_helper(self):
        content = '{\n  "FOO": "bar",\n  "BAZ": 42\n}'
        result = _json_line_numbers(content, ["FOO", "BAZ"])
        assert result == {"FOO": 2, "BAZ": 3}

    def test_toml_line_numbers_helper(self):
        content = 'FOO = "bar"\nBAZ = 42\n'
        result = _toml_line_numbers(content, ["FOO", "BAZ"])
        assert result == {"FOO": 1, "BAZ": 2}

    def test_yaml_line_numbers_helper(self):
        content = "FOO: bar\nBAZ: 42\n"
        result = _yaml_line_numbers(content)
        assert result == {"FOO": 1, "BAZ": 2}

    def test_yaml_line_numbers_empty_returns_empty(self):
        assert _yaml_line_numbers("") == {}

    def test_yaml_line_numbers_non_mapping_returns_empty(self):
        assert _yaml_line_numbers("- foo\n- bar\n") == {}


class TestVariableSubstitution:
    def test_var_resolved_from_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("BASE=hello\nDERIVED=${BASE}_world\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["DERIVED"] == "hello_world"

    def test_var_falls_back_to_os_environ(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PARENT_VAR", "from-shell")
        env_file = tmp_path / ".env"
        env_file.write_text("CHILD=${PARENT_VAR}\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["CHILD"] == "from-shell"

    def test_env_file_var_takes_precedence_over_os_environ(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MYVAR", "from-shell")
        env_file = tmp_path / ".env"
        env_file.write_text("MYVAR=from-file\nCHILD=${MYVAR}\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["CHILD"] == "from-file"

    def test_undefined_var_expands_to_empty_string(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("CHILD=${TOTALLY_UNDEFINED_XYZ}\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["CHILD"] == ""

    def test_substitute_variables_directly(self):
        env_vars = {"FOO": "bar"}
        assert substitute_variables("${FOO}", env_vars) == "bar"
        assert substitute_variables("${MISSING}", env_vars) == ""
        assert substitute_variables("no-refs", env_vars) == "no-refs"


class TestCircularReferences:
    def test_direct_cycle_reported_as_warning(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=${B}\nB=${A}\n")
        messages = lint_env_file(env_file, ParseOptions())
        warnings = [m for m in messages if m.level == "warning" and "circular" in m.message]
        assert len(warnings) == 1
        assert "A" in warnings[0].message
        assert "B" in warnings[0].message

    def test_self_reference_reported_as_warning(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=${A}\n")
        messages = lint_env_file(env_file, ParseOptions())
        warnings = [m for m in messages if m.level == "warning" and "circular" in m.message]
        assert len(warnings) == 1
        assert "A" in warnings[0].message

    def test_longer_cycle_reported(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=${B}\nB=${C}\nC=${A}\n")
        messages = lint_env_file(env_file, ParseOptions())
        warnings = [m for m in messages if m.level == "warning" and "circular" in m.message]
        assert len(warnings) == 1

    def test_no_cycle_produces_no_warning(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("BASE=hello\nDERIVED=${BASE}_world\n")
        messages = lint_env_file(env_file, ParseOptions())
        circular = [m for m in messages if "circular" in m.message]
        assert circular == []

    def test_parse_still_succeeds_despite_cycle(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("A=${B}\nB=${A}\nSAFE=ok\n")
        result = parse_env_file(env_file, ParseOptions())
        assert result["SAFE"] == "ok"
