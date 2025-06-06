# SPDX-FileCopyrightText: 2015-present Marek Wywiał <onjinx@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import logging
import os
import shutil
import stat
import subprocess
import sys
from typing import List, Optional, Sequence, Tuple

from runenv.__about__ import __version__
from runenv.api import create_env

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


def run_legacy_parser(
    argv: Optional[Sequence[str]],
    only_params: bool = False,  # noqa: FBT001,FBT002
) -> Tuple[argparse.Namespace, List[str]]:
    prog = "runenv"
    description = "Run program with given environment file loaded"

    parser = argparse.ArgumentParser(prog=prog, description=description)

    if not only_params:
        parser.add_argument("env_file", help="Environment file to load")
        parser.add_argument("command", help="Command to run with loaded environment")

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
        "-p",
        "--prefix",
        action="store",
        type=str,
        help="Load only variables with given prefix",
    )
    parser.add_argument(
        "-s",
        "--strip-prefix",
        action="store_true",
        help="Strip prefix given with --prefix from environment variables names",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Return parsed .env instead of running command",
    )

    return parser.parse_known_args(argv)


def run_legacy(argv: Optional[Sequence[str]] = None) -> int:
    """Run CLI.

    Args:
        argv: list of CLI arguments
    """
    logger.debug("[DEPRECATED] Use 'runenv run --env-file .env command' instead.")
    args, argv = run_legacy_parser(argv)

    add_stdout_handler(int(args.verbosity))
    logger.debug("args: %s", args)

    loaded_env = create_env(args.env_file, prefix=args.prefix, strip_prefix=args.strip_prefix)
    loaded_env["_RUNENV_WRAPPED"] = "1"

    if args.dry_run:
        sys.stdout.write("[legacy] Dry run mode\n")
        sys.stdout.write(f"[legacy] Parsed environment: {loaded_env}\n")
        sys.exit(0)
    os.environ.update(loaded_env)

    cmd = args.command

    if not cmd.startswith(("/", ".")):
        cmd = shutil.which(cmd)

    try:
        if cmd is None or not os.path.exists(cmd):
            sys.stdout.write(f"[legacy] File `{args.command} does not exist\n")
            sys.exit(1)
        if not (stat.S_IXUSR & os.stat(cmd)[stat.ST_MODE]):
            sys.stdout.write(f"[legacy] File `{args.cmd} is not executable\n")
            sys.exit(1)
        return subprocess.check_call([cmd] + argv, env=os.environ)  # noqa: RUF005, S603
    except subprocess.CalledProcessError as e:
        return e.returncode
