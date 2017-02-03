# -*- coding: utf-8 -*-
from distutils import spawn
import logging
import os
import stat
import subprocess
import sys

__author__ = 'Marek Wywiał'
__email__ = 'onjinx@gmail.com'
__version__ = '1.0.1'


logger = logging.getLogger('runenv')


def run(*args):
    """Load given `envfile` and run `command` with `params`"""

    if not args:
        args = sys.argv[1:]

    if len(args) < 2:
        print('Usage: runenv <envfile> <command> <params>')
        sys.exit(0)
    os.environ.update(create_env(args[0]))
    os.environ['_RUNENV_WRAPPED'] = '1'
    runnable_path = args[1]

    if not runnable_path.startswith(('/', '.')):
        runnable_path = spawn.find_executable(runnable_path)

    try:
        if not(stat.S_IXUSR & os.stat(runnable_path)[stat.ST_MODE]):
            print('File `%s is not executable' % runnable_path)
            sys.exit(1)
        return subprocess.check_call(
            args[1:], env=os.environ
        )
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
    with open(env_file, 'r') as f:
        for line in f.readlines():
            line = line.rstrip(os.linesep)
            if '=' not in line:
                continue
            if line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            environ[key] = parse_value(value)
    return environ


def load_env(
        env_file='.env', prefix=None, strip_prefix=True, force=False,
        search_parent=0
):
    # we need absolute path to support `search_parent`
    env_file = os.path.abspath(env_file)
    logger.info('trying env file {0}'.format(env_file))

    if '_RUNENV_WRAPPED' in os.environ and not force:
        return
    if not os.path.exists(env_file):
        if not search_parent:
            return
        else:
            env_file = os.path.join(
                os.path.dirname(os.path.dirname(env_file)),
                os.path.basename(env_file)
            )
            return load_env(
                env_file, prefix, strip_prefix, force, search_parent - 1
            )

    for k, v in create_env(env_file).items():
        if prefix and not k.startswith(prefix):
            continue
        if prefix and strip_prefix:
            os.environ[k[len(prefix):]] = v
        else:
            os.environ[k] = v
    logger.info('env file {0} loaded'.format(env_file))
