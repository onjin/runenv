# SPDX-FileCopyrightText: 2015-present Marek Wywiał <onjinx@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import dedent
from typing import List, Optional, Sequence, Tuple, Union, cast

from runenv.__about__ import __version__
from runenv._utils import add_stdout_handler
from runenv.api import create_env, find_env_file, lint_env
from runenv.legacy import run_legacy, run_legacy_parser
from runenv.parser import ParseMessage

logger = logging.getLogger(__name__)

LEVEL_ORDER = {"none": 0, "info": 1, "warning": 2, "error": 3}


def _strict_clamp(level: str) -> str:
    n = LEVEL_ORDER.get(level, 0)
    if n == 0 or n > LEVEL_ORDER["warning"]:
        return "warning"
    return level


def _strict_lint_settings(strict: bool, fail_on: str, lint_level: str) -> Tuple[str, str]:
    if not strict:
        return fail_on, lint_level
    return _strict_clamp(fail_on), _strict_clamp(lint_level)


@dataclass
class CLIOptions:
    verbosity: int


@dataclass
class EnvCMDOptions(CLIOptions):
    env_file: str
    prefix: Union[str, None]
    strip_prefix: bool
    search_parent: int
    lint_level: str
    fail_on: str
    strict: bool


@dataclass
class RunCMDOptions(EnvCMDOptions):
    command: List[str]


@dataclass
class ListCMDOptions(EnvCMDOptions):
    pass


@dataclass
class LintCMDOptions(EnvCMDOptions):
    as_json: bool


def fail(msg: str, returncode: int = 1) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.exit(returncode)


def _require_env_file(search_parent: int, env_file: Optional[str]) -> Path:
    resolved = find_env_file(Path.cwd(), search_parent, env_file)
    if not resolved:
        if env_file:
            fail(f"ERROR!!! Environment file `{env_file}` does not exist", 1)
        else:
            fail(f"No .env / .env.json / .env.toml / .env.yaml found in {Path.cwd()}", 1)
    return resolved  # type: ignore[return-value]


def apply_lint_policy(
    messages: List[ParseMessage],
    lint_level: str,
    fail_on: str,
    as_json: bool = False,
) -> int:
    min_print = LEVEL_ORDER.get(lint_level, 0)
    min_fail = LEVEL_ORDER.get(fail_on, 0)

    to_show = [m for m in messages if LEVEL_ORDER.get(m.level, 0) >= min_print] if min_print > 0 else []
    if to_show:
        if as_json:
            sys.stdout.write(json.dumps([asdict(m) for m in to_show]))
        else:
            for msg in to_show:
                sys.stderr.write(f"[{msg.level}] (line {msg.line_number}) '{msg.message}'\n")

    if min_fail > 0 and any(LEVEL_ORDER.get(m.level, 0) >= min_fail for m in messages):
        return 1
    return 0


def _run_lint_check(options: EnvCMDOptions) -> int:
    if options.lint_level == "none" and options.fail_on == "none":
        return 0
    messages = lint_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix,
        search_parent=options.search_parent, strict=options.strict,
    )
    return apply_lint_policy(messages, options.lint_level, options.fail_on)


def handle_run_subcommand(options: RunCMDOptions) -> Union[int, None]:
    cmd = options.command[1:] if options.command and options.command[0] == "--" else options.command[:]
    if not cmd:
        sys.stdout.write("Missing command to execute after 'runenv run -- <command> [params]'\n")
        sys.exit(1)

    rc = _run_lint_check(options)
    if rc != 0:
        return rc

    loaded_env = create_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix,
        search_parent=options.search_parent, strict=options.strict,
    )
    loaded_env["_RUNENV_WRAPPED"] = "1"
    os.environ.update(loaded_env)

    executable = shutil.which(cmd[0])
    params = cmd[1:]

    try:
        if executable is None or not os.path.exists(executable):
            fail(f"File `{executable}` does not exist", 1)
            return 1
        if not (os.stat(executable).st_mode & stat.S_IXUSR):
            fail(f"File `{executable}` is not executable")
            return 1
        return subprocess.check_call([executable, *params], env=os.environ)  # noqa: S603
    except subprocess.CalledProcessError as e:
        return e.returncode


def handle_list_subcommand(options: ListCMDOptions) -> int:
    rc = _run_lint_check(options)
    if rc != 0:
        return rc

    loaded_env = create_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix,
        search_parent=options.search_parent, strict=options.strict,
    )
    for key, value in sorted(loaded_env.items()):
        sys.stdout.write(f"{key}={value}\n")
    return 0


def handle_lint_subcommand(options: LintCMDOptions) -> int:
    messages = lint_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix,
        search_parent=options.search_parent, strict=options.strict,
    )
    return apply_lint_policy(messages, options.lint_level, options.fail_on, as_json=options.as_json)


def run(argv: Optional[Sequence[str]] = None) -> Union[int, None]:
    """Run CLI.

    Args:
        argv: list of CLI arguments
    """
    if argv is None:
        argv = sys.argv[1:]
    # do not pass `-h` | `--help` to legacy
    params = (" ".join(argv).split(" -- ", 1))[0].split(" ")
    if "-h" not in params and "--help" not in params:
        _, l_argv = run_legacy_parser(argv, only_params=True)
        if len(l_argv) > 0 and Path(l_argv[0]).is_file():
            # Legacy usage detected
            return run_legacy()

    prog = "runenv"
    description = "Run program with given environment file loaded"
    epilog = dedent(
        """
    NOTES:
        v1.3.0:
          The `runenv .env <command> <params>` still works but the new separate subcommand as introduced:

              $ runenv run [--env-file .env] -- command --with --params

    """
    )

    parser = argparse.ArgumentParser(
        prog=prog, description=description, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-v",
        "--verbosity",
        action="store",
        default=1,
        type=int,
        help="verbosity level, 1 - (ERROR, default), 2 - (INFO) or 3 - (DEBUG)",
        choices=[1, 2, 3],
    )
    parser.add_argument(
        "--help-legacy",
        action="store_true",
        help="Return help from legacy `runenv .env <command> [params]` CLI",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=False)

    # --- run command ---
    run_parser = subparsers.add_parser("run", help="Run a command with .env loaded")
    run_parser.add_argument("command", help="Command to run with loaded environment", nargs=argparse.REMAINDER)
    run_parser.add_argument(
        "--env-file",
        help="Environment file to load",
        type=str,
    )
    run_parser.add_argument(
        "-p",
        "--prefix",
        action="store",
        type=str,
        help="Load only variables with given prefix",
    )
    run_parser.add_argument(
        "-s",
        "--strip-prefix",
        action="store_true",
        help="Strip prefix given with --prefix from environment variables names",
    )
    run_parser.add_argument(
        "--search-parent",
        type=int,
        default=0,
        help="How many parent dirs search for .env[.json,.toml,.yaml] files; default 0",
    )
    run_parser.add_argument(
        "--lint-level",
        choices=["none", "info", "warning", "error"],
        default="none",
        help="Minimum message level to print to stderr (default: none)",
    )
    run_parser.add_argument(
        "--fail-on",
        choices=["none", "info", "warning", "error"],
        default="none",
        help="Minimum message level that causes a non-zero exit before running the command (default: none)",
    )
    run_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode: warn on undefined/ambient variable references, treat duplicates as errors; implies --fail-on warning",
    )

    # --- list command ---
    list_parser = subparsers.add_parser("list", help="List parsed variables")
    list_parser.add_argument(
        "--env-file",
        help="Environment file to load",
        type=str,
    )
    list_parser.add_argument(
        "-p",
        "--prefix",
        action="store",
        type=str,
        help="Load only variables with given prefix",
    )
    list_parser.add_argument(
        "-s",
        "--strip-prefix",
        action="store_true",
        help="Strip prefix given with --prefix from environment variables names",
    )
    list_parser.add_argument(
        "--search-parent",
        type=int,
        default=0,
        help="How many parent dirs search for .env[.json,.toml,.yaml] files; default 0",
    )
    list_parser.add_argument(
        "--lint-level",
        choices=["none", "info", "warning", "error"],
        default="none",
        help="Minimum message level to print to stderr (default: none)",
    )
    list_parser.add_argument(
        "--fail-on",
        choices=["none", "info", "warning", "error"],
        default="none",
        help="Minimum message level that causes a non-zero exit before listing (default: none)",
    )
    list_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode: warn on undefined/ambient variable references, treat duplicates as errors; implies --fail-on warning",
    )

    # --- lint command ---
    lint_parser = subparsers.add_parser("lint", help="Lint env file")
    lint_parser.add_argument(
        "--env-file",
        help="Environment file to lint",
        type=str,
    )
    lint_parser.add_argument(
        "-p",
        "--prefix",
        action="store",
        type=str,
        help="Load only variables with given prefix",
    )
    lint_parser.add_argument(
        "-s",
        "--strip-prefix",
        action="store_true",
        help="Strip prefix given with --prefix from environment variables names",
    )
    lint_parser.add_argument(
        "--search-parent",
        type=int,
        default=0,
        help="How many parent dirs search for .env[.json,.toml,.yaml] files; default 0",
    )
    lint_parser.add_argument(
        "--as-json",
        action="store_true",
        help="Return json instead log lines",
    )
    lint_parser.add_argument(
        "--lint-level",
        choices=["none", "info", "warning", "error"],
        default="info",
        help="Minimum message level to print (default: info)",
    )
    lint_parser.add_argument(
        "--fail-on",
        choices=["none", "info", "warning", "error"],
        default="error",
        help="Minimum message level that causes a non-zero exit (default: error)",
    )
    lint_parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode: warn on undefined/ambient variable references, treat duplicates as errors; implies --fail-on warning",
    )

    args = parser.parse_args(argv)

    add_stdout_handler(cast(int, args.verbosity))

    logger.debug("args: %s", args)
    subcommand: str = args.subcommand

    if subcommand is None:
        parser.print_help()
        return 0

    if subcommand == "run":
        handler = handle_run_subcommand
        env_file = _require_env_file(args.search_parent, args.env_file)
        fail_on, lint_level = _strict_lint_settings(args.strict, args.fail_on, args.lint_level)
        opts = RunCMDOptions(
            verbosity=args.verbosity,
            env_file=str(env_file),
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=0,
            command=args.command,
            lint_level=lint_level,
            fail_on=fail_on,
            strict=args.strict,
        )
    elif subcommand == "list":
        handler = handle_list_subcommand
        env_file = _require_env_file(args.search_parent, args.env_file)
        fail_on, lint_level = _strict_lint_settings(args.strict, args.fail_on, args.lint_level)
        opts = ListCMDOptions(
            verbosity=args.verbosity,
            env_file=str(env_file),
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=0,
            lint_level=lint_level,
            fail_on=fail_on,
            strict=args.strict,
        )
    elif subcommand == "lint":
        handler = handle_lint_subcommand
        env_file = _require_env_file(args.search_parent, args.env_file)
        fail_on, lint_level = _strict_lint_settings(args.strict, args.fail_on, args.lint_level)
        opts = LintCMDOptions(
            verbosity=args.verbosity,
            env_file=str(env_file),
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=0,
            as_json=args.as_json,
            lint_level=lint_level,
            fail_on=fail_on,
            strict=args.strict,
        )
    else:
        parser.error("Unknown subcommand")
    try:
        return handler(opts)
    except ValueError as e:
        fail(str(e), 1)
        return 1
