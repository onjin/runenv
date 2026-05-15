import pytest

from runenv.parser import EnvParser, ParseOptions, lint_env_file, parse_env_file


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
