from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

VARIABLE_LINE_REGEX = re.compile(r'^\s*(?:export\s+)?([\w.]+)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([^\n#]*?))\s*(?:#.*)?$')
VARIABLE_REFERENCE_REGEX = re.compile(r"\$\{(\w+)(?:(:-|:[\?+]|-)([^}]*))?\}")
POSIX_NAME_REGEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
EXPORT_BARE_REGEX = re.compile(r'^\s*export\s+[\w.]+\s*$')
TRIPLE_QUOTE_START_REGEX = re.compile(r'^\s*(?:export\s+)?([\w.]+)\s*=\s*("""|\'\'\')(.*)')

_ESCAPE_MAP: Dict[str, str] = {
    'n': '\n',
    't': '\t',
    'r': '\r',
    '"': '"',
    '\\': '\\',
}


def _process_escape_sequences(value: str) -> str:
    result = []
    i = 0
    while i < len(value):
        if value[i] == '\\' and i + 1 < len(value):
            escaped = value[i + 1]
            result.append(_ESCAPE_MAP.get(escaped, '\\' + escaped))
            i += 2
        else:
            result.append(value[i])
            i += 1
    return ''.join(result)


def _json_line_numbers(content: str, keys: Iterable[str]) -> Dict[str, int]:
    lines = content.splitlines()
    result: Dict[str, int] = {}
    for key in keys:
        pattern = re.compile(r'"' + re.escape(key) + r'"\s*:')
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                result[key] = i
                break
    return result


def _toml_line_numbers(content: str, keys: Iterable[str]) -> Dict[str, int]:
    lines = content.splitlines()
    result: Dict[str, int] = {}
    for key in keys:
        pattern = re.compile(r'^\s*' + re.escape(key) + r'\s*=')
        for i, line in enumerate(lines, 1):
            if pattern.match(line):
                result[key] = i
                break
    return result


def _yaml_line_numbers(content: str) -> Dict[str, int]:
    try:
        import yaml
    except ImportError:
        return {}
    node = yaml.compose(content)
    if not isinstance(node, yaml.MappingNode):
        return {}
    result: Dict[str, int] = {}
    for key_node, _ in node.value:
        result[str(key_node.value)] = key_node.start_mark.line + 1
    return result


def _normalize_structured_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass
class ParseOptions:
    prefix: Union[str, None] = None
    strip_prefix: bool = True


@dataclass
class ParseMessage:
    line_number: int
    level: str
    message: str


class EnvParser:
    def __init__(self, options: ParseOptions) -> None:
        self.options: ParseOptions = options
        self.raw_environ: Dict[str, str] = {}
        self._line_numbers: Dict[str, int] = {}
        self.final_environ: Dict[str, str] = {}
        self.messages: List[ParseMessage] = []

    def parse(self, env_file: Union[str, Path]) -> EnvParser:
        filename = env_file if isinstance(env_file, str) else env_file.name
        extension = Path(filename).suffix

        LOADERS = {
            ".json": self.load_json_file,
            ".yaml": self.load_yaml_file,
            ".toml": self.load_toml_file,
        }
        loader = LOADERS.get(extension, self.load_env_file)
        environ = loader(env_file)
        # skip not prefixed if prefix used
        for line_number, key, value in environ:
            if self.options.prefix and (not key.startswith(self.options.prefix) or key == self.options.prefix):
                msg = f"skip {key} without prefix {self.options.prefix}"
                logger.debug(msg)
                self.messages.append(
                    ParseMessage(
                        line_number=line_number,
                        level="info",
                        message=msg,
                    )
                )
                continue
            if self.options.prefix and self.options.strip_prefix:
                logger.debug("strip %s without prefix %s", key, self.options.prefix)
                key = key[len(self.options.prefix) :]

            if not POSIX_NAME_REGEX.match(key):
                msg = f"'{key}' is not a valid POSIX env var name"
                logger.debug(msg)
                self.messages.append(
                    ParseMessage(
                        line_number=line_number,
                        level="warning",
                        message=msg,
                    )
                )

            if key in self.raw_environ:
                msg = f"duplicated '{key}' variable, last value wins"
                logger.debug(msg)
                self.messages.append(
                    ParseMessage(
                        line_number=line_number,
                        level="warning",
                        message=msg,
                    )
                )
            self.raw_environ[key] = value
            self._line_numbers[key] = line_number

        self._find_cycles()
        expansion_errors: List[str] = []
        for key, value in self.raw_environ.items():
            try:
                self.final_environ[key] = substitute_variables(value, self.raw_environ)
            except ValueError as exc:
                msg = str(exc)
                expansion_errors.append(msg)
                self.messages.append(
                    ParseMessage(
                        line_number=self._line_numbers.get(key, 0),
                        level="error",
                        message=msg,
                    )
                )
        if expansion_errors:
            raise ValueError(expansion_errors[0])
        return self

    def _find_cycles(self) -> None:
        deps: Dict[str, Set[str]] = {
            key: {m[0] for m in VARIABLE_REFERENCE_REGEX.findall(value)} & self.raw_environ.keys()
            for key, value in self.raw_environ.items()
        }

        WHITE, GRAY, BLACK = 0, 1, 2
        colors: Dict[str, int] = {k: WHITE for k in deps}
        reported: Set[frozenset] = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            colors[node] = GRAY
            path.append(node)
            for neighbor in sorted(deps.get(node, set())):
                if colors.get(neighbor) == GRAY:
                    cycle = path[path.index(neighbor):]
                    cycle_key: frozenset = frozenset(cycle)
                    if cycle_key not in reported:
                        reported.add(cycle_key)
                        self.messages.append(ParseMessage(
                            line_number=0,
                            level="warning",
                            message="circular reference: " + " -> ".join(cycle + [neighbor]),
                        ))
                elif colors.get(neighbor, WHITE) == WHITE:
                    dfs(neighbor)
            path.pop()
            colors[node] = BLACK

        for node in sorted(deps.keys()):
            if colors[node] == WHITE:
                dfs(node)

    def load_env_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        environ: List[Tuple[int, str, str]] = []
        with open(env_file) as f:
            all_lines = list(enumerate(f, start=1))

        idx = 0
        while idx < len(all_lines):
            line_number, raw_line = all_lines[idx]
            line = raw_line.rstrip(os.linesep).strip()
            idx += 1

            if not line or line.startswith("#"):
                continue

            if EXPORT_BARE_REGEX.match(line):
                continue

            triple_match = TRIPLE_QUOTE_START_REGEX.match(line)
            if triple_match:
                key = triple_match.group(1)
                quote = triple_match.group(2)
                rest = triple_match.group(3)
                close_pos = rest.find(quote)
                if close_pos != -1:
                    value = rest[:close_pos]
                    if quote == '"""':
                        value = _process_escape_sequences(value)
                    environ.append((line_number, key, value))
                    continue

                parts: List[str] = [] if not rest else [rest]
                closed = False
                while idx < len(all_lines):
                    _, next_raw = all_lines[idx]
                    idx += 1
                    next_line = next_raw.rstrip(os.linesep)
                    close_pos = next_line.find(quote)
                    if close_pos != -1:
                        parts.append(next_line[:close_pos])
                        closed = True
                        break
                    parts.append(next_line)

                if not closed:
                    self.messages.append(ParseMessage(
                        line_number=line_number,
                        level="error",
                        message=f"unclosed triple-quote for '{key}'",
                    ))
                    continue

                value = "\n".join(parts)
                if quote == '"""':
                    value = _process_escape_sequences(value)
                environ.append((line_number, key, value))
                continue

            match = re.match(VARIABLE_LINE_REGEX, line)
            if match:
                key = match.group(1)
                if match.group(2) is not None:
                    value = _process_escape_sequences(match.group(2))
                else:
                    value = next(g for g in match.groups()[1:] if g is not None)
                environ.append((line_number, key, value))
            else:
                msg = "line not matched"
                logger.debug("%s '%s'", msg, line)
                self.messages.append(
                    ParseMessage(
                        line_number=line_number,
                        level="warning",
                        message=msg,
                    )
                )

        return environ

    def _check_structured_root(self, data: object, fmt: str) -> Dict[str, object]:
        if data is None:
            return {}
        if not isinstance(data, dict):
            msg = f"{fmt} root must be a mapping, got {type(data).__name__}"
            self.messages.append(ParseMessage(line_number=1, level="error", message=msg))
            raise ValueError(msg)
        return data  # type: ignore[return-value]

    def _iter_structured(
        self,
        data: Dict[str, object],
        fmt: str,
        line_numbers: Optional[Dict[str, int]] = None,
    ) -> List[Tuple[int, str, str]]:
        environ: List[Tuple[int, str, str]] = []
        for seq_num, (key, value) in enumerate(data.items(), start=1):
            ln = line_numbers.get(key, seq_num) if line_numbers is not None else seq_num
            if value is None:
                msg = f"'{key}' has null value, using empty string"
                self.messages.append(ParseMessage(line_number=ln, level="warning", message=msg))
                value_str = ""
            else:
                value_str = _normalize_structured_value(value)
            environ.append((ln, key, value_str))
        return environ

    def load_json_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        with open(env_file) as f:
            content = f.read()
        data = json.loads(content)
        root = self._check_structured_root(data, "JSON")
        return self._iter_structured(root, "JSON", _json_line_numbers(content, root.keys()))

    def load_yaml_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        try:
            import yaml
        except ImportError:
            sys.stderr.write("ERROR!!! To use YAML install runenv[yaml]\n")
            sys.exit(1)
        with open(env_file, "r") as f:
            content = f.read()
        data = yaml.safe_load(content)
        root = self._check_structured_root(data, "YAML")
        return self._iter_structured(root, "YAML", _yaml_line_numbers(content))

    def load_toml_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        if sys.version_info >= (3, 11):
            import tomllib as tomli
        else:
            try:
                import tomli
            except ImportError:
                sys.stderr.write("ERROR!!! To use TOML install runenv[toml]\n")
                sys.exit(1)
        with open(env_file, "rb") as f:
            raw = f.read()
        content = raw.decode("utf-8")
        data = tomli.loads(content)
        root = self._check_structured_root(data, "TOML")
        return self._iter_structured(root, "TOML", _toml_line_numbers(content, root.keys()))


def substitute_variables(value: str, env_vars: Dict[str, str]) -> str:
    def replace_match(match: re.Match[str]) -> str:
        name = match.group(1)
        op = match.group(2)
        operand = match.group(3) or ""

        in_env_vars = name in env_vars
        in_os_environ = name in os.environ
        if in_env_vars:
            resolved: Optional[str] = str(env_vars[name])
        elif in_os_environ:
            resolved = os.environ[name]
        else:
            resolved = None

        is_set = resolved is not None
        is_nonempty = is_set and resolved != ""

        if op is None:
            return resolved if is_set else ""
        if op == ":-":
            return resolved if is_nonempty else operand
        if op == "-":
            return resolved if is_set else operand
        if op == ":?":
            if not is_nonempty:
                raise ValueError(operand or f"{name}: unset or empty")
            return resolved  # type: ignore[return-value]
        if op == ":+":
            return operand if is_nonempty else ""
        return ""

    logger.debug(f"VALUE: {value} , type {type(value)}")
    return VARIABLE_REFERENCE_REGEX.sub(replace_match, str(value))


def parse_env_file(env_file: Union[str, Path], options: ParseOptions) -> Dict[str, str]:
    return EnvParser(options).parse(env_file).final_environ


def lint_env_file(env_file: Union[str, Path], options: ParseOptions) -> List[ParseMessage]:
    parser = EnvParser(options)
    try:
        parser.parse(env_file)
    except ValueError:
        pass
    return parser.messages
