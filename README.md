# runenv

<div align="center">

|         |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| CI/CD   | [![CI - Test](https://github.com/onjin/runenv/actions/workflows/test.yml/badge.svg)](https://github.com/onjin/runenv/actions/workflows/test.yml)                                                                                                                                                                                                                                                                                                                                       |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/runenv.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/runenv/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/runenv.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypi.org/project/runenv/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runenv.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/runenv/)                 |
| Meta    | [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/) |

</div>

---
You can use *runenv* to manage your app settings using [12-factor](http://12factor.net/) principles.

The `runenv` package provides a few things:

- [cli] Wrapper to run programs with modified environment variables loaded from given .env file.
- [api] Python API to load variables from .env file into environment

License: Free software: MIT license
Changes: [CHANGELOG.md](CHANGELOG.md)

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Integration](#integration)

## Installation

To install `runenv` package along with `runenv` CLI command run:

```console
pip install runenv
```

## Usage

Fist you have to create `.env` (this is the default name, you can use any name and have multiple environment files in projects) file in your project.


**Example `.env` file:**

```ini
BASE_URL=http://127.0.0.1:8000
DATABASE_URI=postgres://postgres:password@localhost/dbname

# line with comment
EMAIL_HOST=smtp.mandrillapp.com
EMAIL_PORT=587                             # inline comment
EMAIL_HOST_USER="double quoted value"
EMAIL_HOST_PASSWORD='single quoted value'
EMAIL_FROM=user@${EMAIL_HOST}              # reuse variable from same file
EMAIL_USE_TLS=1
```

### Python API

#### load_env(env_file=".env", prefix=None, strip_prefix=True, force=False, search_parent=0)`

This function is loading content of `.env` file into environment without raising errors if file does not exist.

**Options**:

- `env_file`: optional environment file name; default `.env`
- `prefix`: optional prefix to filter loaded variables; f.e. `DJANGO_` will load only `DJANGO_*` variables
- `strip_prefix`: whether strip prefix when loading variables; default `True`; f.e. `DJANGO_SECRET` will be loaded as `SECRET` if `prefix=DJANGO_`
- `force`: whether load `.env` file again, even if application was started by `runenv` CLI wrapper (this wrapper already is loading `.env` file)
- `search_parent`: how many parent directories search for `.env` file; default `0`

#### create_env(env_file=".env", prefix=None, strip_prefix=True)`

This function is only parsing content of `.env` file and returns it as python dictionary, without changing environment.

**Options**:

- `env_file`: optional environment file name; default `.env`
- `prefix`: optional prefix to filter loaded variables; f.e. `DJANGO_` will load only `DJANGO_*` variables
- `strip_prefix`: whether strip prefix when loading variables; default `True`; f.e. `DJANGO_SECRET` will be loaded as `SECRET` if `prefix=DJANGO_`

### CLI

The `runenv` CLI can be used to run commands wrapped with environment loaded from passed `.env` files.

```console
$ runenv --help
usage: runenv [-h] [-V] [-v {1,2,3}] [-p PREFIX] [-s] [--dry_run] env_file command

Run program with given environment file loaded

positional arguments:
  env_file              Environment file to load
  command               Command to run with loaded environment

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v {1,2,3}, --verbosity {1,2,3}
                        verbosity level, 1 - (ERROR, default), 2 - (INFO) or 3 - (DEBUG)
  -p PREFIX, --prefix PREFIX
                        Load only variables with given prefix
  -s, --strip_prefix    Strip prefix given with --prefix from environment variables names
  --dry_run             Return parsed .env instead of running command
```

**Example usage:**

Run `./manage.py serve` command with environment loaded from `.env.development` file.

```console
$ runenv .env.development ./manage.py serve
```

**Options**:

- `env_file`: environment file name to load
- `--prefix`: optional prefix to filter loaded variables; f.e. `DJANGO_` will load only `DJANGO_*` variables
- `--strip-prefix`: whether strip prefix when loading variables; default `True`; f.e. `DJANGO_SECRET` will be loaded as `SECRET` if `prefix=DJANGO_`
- `--dry-run`: only display parsed `.env` result instead of loading environment and running command


## Integration

To use `load_env` with [Django](http://djangoproject.com/) or [Flask](http://flask.pocoo.org/), put the following code in `manage.py` and `wsgi.py` files.

``` python
from runenv import load_env
load_env()
```

## Similar projects

-   <https://github.com/jezdez/envdir> - runs another program with a
    modified environment according to files in a specified directory
-   <https://github.com/theskumar/python-dotenv> - Reads the key,value
    pair from .env and adds them to environment variable
