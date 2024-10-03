# SPDX-FileCopyrightText: 2015-present Marek Wywiał <onjinx@gmail.com>
#
# SPDX-License-Identifier: MIT
import logging
import os
import re
import stat
import subprocess
import sys
from distutils import spawn

logger = logging.getLogger("runenv")


def run(*args):
    """Load given `envfile` and run `command` with `params`"""

    if not args:
        args = sys.argv[1:]

    if len(args) < 2:  # noqa
        sys.stdout.write("Usage: runenv <envfile> <command> <params>\n")
        sys.exit(0)
    os.environ.update(create_env(args[0]))
    os.environ["_RUNENV_WRAPPED"] = "1"
    runnable_path = args[1]

    if not runnable_path.startswith(("/", ".")):
        runnable_path = spawn.find_executable(runnable_path)

    try:
        if not (stat.S_IXUSR & os.stat(runnable_path)[stat.ST_MODE]):
            sys.stdout.write("File `%s is not executable\n" % runnable_path)
            sys.exit(1)
        return subprocess.check_call(args[1:], env=os.environ)  # noqa
    except subprocess.CalledProcessError as e:
        return e.returncode


def parse_value(value):
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value


def create_env(env_file):
    """Create environ dictionary from current os.environ and
    variables got from given `env_file`"""

    environ = {}
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

                # Strip quotes if they exist
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                environ[key] = value
            else:
                logger.debug(f"skip not matched {line}")

    return environ


def load_env(env_file=".env", prefix=None, strip_prefix=True, force=False, search_parent=0):  # noqa: FBT002
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

    for k, v in create_env(env_file).items():
        if prefix and not k.startswith(prefix):
            continue
        if prefix and strip_prefix:
            os.environ[k[len(prefix) :]] = v
        else:
            os.environ[k] = v
    logger.info("env file {0} loaded".format(env_file))
