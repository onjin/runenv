===============================
runenv
===============================

.. image:: https://img.shields.io/travis/onjin/runenv.svg
        :target: https://travis-ci.org/onjin/runenv

.. image:: https://img.shields.io/pypi/v/runenv.svg
        :target: https://pypi.python.org/pypi/runenv

.. image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
        :target: https://github.com/onjin/runenv/blob/master/LICENSE

.. image:: https://img.shields.io/pypi/dm/runenv.svg
        :target: https://pypi.python.org/pypi/runenv


Wrapper to run programs with modified environment variables loaded from given file. You can use *runenv* to manage your
app settings using 12-factor_ principles.

You can use same environment file with **runenv** and with **docker** using `env-file`_ parameter

.. _env-file: https://docs.docker.com/reference/commandline/cli/
.. _12-factor: http://12factor.net/


* Free software: BSD license
* Documentation: https://runenv.readthedocs.org.

Installation
------------

In order to install use `pip`::

    $ pip install -U runenv

Usage
-----

Run from shell::

    $ runenv env.development ./manage.py runserver

example `env.development` file::

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

Similar projects
----------------

* https://github.com/jezdez/envdir - runs another program with a modified environment according to files in a specified directory
* https://github.com/theskumar/python-dotenv - Reads the key,value pair from .env and adds them to environment variable
