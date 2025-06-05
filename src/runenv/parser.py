from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

logger = logging.getLogger(__name__)

# Regular expression to match variable references like ${VAR_NAME}
VARIABLE_LINE_REGEX = re.compile(r'^\s*([\w.]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\n#]*?))\s*(?:#.*)?$')
VARIABLE_REFERENCE_REGEX = re.compile(r"\$\{(\w+)\}")


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
            if self.options.prefix and key != self.options.prefix and not key.startswith(self.options.prefix):

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
            if self.options.prefix and key != self.options.prefix and self.options.strip_prefix:
                logger.debug("strip %s without prefix %s", key, self.options.prefix)
                key = key[len(self.options.prefix) :]

            if key in self.raw_environ:
                msg = f"duplicated '{key}' variable"
                logger.debug(msg)
                self.messages.append(
                    ParseMessage(
                        line_number=line_number,
                        level="error",
                        message=msg,
                    )
                )
            self.raw_environ[key] = value

        # Perform lazy evaluation after parsing all variables
        for key, value in self.raw_environ.items():
            self.final_environ[key] = substitute_variables(value, self.raw_environ)
        return self

    def load_env_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        environ: List[Tuple[int, str, str]] = []
        with open(env_file) as f:

            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.rstrip(os.linesep)

                # Strip leading and trailing whitespace from the line
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Match key-value pairs (supports inline comments and empty values)
                match = re.match(VARIABLE_LINE_REGEX, line)

                if match:
                    key = match.group(1)
                    # Only one of groups 2, 3, or 4 will contain the value
                    value = next(g for g in match.groups()[1:] if g is not None)

                    # Strip quotes if they exist
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

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

    def load_json_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        environ: List[Tuple[int, str, str]] = []
        with open(env_file) as f:
            line_number = 1
            for key, value in json.loads(f.read()).items():
                environ.append((line_number, key, value))
                line_number += 1
        return environ

    def load_yaml_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        try:
            import yaml
        except ImportError:
            sys.stderr.write("ERROR!!! To use YAML install runenv[yaml]\n")
            sys.exit(1)
        environ: List[Tuple[int, str, str]] = []
        with open(env_file, "r") as f:
            line_number = 1
            for key, value in yaml.safe_load(f.read()).items():
                environ.append((line_number, key, value))
                line_number += 1
        return environ

    def load_toml_file(self, env_file: Union[str, Path]) -> List[Tuple[int, str, str]]:
        if sys.version_info >= (3, 11):
            import tomllib as tomli
        else:
            try:
                import tomli
            except ImportError:
                sys.stderr.write("ERROR!!! To use YAML install runenv[toml]\n")
                sys.exit(1)
        environ: List[Tuple[int, str, str]] = []
        with open(env_file, "rb") as f:
            line_number = 1
            for key, value in tomli.load(f).items():
                environ.append((line_number, key, value))
                line_number += 1
        return environ


def substitute_variables(value: str, env_vars: Dict[str, str]) -> str:
    """
    Recursively resolve variable references (e.g., ${VAR_NAME}) in a value using env_vars.
    """

    def replace_match(match: re.Match[str]) -> str:
        var_name = match.group(1)
        # Resolve variable from env_vars or os.environ
        return str(env_vars.get(var_name, os.environ.get(var_name, "")))

    # Replace all occurrences of ${VAR_NAME} in the value
    logger.debug(f"VALUE: {value} , type {type(value)}")
    return VARIABLE_REFERENCE_REGEX.sub(replace_match, str(value))


def parse_env_file(env_file: Union[str, Path], options: ParseOptions) -> Dict[str, str]:
    return EnvParser(options).parse(env_file).final_environ


def lint_env_file(env_file: Union[str, Path], options: ParseOptions) -> List[ParseMessage]:
    return EnvParser(options).parse(env_file).messages
