-----
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

----------
Python API
----------

**load_env(env_file='.env', prefix=None, strip_prefix=True, force=False)**

Loads environment from given ``env_file```, default `.env`.

If ``prefix`` provided only variables started with given prefix will be loaded to environment with keys truncated from
``prefix``. To preserver prefix, pass ``strip_prefix=False``.

Example::

    $ echo 'DJANGO_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env

    $ python
    >>> import os
    >>> from runenv import load_env
    >>> load_env(prefix='DJANGO_')
    >>> 'DJANGO_SECRET_KEY' in os.environ
    False
    >>> 'SECRET_KEY' in os.environ
    True
    >>> load_env(prefix='DJANGO_', strip_prefix=False)
    >>> 'DJANGO_SECRET_KEY' in os.environ
    True


**Notice**: Environment will be not loaded if command was fired by `runenv` wrapper unless you use **force=True** parameter

Wrapper ``runenv`` sets ``_RUNENV_WRAPPED=1`` variable and ``load_env`` does not load variables then.

Example::

    $ echo 'DJANGO_SECRET_KEY=bzemAG0xfdMgFrHBT3tJBbiYIoY6EeAj' > .env

    $ python
    >>> import os
    >>> from runenv import load_env
    >>> os.environ['_RUNENV_WRAPPED'] = '1'
    >>> load_env()
    >>> 'DJANGO_SECRET_KEY' in os.environ
    False
    >>> load_env(force=True)
    >>> 'DJANGO_SECRET_KEY' in os.environ
    True


Django integration
------------------

To use ``load_env`` with `Django`_, put in ``manage.py`` and ``wsgi.py`` code::

    from runenv import load_env
    load_env()


.. _django: http://djangoproject.com/
