# -*- coding: utf-8 -*-

__author__ = 'Marek Wywiał'
__email__ = 'onjinx@gmail.com'
__version__ = '0.1.3'

import sys
import subprocess
import os
import stat


def run(*args):
    """Create given `envfile` and run `command` with `params`"""

    if not args:
        args = sys.argv[1:]

    if len(args) < 2:
        print('Usage: runenv <envfile> <command> <params>')
        sys.exit(0)
    environ = create_env(args[0])
    runnable_path = args[1]

    try:
        if not os.path.isfile(runnable_path):
            print('File `{}` does not exist'.format(runnable_path))
            sys.exit(1)
        if not(stat.S_IXUSR & os.stat(runnable_path)[stat.ST_MODE]):
            print('File `{}` is not executable'.format(runnable_path))
            sys.exit(1)
        return subprocess.check_call(
            args[1:], env=environ
        )
    except subprocess.CalledProcessError as e:
        return e.returncode


def create_env(env_file):
    """Create environ dictionary from current os.environ and
    variables got from given `env_file`"""

    environ = os.environ
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
