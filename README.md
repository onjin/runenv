---
title: runenv
---

[![image](https://img.shields.io/travis/onjin/runenv.svg)](https://travis-ci.org/onjin/runenv)
[![image](https://img.shields.io/pypi/v/runenv.svg)](https://pypi.python.org/pypi/runenv)
[![image](https://img.shields.io/badge/license-New%20BSD-blue.svg)](https://github.com/onjin/runenv/blob/master/LICENSE)
[![image](https://img.shields.io/badge/python-2.7%20%7C%203.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-bue)](https://travis-ci.org/onjin/runenv)
[![image](https://img.shields.io/pypi/dm/runenv.svg)](https://pypi.python.org/pypi/runenv)

Wrapper to run programs with modified environment variables loaded from
given file. You can use *runenv* to manage your app settings using
[12-factor](http://12factor.net/) principles.

You can use same environment file with **runenv** and with **docker**
using [env-file](https://docs.docker.com/reference/commandline/cli/)
parameter

-   Free software: BSD license
-   Documentation: <https://runenv.readthedocs.org>.

Features
========

CLI:

-   command-line tool to load environment variables from given file

Python API:

-   load variables from a file ([.env]{.title-ref} or passed filename)
-   load only variables with given [prefix]{.title-ref}
-   [prefix]{.title-ref} can be stripped during load
-   detect whether environment was loaded by [runenv]{.title-ref} CLI
-   force load even if [runenv]{.title-ref} CLI was used
-   [search\_parent]{.title-ref} option which allows to look for
    [env\_file]{.title-ref} in parent dirs

Installation
============

In order to install use [pip]{.title-ref}

``` {.console}
$ pip install -U runenv
```

Usage
=====

Run from shell

``` {.console}
$ runenv env.development ./manage.py runserver
```

example [env.development]{.title-ref} file

``` {.python}
BASE_URL=http://127.0.0.1:8000
DATABASE_URI=postgres://postgres:password@localhost/dbname
SECRET_KEY=y7W8pbRcuPuAmgTHsJtEpKocb7XPcV0u

# email settings
EMAIL_HOST=smtp.mandrillapp.com
EMAIL_PORT=587
EMAIL_HOST_USER=someuser
EMAIL_HOST_PASSWORD=hardpassword
EMAIL_FROM=dev@local.host
EMAIL_USE_TLS=1
```

Python API
==========

**load\_env(env\_file=\'.env\', prefix=None, strip\_prefix=True,
force=False, search\_parent=0)**

Loads environment from given `env_file`[ (default ]{.title-ref}.env\`).

Options:

  ---------------------------------------------------------------------------------------------
  option           default               description
  ---------------- --------------------- ------------------------------------------------------
  env\_file        [.env]{.title-ref}    relative or absolute path to file with environment
                                         variables

  prefix           [None]{.title-ref}    prefix to match variables e.g. [APP\_]{.title-ref}

  strip\_prefix    [True]{.title-ref}    should the prefix be stripped during loa

  force            [False]{.title-ref}   load env\_file, even though [runenv]{.title-ref} CLI
                                         command was used

  search\_parent   [0]{.title-ref}       To what level traverse parents in search of file
  ---------------------------------------------------------------------------------------------

If `prefix` option is provided only variables starting with it will be
loaded to environment, with their keys stripped of that prefix. To
preserve prefix, you can set `strip_prefix` to `False`.

Example

``` {.console}
$ echo 'APP_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env
```

``` {.python}
$ python
>>> import os
>>> from runenv import load_env
>>> load_env(prefix='APP_')
>>> 'APP_SECRET_KEY' in os.environ
False
>>> 'SECRET_KEY' in os.environ
True
>>> load_env(prefix='APP_', strip_prefix=False)
>>> 'APP_SECRET_KEY' in os.environ
True
```

**Notice**: Environment will not be loaded if command was fired by
[runenv]{.title-ref} wrapper, unless you set the **force** parameter to
**True**

`load_env` does not load variables when wrapper `runenv` is used. Also
`_RUNENV_WRAPPED` is set to `1`

Example

``` {.console}
$ echo 'APP_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env
```

``` {.python}
$ python
>>> import os
>>> from runenv import load_env
>>> os.environ['_RUNENV_WRAPPED'] = '1'
>>> load_env()
>>> 'APP_SECRET_KEY' in os.environ
False
>>> load_env(force=True)
>>> 'APP_SECRET_KEY' in os.environ
True
```

Django/Flask integration
------------------------

To use `load_env` with [Django](http://djangoproject.com/) or
[Flask](http://flask.pocoo.org/), put the followin in `manage.py` and
`wsgi.py`

``` {.python}
from runenv import load_env
load_env()
```

Similar projects
----------------

-   <https://github.com/jezdez/envdir> - runs another program with a
    modified environment according to files in a specified directory
-   <https://github.com/theskumar/python-dotenv> - Reads the key,value
    pair from .env and adds them to environment variable
