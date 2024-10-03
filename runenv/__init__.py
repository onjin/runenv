# SPDX-FileCopyrightText: 2015-present Marek Wywiał <onjinx@gmail.com>
#
# SPDX-License-Identifier: MIT
import argparse
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
from typing import Dict, Optional, Sequence, Union

from runenv.__about__ import __version__

logger = logging.getLogger("runenv")

# Regular expression to match variable references like ${VAR_NAME}
VARIABLE_REFERENCE_REGEX = re.compile(r"\$\{(\w+)\}")


def add_stdout_handler(verbosity: int):
    """Adds stdout handler with given verbosity to logger.

    Args:
        logger (Logger) - python logger instance
        verbosity (int) - target verbosity
                          1 - ERROR
                          2 - INFO
                          3 - DEBUG

    Usage:
        add_stdout_handler(verbosity=3)

    """

    v_map = {1: logging.ERROR, 2: logging.INFO, 3: logging.DEBUG}
    level = v_map.get(verbosity, 1)
    logging.basicConfig(level=level)


def run(argv: Optional[Sequence[str]] = None):
    prog = "runenv"
    description = "Run program with given environment file loaded"

    parser = argparse.ArgumentParser(prog=prog, description=description)

    _ = parser.add_argument("env_file", help="Environment file to load")
    _ = parser.add_argument("command", help="Command to run with loaded environment")

    _ = parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    _ = parser.add_argument(
        "-v",
        "--verbosity",
        action="store",
        default=1,
        type=int,
        help="verbosity level, 1 - (ERROR, default), 2 - (INFO) or 3 - (DEBUG)",
        choices=[1, 2, 3],
    )
    _ = parser.add_argument(
        "-p",
        "--prefix",
        action="store",
        type=str,
        help="Load only variables with given prefix",
    )
    _ = parser.add_argument(
        "-s",
        "--strip_prefix",
        action="store_true",
        help="Strip prefix given with --prefix from environment variables names",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Return parsed .env instead of running command",
    )

    args, argv = parser.parse_known_args(argv)

    add_stdout_handler(int(args.verbosity))

    loaded_env = create_env(args.env_file, prefix=args.prefix, strip_prefix=args.strip_prefix)
    loaded_env["_RUNENV_WRAPPED"] = "1"

    if args.dry_run:
        sys.stdout.write("Dry run mode\n")
        sys.stdout.write(f"Parsed environment: {loaded_env}\n")
        sys.exit(0)
    os.environ.update(loaded_env)

    cmd = args.command

    if not cmd.startswith(("/", ".")):
        cmd = shutil.which(cmd)

    try:
        if cmd is None or not (stat.S_IXUSR & os.stat(cmd)[stat.ST_MODE]):
            _ = sys.stdout.write("File `%s is not executable\n" % cmd)
            sys.exit(1)
        return subprocess.check_call([cmd] + argv, env=os.environ)  # noqa
    except subprocess.CalledProcessError as e:
        return e.returncode


def resolve_lazy_value(value: str, env_vars: Dict[str, str]) -> str:
    """
    Recursively resolve variable references (e.g., ${VAR_NAME}) in a value using env_vars.
    """

    def replace_match(match):
        var_name = match.group(1)
        # Resolve variable from env_vars or os.environ
        return env_vars.get(var_name, os.environ.get(var_name, ""))

    # Replace all occurrences of ${VAR_NAME} in the value
    resolved_value = VARIABLE_REFERENCE_REGEX.sub(replace_match, value)
    return resolved_value


def create_env(
    env_file: str = ".env",
    prefix: Union[str, None] = None,
    strip_prefix: bool = True,  # noqa: FBT001,FBT002
) -> Dict[str, Union[str, str]]:
    """Create environ dictionary from current os.environ and
    variables got from given `env_file`"""

    environ: Dict[str, str] = {}
    with open(env_file, "r") as f:
        for raw_line in f.readlines():
            line = raw_line.rstrip(os.linesep)

            # Strip leading and trailing whitespace from the line
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Match key-value pairs (supports inline comments and empty values)
            match = re.match(r'^\s*([\w\.]+)\s*=\s*(["\']?.*?["\']?)\s*(?:#.*)?$', line)
            if match:
                key, value = match.groups()

                # skip not prefixed if prefix used
                if prefix and key != prefix and not key.startswith(prefix):
                    logger.debug(f"skip {key} without prefix {prefix}")
                    continue
                if prefix and key != prefix and strip_prefix:
                    logger.debug(f"strip prefix {prefix} from {key}")
                    key = key[len(prefix) :]

                # Strip quotes if they exist
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                environ[key] = value
            else:
                logger.debug(f"skip not matched {line}")

    # Perform lazy evaluation after parsing all variables
    for key, value in environ.items():
        environ[key] = resolve_lazy_value(value, environ)

    return environ


def load_env(
    env_file: str = ".env",
    prefix: Union[str, None] = None,
    strip_prefix: bool = True,  # noqa: FBT001,FBT002
    force: bool = False,  # noqa: FBT001,FBT002
    search_parent: int = 0,
) -> None:
    # we need absolute path to support `search_parent`
    env_file = os.path.abspath(env_file)
    logger.info("trying env file {0}".format(env_file))

    if "_RUNENV_WRAPPED" in os.environ and not force:
        return
    if not os.path.exists(env_file):
        if not search_parent:
            return
        else:
            env_file = os.path.join(os.path.dirname(os.path.dirname(env_file)), os.path.basename(env_file))
            return load_env(env_file, prefix, strip_prefix, force, search_parent - 1)

    os.environ.update(create_env(env_file, prefix=prefix, strip_prefix=strip_prefix))
    logger.info("env file {0} loaded".format(env_file))
