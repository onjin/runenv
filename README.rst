runenv
======
.. image:: https://img.shields.io/travis/onjin/runenv.svg
        :target: https://travis-ci.org/onjin/runenv

.. image:: https://img.shields.io/pypi/v/runenv.svg
        :target: https://pypi.python.org/pypi/runenv

.. image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
        :target: https://github.com/onjin/runenv/blob/master/LICENSE

.. image:: https://img.shields.io/badge/python-2.7%20|%203.6%20|%203.7%20|%203.8%20|%203.9-blue

.. image:: https://img.shields.io/pypi/dm/runenv.svg
        :target: https://pypi.python.org/pypi/runenv

Wrapper to run programs with modified environment variables loaded from
given file. You can use *runenv* to manage your app settings using
`12-factor <http://12factor.net/>`__ principles.

You can use same environment file with **runenv** and with **docker**
using `env-file <https://docs.docker.com/reference/commandline/cli/>`__
parameter

-  Free software: BSD license
-  Documentation: https://runenv.readthedocs.org.

Features
========

CLI:

-  command-line tool to load environment variables from given file

Python API:

-  load variables from a file (.env or passed filename)
-  load only variables with given prefix
-  prefix can be stripped during load
-  detect whether environment was loaded by runenv CLI
-  force load even if runenv CLI was used
-  search_parent option which allows to look for env_file in parent dirs

Installation
============

In order to install use pip

.. code:: console

   $ pip install -U runenv

Usage
=====

Run from shell

.. code:: console

   $ runenv env.development ./manage.py runserver

example env.development file

.. code:: python

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

Python API
==========

**load_env(env_file='.env', prefix=None, strip_prefix=True, force=False,
search_parent=0)**

Loads environment from given ``env_file``\ (default.env`).

Options:

+-----------+---------------+----------------------------------------+
| option    | default       | description                            |
+===========+===============+========================================+
| env_file  | .env          | relative or absolute path to file with |
|           |               | environment variables                  |
+-----------+---------------+----------------------------------------+
| prefix    | None          | prefix to match variables e.g. APP\_   |
+-----------+---------------+----------------------------------------+
| str       | True          | should the prefix be stripped during   |
| ip_prefix |               | loa                                    |
+-----------+---------------+----------------------------------------+
| force     | False         | load env_file, even though runenv CLI  |
|           |               | command was used                       |
+-----------+---------------+----------------------------------------+
| sear      | 0             | To what level traverse parents in      |
| ch_parent |               | search of file                         |
+-----------+---------------+----------------------------------------+

If ``prefix`` option is provided only variables starting with it will be
loaded to environment, with their keys stripped of that prefix. To
preserve prefix, you can set ``strip_prefix`` to ``False``.

Example

.. code:: console

   $ echo 'APP_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env

.. code:: python

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

**Notice**: Environment will not be loaded if command was fired by
runenv wrapper, unless you set the **force** parameter to **True**

``load_env`` does not load variables when wrapper ``runenv`` is used.
Also ``_RUNENV_WRAPPED`` is set to ``1``

Example

.. code:: console

   $ echo 'APP_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env

.. code:: python

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

Django/Flask integration
------------------------

To use ``load_env`` with `Django <http://djangoproject.com/>`__ or
`Flask <http://flask.pocoo.org/>`__, put the followin in ``manage.py``
and ``wsgi.py``

.. code:: python

   from runenv import load_env
   load_env()

Similar projects
----------------

-  https://github.com/jezdez/envdir - runs another program with a
   modified environment according to files in a specified directory
-  https://github.com/theskumar/python-dotenv - Reads the key,value pair
   from .env and adds them to environment variable

.. |image| image:: https://img.shields.io/travis/onjin/runenv.svg
   :target: https://travis-ci.org/onjin/runenv
.. |image| image:: https://img.shields.io/pypi/v/runenv.svg
   :target: https://pypi.python.org/pypi/runenv
.. |image| image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
   :target: https://github.com/onjin/runenv/blob/master/LICENSE
.. |image| image:: https://img.shields.io/badge/python-2.7%20%7C%203.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-bue
   :target: https://travis-ci.org/onjin/runenv
.. |image| image:: https://img.shields.io/pypi/dm/runenv.svg
   :target: https://pypi.python.org/pypi/runenv
