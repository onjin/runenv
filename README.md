
# runenv

Manage your application’s settings with `runenv`, using the [12-factor](http://12factor.net/) principles. This library provides both a CLI tool and a Python API to simplify the management of environment variables in your projects.

| Section  | Details |
|----------|---------|
| CI/CD    | [![CI - Test](https://github.com/onjin/runenv/actions/workflows/test.yml/badge.svg)](https://github.com/onjin/runenv/actions/workflows/test.yml) |
| Package  | [![PyPI - Version](https://img.shields.io/pypi/v/runenv.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/runenv/) |
| Downloads | [![PyPI - Downloads](https://img.shields.io/pypi/dm/runenv.svg?color=blue&label=Downloads&logo=pypi&logoColor=gold)](https://pypi.org/project/runenv/) |
| Python Version | [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/runenv.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/runenv/) |
| Meta | [![Linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Code Style - Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Types - MyPy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) |
| License | [![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/) |
| Changes | [CHANGELOG.md](CHANGELOG.md) |


---

## Table of Contents

- [Features at a Glance](#features-at-a-glance)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Quick CLI Usage](#quick-cli-usage)
  - [Python API Overview](#python-api-overview)
- [In-Depth Usage and Examples](#in-depth-usage-and-examples)
  - [Using the CLI Tool](#using-the-cli-tool)
  - [Python API Details](#python-api-details)
  - [Framework Integration](#framework-integration)
- [Example `.env` File](#example-env-file)
- [Similar Projects](#similar-projects)

## Features at a Glance

- **CLI Tool**: Run programs with customized environment variables from a `.env` file.
- **Python API**: Load and manage environment variables programmatically.
- **Integration**: Easily integrate with frameworks like Django and Flask.

---

## Getting Started

### Installation

To install `runenv` along with its CLI tool, run:

```console
pip install runenv
```

### Quick CLI Usage

1. Create a `.env` file in your project’s root directory:

The `.env` file can contain simple key-value pairs, comment lines, and inline comments:

```ini
# Base settings
BASE_URL=http://127.0.0.1:8000
DATABASE_URI=postgres://postgres:password@localhost/dbname

# Email configuration
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587  # Port for SMTP
EMAIL_USER="user@example.com"
EMAIL_PASSWORD='password'
EMAIL_USE_TLS=1

# Reusing variables
EMAIL_FROM=user@${EMAIL_HOST}
```

- Variables are set in `KEY=VALUE` pairs.
- Use `#` for comments.
- Inline comments are also supported after a `#`.

2. Run a command with the environment loaded from the `.env` file:

   ```console
   runenv .env ./your_command
   ```

### Python API Overview

You can load environment variables directly in Python:

```python
from runenv import load_env

# Load variables from the specified .env file
load_env(".env")
```

## In-Depth Usage and Examples

### Using the CLI Tool

The `runenv` CLI provides flexibility to run any command with custom environment settings:

```console
runenv .env.development ./manage.py runserver
```

**Options:**

- `--prefix`: Load variables with a specific prefix, e.g., `DJANGO_`.
- `--strip-prefix`: Remove the prefix from variable names after loading.
- `--dry-run`: Output the parsed `.env` file as environment without executing the command.

Full help and options:

```console
runenv --help
```

### Python API Details

#### `load_env`

Load variables into the environment:

```python
load_env(env_file=".env", prefix="DJANGO_", strip_prefix=True, force=False, search_parent=0)
```

**Parameters:**

- `env_file` (str, optional): The environment file to read from (default is `.env`).
- `prefix` (str, optional): Load only variables that start with this prefix.
- `strip_prefix` (bool, optional): If True, removes the prefix from variable names when loaded (default is True).
- `force` (bool, optional): Force loading the `.env` file again even if already loaded by `runenv` CLI (default is False).
- `search_parent` (int, optional): Number of parent directories to search for `.env` file (default is 0).

#### `create_env`

Parse `.env` contents into a dictionary without modifying the environment:

```python
env_vars = create_env(env_file=".env", prefix="APP_", strip_prefix=True)
print(env_vars)
```

**Parameters:**

- `env_file` (str, optional): The environment file to read from (default is `.env`).
- `prefix` (str, optional): Load only variables that start with this prefix.
- `strip_prefix` (bool, optional): If True, removes the prefix from variable names when loaded (default is True).

### Framework Integration

Easily integrate `runenv` with web frameworks:

```python
# In Django's manage.py or Flask's app setup
from runenv import load_env
load_env(".env")
```


## Similar Projects

- [envdir](https://github.com/jezdez/envdir): Run programs with a modified environment based on files in a directory.
- [python-dotenv](https://github.com/theskumar/python-dotenv): Reads key-value pairs from `.env` files and adds them to the environment.

---

With `runenv`, managing environment variables becomes simpler and more consistent, making it easier to develop and deploy applications across different environments.
