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
from typing import List, Optional, Sequence, Union, cast

from runenv.__about__ import __version__
from runenv.api import create_env, find_env_file, lint_env
from runenv.legacy import run_legacy, run_legacy_parser

logger = logging.getLogger(__name__)


def add_stdout_handler(verbosity: int) -> None:
    """Adds stdout handler with given verbosity to logger.

    Args:
        logger: python logger instance
        verbosity: target verbosity
                          1 - ERROR
                          2 - INFO
                          3 - DEBUG

    Usage:
        add_stdout_handler(verbosity=3)

    """
    v_map = {1: logging.ERROR, 2: logging.INFO, 3: logging.DEBUG}
    level = v_map.get(verbosity, 1)
    logging.basicConfig(level=level)


@dataclass
class CLIOptions:
    verbosity: int


@dataclass
class RunCMDOptions(CLIOptions):
    env_file: str
    prefix: Union[str, None]
    strip_prefix: bool
    search_parent: int
    command: List[str]


@dataclass
class ListCMDOptions(CLIOptions):
    env_file: str
    prefix: Union[str, None]
    strip_prefix: bool
    search_parent: int


@dataclass
class LintCMDOptions(CLIOptions):
    env_file: str
    prefix: Union[str, None]
    strip_prefix: bool
    search_parent: int
    as_json: bool


def fail(msg: str, returncode: int = 1) -> None:
    sys.stdout.write(f"{msg}\n")
    sys.exit(returncode)


def handle_run_subcommand(options: RunCMDOptions) -> Union[int, None]:
    cmd = options.command[1:] if options.command and options.command[0] == "--" else options.command[:]
    if not cmd:
        sys.stdout.write("Missing command to execute after 'runenv run -- <command> [params]'\n")
        sys.exit(1)

    loaded_env = create_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix, search_parent=options.search_parent
    )
    loaded_env["_RUNENV_WRAPPED"] = "1"
    os.environ.update(loaded_env)

    executable = shutil.which(cmd[0])
    params = cmd[1:]

    try:
        if executable is None or not os.path.exists(executable):
            fail(f"File `{executable} does not exist", 1)
            return 1
        if not (os.stat(executable).st_mode & stat.S_IXUSR):
            fail(f"File `{executable} is not executable")
            return 1
        return subprocess.check_call([executable, *params], env=os.environ)  # noqa: S603
    except subprocess.CalledProcessError as e:
        return e.returncode


def handle_list_subcommand(options: ListCMDOptions) -> None:
    loaded_env = create_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix, search_parent=options.search_parent
    )
    for key, value in sorted(loaded_env.items()):
        sys.stdout.write(f"{key}={value}\n")


def handle_lint_subcommand(options: LintCMDOptions) -> None:
    messages = lint_env(
        options.env_file, prefix=options.prefix, strip_prefix=options.strip_prefix, search_parent=options.search_parent
    )
    if options.as_json:
        sys.stdout.write(json.dumps([asdict(m) for m in messages]))
    else:
        for msg in messages:
            sys.stdout.write(f"[{msg.level}] (line {msg.line_number}) '{msg.message}'\n")


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

    args = parser.parse_args(argv)

    add_stdout_handler(cast("int", args.verbosity))

    logger.debug("args: %s", args)
    subcommand: str = args.subcommand

    if subcommand == "run":
        handler = handle_run_subcommand
        env_file = find_env_file(Path.cwd(), args.search_parent, args.env_file)
        if not env_file:
            fail(f"ERROR!!! Environment file {args.env_file} does not exist", 1)
        opts = RunCMDOptions(
            verbosity=args.verbosity,
            env_file=args.env_file,
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=args.search_parent,
            command=args.command,
        )
    elif subcommand == "list":
        handler = handle_list_subcommand
        env_file = find_env_file(Path.cwd(), args.search_parent, args.env_file)
        if not env_file:
            fail(f"ERROR!!! Environment file {args.env_file} does not exist", 1)
        opts = ListCMDOptions(
            verbosity=args.verbosity,
            env_file=args.env_file,
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=args.search_parent,
        )
    elif subcommand == "lint":
        handler = handle_lint_subcommand
        env_file = find_env_file(Path.cwd(), args.search_parent, args.env_file)
        if not env_file:
            fail(f"ERROR!!! Environment file {args.env_file} does not exist", 1)
        opts = LintCMDOptions(
            verbosity=args.verbosity,
            env_file=args.env_file,
            prefix=args.prefix,
            strip_prefix=args.strip_prefix,
            search_parent=args.search_parent,
            as_json=args.as_json,
        )
    else:
        parser.error("Unknown subcommand")
    return handler(opts)
