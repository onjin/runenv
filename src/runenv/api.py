# SPDX-FileCopyrightText: 2015-present Marek Wywiał <onjinx@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Union

from runenv.parser import ParseMessage, ParseOptions, lint_env_file, parse_env_file

logger = logging.getLogger(__name__)


def find_env_file(path: Path, search_parent: int = 0, filename: Union[str, Path, None] = None) -> Union[Path, None]:
    search_names: List[str] = [".env", ".env.json", ".env.toml", ".env.yaml"]

    names = [filename] if filename else search_names[:]

    for name in names:
        logger.debug("Searching for %s files at %s with search_parent=%s", name, path, search_parent)
        if (path / name).is_file():
            file = path / name
            logger.debug("Found env file: %s", file)
            return file
    if search_parent > 0:
        env_file = find_env_file(path.parent, search_parent - 1, filename=filename)
        if env_file:
            return env_file
    return None


def create_env(
    env_file: Union[str, Path, None] = None,
    prefix: Union[str, None] = None,
    strip_prefix: bool = True,  # noqa: FBT001,FBT002
    search_parent: int = 0,
) -> Dict[str, str]:
    """Create environ dictionary from current variables got from given `env_file`."""
    env_file = find_env_file(Path.cwd(), search_parent, filename=env_file)
    if not env_file:
        raise ValueError("No env file found")
    return parse_env_file(env_file, ParseOptions(prefix=prefix, strip_prefix=strip_prefix))


def load_env(
    env_file: Union[str, Path, None] = None,
    prefix: Union[str, None] = None,
    strip_prefix: bool = True,  # noqa: FBT001,FBT002
    force: bool = False,  # noqa: FBT001,FBT002
    search_parent: int = 0,
    require_env_file: bool = False,
) -> None:

    env_file = find_env_file(Path.cwd(), search_parent, filename=env_file)

    # In `load_env` we will not fail if file does not exists
    if not env_file:
        if require_env_file:
            raise ValueError("No env file found")
        return

    if "_RUNENV_WRAPPED" in os.environ and not force:
        return

    os.environ.update(create_env(env_file, prefix=prefix, strip_prefix=strip_prefix))
    logger.info("env file %s loaded", getattr(env_file, "name", str(env_file)))
    return


def lint_env(
    env_file: Union[str, Path, None] = None,
    prefix: Union[str, None] = None,
    strip_prefix: bool = True,  # noqa: FBT001,FBT002
    search_parent: int = 0,
) -> List[ParseMessage]:
    """Lint env_file."""
    env_file = find_env_file(Path.cwd(), search_parent, filename=env_file)
    if not env_file:
        raise ValueError("No env file found")
    return lint_env_file(env_file, ParseOptions(prefix=prefix, strip_prefix=strip_prefix))
