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
- [Sample `.env` File](#sample-env-file)
- [Similar Tools](#similar-tools)

---

## Key Features

- 🚀 **CLI-First**: Use `.env` files across any language or platform.
- 🐍 **Python-native API**: Load and transform environment settings inside Python.
- ⚙️ **Multiple Profiles**: Switch easily between `.env.dev`, `.env.prod`, etc.
- 🧩 **Framework-Friendly**: Works well with Django, Flask, FastAPI, and more.

---

## Quick Start

### Installation

```bash
pip install runenv
```

### CLI Usage

Run any command with a specified environment:

```bash
runenv .env.dev python manage.py runserver
runenv .env.prod uvicorn app:app --host 0.0.0.0
```

View options:

```bash
runenv --help
```

Key CLI features:
- `--prefix`, `--strip-prefix`: Use selective environments
- `--dry-run`: Inspect loaded environment
- `-v`: Verbosity control

---

## Python API

### Load `.env` into `os.environ`

> **Note**: The `load_env` will not parse env_file if the `runenv` CLI was used, unless you `force=True` it.

```python
from runenv import load_env

load_env() # loads .env
load_env(
    env_file=".env.dev", # file to load
    prefix='APP_',       # load only APP_.* variables from file
    strip_prefix=True,   # strip ^ prefix when loading variables
    force=True,          # load env_file even if the `runvenv` CLI was used
    search_parent=1      # look for env_file in current dir and its parent dir
)
```

### Read `.env` as a dictionary

```python
from runenv import create_env

config = create_env() # parse .env content into dictionary
config = create_env(
    env_file=".env.dev", # file to load
    prefix='APP_',       # parse only APP_.* variables from file
    strip_prefix=True,   # strip ^ prefix when parsing variables
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

## Sample `.env` File

```ini
# Basic
DEBUG=1
PORT=8000

# Nested variable
HOST=localhost
URL=http://${HOST}:${PORT}

# Quotes and comments
EMAIL="admin@example.com" # Inline comment
SECRET='s3cr3t'
```

---

## Similar Tools

- [python-dotenv](https://github.com/theskumar/python-dotenv) – Python-focused, lacks CLI tool
- [envdir](https://github.com/jezdez/envdir) – Directory-based env manager
- [dotenv-linter](https://github.com/dotenv-linter/dotenv-linter) – Linter for `.env` files

---

With `runenv`, you get portable, scalable, and explicit configuration management that aligns with modern deployment standards. Ideal for CLI usage, Python projects, and multi-environment pipelines.
