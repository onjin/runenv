# runenv

Manage application settings with ease using `runenv`, a lightweight tool inspired by [The Twelve-Factor App](https://12factor.net/config) methodology for configuration through environment variables.

`runenv` provides:
- A CLI for language-agnostic `.env` profile execution
- A Python API for programmatic `.env` loading

> “Store config in the environment” — [12factor.net/config](https://12factor.net/config)

| Section  | Status |
|----------|--------|
| CI/CD    | [![CI - Test](https://github.com/onjin/runenv/actions/workflows/test.yml/badge.svg)](https://github.com/onjin/runenv/actions/workflows/test.yml) |
| PyPI     | [![PyPI - Version](https://img.shields.io/pypi/v/runenv.svg?logo=pypi&label=PyPI)](https://pypi.org/project/runenv/) [![Downloads](https://img.shields.io/pypi/dm/runenv.svg?color=blue)](https://pypi.org/project/runenv/) |
| Python   | [![Python Versions](https://img.shields.io/pypi/pyversions/runenv.svg?logo=python&label=Python)](https://pypi.org/project/runenv/) |
| Style    | [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy) |
| License  | [![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/) |
| Docs     | [CHANGELOG.md](CHANGELOG.md) |

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [CLI Usage](#cli-usage)
  - [Python API](#python-api)
- [Multiple Profiles](#multiple-profiles)
- [Framework Integrations](#framework-integrations)
- [Parsing Behaviour](#parsing-behaviour)
  - [Variable Expansion](#variable-expansion)
  - [Quoting and Escape Sequences](#quoting-and-escape-sequences)
  - [Required Variables](#required-variables)
- [Sample `.env` File](#sample-env-file)
- [Similar Tools](#similar-tools)

---

## Key Features

- 🚀 **CLI-First**: Use `.env` files across any language or platform.
- 🐍 **Python-native API**: Load and transform environment settings inside Python.
- ⚙️ **Multiple Profiles**: Switch easily between `.env.dev`, `.env.prod`, etc.
- ⚙️ **Multiple Formats**: Use plain `.env`, `.env.json`, `.env.toml`, or `.env.yaml`
- ⚙️ **Autodetect Env File**: Looking for `.env`, `.env.json`, `.env.toml`, and `.env.yaml`
- 🔧 **Parameter Expansion**: Bash-style `${VAR:-default}`, `${VAR:?msg}`, `${VAR:+alt}` operators.
- ✏️ **Escape Sequences**: `\n`, `\t`, `\\`, `\"` in double-quoted values; `$$` for a literal `$`.
- 📄 **Multi-line Values**: Triple-quoted heredoc syntax (`"""..."""` / `'''...'''`).
- 🔒 **Required Variables**: `# @required VAR` declarations fail fast on missing config.
- 🧩 **Framework-Friendly**: Works well with Django, Flask, FastAPI, and more.

---

## Quick Start

### Installation

```bash
pip install runenv
pip install runenv[toml] # if you want to use .env.toml in python < 3.11
pip install runenv[yaml] # if you want to use .env.yaml
```

### CLI Usage

Run any command with a specified environment:

```bash
runenv run --env-file .env.dev -- python manage.py runserver
runenv run --env-file .env.prod -- uvicorn app:app --host 0.0.0.0
runenv list [--env-file .env]           # view parsed variables
runenv lint [--env-file .env]           # check for errors in env file
runenv lint --strict [--env-file .env]  # also warn on ambient/undefined refs
```

---

## Python API

### Load `.env` into `os.environ`

> **Note**: The `load_env` will not parse env_file if the `runenv` CLI was used, unless you `force=True` it.

```python
from runenv import load_env

load_env() # loads .env
load_env(
    env_file=".env.dev",    # file to load - will be autodetected if not passed
    prefix='APP_',          # load only APP_.* variables from file
    strip_prefix=True,      # strip ^ prefix when loading variables
    force=True,             # load env_file even if the `runvenv` CLI was used
    search_parent=1,        # look for env_file in current dir and its 1 parent dirs
    require_env_file=False  # raise error if env file is missing, otherwise just ignore
)
```

### Read `.env` as a dictionary

```python
from runenv import create_env

config = create_env() # parse .env content into dictionary
config = create_env(
    env_file=".env.dev",    # file to load - will be autodetected if not passed
    prefix='APP_',          # parse only APP_.* variables from file
    strip_prefix=True,      # strip ^ prefix when parsing variables
    search_parent=1,        # look for env_file in current dir and its 1 parent dirs
)
print(config)
```

Options include:
- Filtering by prefix
- Automatic prefix stripping
- Searching parent directories

---

## Multiple Profiles

Use separate `.env` files per environment:

```bash
runenv .env.dev flask run
runenv .env.staging python main.py
runenv .env.production uvicorn app.main:app
```

Recommended structure:
```
.env.dev
.env.test
.env.staging
.env.production
```

---

## Framework Integrations

> **Note**: If you're using `runenv .env [./manage.py, ...]` CLI then you do not need change your code. Use these integrations only if you're using Python API.

### Django

```python
# manage.py or wsgi.py
from runenv import load_env
load_env(".env")
```

### Flask

```python
from flask import Flask
from runenv import load_env

load_env(".env")
app = Flask(__name__)
```

### FastAPI

```python
from fastapi import FastAPI
from runenv import load_env

load_env(".env")
app = FastAPI()
```

---

## Parsing Behaviour

| Situation | Behaviour |
|-----------|-----------|
| Duplicate key | Last definition wins; a `warning` is emitted by `lint` |
| Key exactly equal to `--prefix` | Skipped (stripping would produce an empty name) |
| Key without matching prefix | Skipped and reported as `info` by `lint` |

Duplicate keys are **not** an error — the last value in the file takes effect, matching the behaviour of most shell `.env` loaders. Use `runenv lint` to surface duplicates as warnings before they reach production.

### Variable Expansion

`${VAR}` references resolve against variables defined in the same file and then fall back to the calling shell's `os.environ`. The following bash-style parameter expansion operators are supported:

| Syntax | Behaviour |
|--------|-----------|
| `${VAR}` | Value of `VAR`; empty string if unset |
| `${VAR:-default}` | Value of `VAR` if set and non-empty, otherwise `default` |
| `${VAR-default}` | Value of `VAR` if set (even if empty), otherwise `default` |
| `${VAR:?msg}` | Value of `VAR` if set and non-empty; fatal error with `msg` otherwise |
| `${VAR:+alt}` | `alt` if `VAR` is set and non-empty, otherwise empty string |

The `:?` operator causes `runenv run` / `runenv list` to exit non-zero and `runenv lint` to report an error-level message with the line number where the variable is declared.

### Quoting and Escape Sequences

| Style | Escape processing | Variable expansion |
|-------|------------------|--------------------|
| Unquoted `VAR=value` | None | Yes |
| Single-quoted `VAR='value'` | None | Yes |
| Double-quoted `VAR="value"` | `\n` `\t` `\r` `\\` `\"` | Yes |
| Triple double-quoted `VAR="""..."""` | Same as double-quoted | Yes |
| Triple single-quoted `VAR='''...'''` | None | Yes |

Double-quoted values process the standard escape sequences:

```ini
GREETING="Hello\tWorld\n"   # tab + newline
PATH_VAL="C:\\Users\\name"  # literal backslashes
QUOTED="say \"hi\""         # embedded double quote
```

Use `$$` anywhere to emit a literal `$` without triggering variable expansion:

```ini
PGSERVICE=$$HOME/.pgservice  # value: $HOME/.pgservice
TEMPLATE=price: $$${AMOUNT}  # literal $ followed by expanded AMOUNT
```

Triple-quoted values span multiple lines — useful for certificates, JSON blobs, or any multi-line secret:

```ini
PRIVATE_KEY="""
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----
"""

RAW_TEXT='''
no \n escape processing here
$$HOME is literal too
'''
```

### Required Variables

Declare variables that must be present and non-empty with `# @required`:

```ini
# @required DATABASE_URL, SECRET_KEY
# @required PORT

DATABASE_URL=postgresql://localhost/mydb
SECRET_KEY=${APP_SECRET:?APP_SECRET must be set}
PORT=${PORT:-8000}
```

If any declared variable is missing or empty after full expansion, `runenv lint` reports an error at the directive's line number and `runenv run` exits non-zero. Multiple names can appear on one line (comma-separated) or across multiple directives.

`# @required` and `${VAR:?msg}` are complementary, not duplicates. Use `# @required` to declare top-level contracts on the keys your application needs. Use `${SOURCE:?msg}` when building a value from another variable and you want a specific error message that names the source. Don't combine both on the same variable.

---

## Sample `.env` File

```ini
# Declare required variables — runenv fails fast if any are missing
# @required DATABASE_URL, SECRET_KEY

# export keyword accepted for shell-source compatibility
export HOST=localhost
PORT=${PORT:-8000}
URL=http://${HOST}:${PORT}

# Parameter expansion
CACHE_URL=${REDIS_URL:-redis://localhost:6379}   # default if unset/empty
LOG_LEVEL=${LOG_LEVEL-info}                      # default only if unset
FEATURE_HEADER=${FEATURE_FLAG:+X-Feature: on}   # set only when flag is on

# :? is for inline interpolation guards (different from # @required):
# it fails with a custom message pointing at the *source* variable
DATABASE_URL=${DATABASE_URL:?DATABASE_URL must be set}
SECRET_KEY=${SECRET_KEY:?SECRET_KEY must be set}

# Escape sequences in double-quoted strings
GREETING="Hello\tWorld"
WINDOWS_PATH="C:\\Users\\deploy"

# Literal $ with $$ — no variable expansion triggered
PGSERVICE=$$HOME/.pgservice

# Multi-line heredoc value (triple-quoted)
BANNER="""
Welcome to MyApp
Running on ${HOST}:${PORT}
"""

# Quotes and inline comments
EMAIL="admin@example.com" # Inline comment
TOKEN='s3cr3t'
DEBUG=1
```

---

## Similar Tools

- [python-dotenv](https://github.com/theskumar/python-dotenv) – Python-focused, lacks CLI tool
- [envdir](https://github.com/jezdez/envdir) – Directory-based env manager
- [dotenv-linter](https://github.com/dotenv-linter/dotenv-linter) – Linter for `.env` files

---

With `runenv`, you get portable, scalable, and explicit configuration management that aligns with modern deployment standards. Ideal for CLI usage, Python projects, and multi-environment pipelines.
