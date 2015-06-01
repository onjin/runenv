===============================
runenv
===============================

.. image:: https://img.shields.io/travis/onjin/runenv.svg
        :target: https://travis-ci.org/onjin/runenv

.. image:: https://img.shields.io/pypi/v/runenv.svg
        :target: https://pypi.python.org/pypi/runenv


Wrapper to run programs with different env

* Free software: BSD license
* Documentation: https://runenv.readthedocs.org.

Installation
------------

```shell
$ pip install -U runenv
```

Usage
-----

```shell
$ runenv env.development ./manage.py runserver
```

example `env.development` file:

```shell
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
