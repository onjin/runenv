# -*- coding: utf-8 -*-

__author__ = 'Marek Wywiał'
__email__ = 'onjinx@gmail.com'
__version__ = '0.2.4'

import sys
import subprocess
import os
import stat
from distutils import spawn


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
        if not os.path.isfile(runnable_path):
            print('File `%s` does not exist' % runnable_path)
            sys.exit(1)
        if not(stat.S_IXUSR & os.stat(runnable_path)[stat.ST_MODE]):
            print('File `%s is not executable' % runnable_path)
            sys.exit(1)
        return subprocess.check_call(
            args[1:], env=os.environ
        )
    except subprocess.CalledProcessError as e:
        return e.returncode


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
            environ[key] = value
    return environ


def load_env(env_file='.env', prefix=None, strip_prefix=True, force=False):
    if '_RUNENV_WRAPPED' in os.environ and not force:
        return
    if not os.path.exists(env_file):
        return
    for k, v in create_env(env_file).items():
        if prefix and not k.startswith(prefix):
            continue
        if prefix and strip_prefix:
            os.environ[k[len(prefix):]] = v
        else:
            os.environ[k] = v
