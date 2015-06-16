#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_runenv
----------------------------------

Tests for `runenv` module.
"""

import os
import sys
from contextlib import contextmanager
import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from . import TESTS_DIR
from runenv import run, create_env, load_env


@contextmanager
def capture(command, *args, **kwargs):
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


class TestRunenv(unittest.TestCase):

    def setUp(self):
        self.env_file = os.path.join(TESTS_DIR, 'env.test')
        os.environ.clear()

    def test_create_env(self):
        environ = create_env(self.env_file)
        self.assertEqual(environ.get('STRING'), 'some string with spaces')
        self.assertEqual(environ.get('NUMBER'), '12')
        self.assertEqual(environ.get('FLOAT'), '11.11')
        self.assertEqual(environ.get('EMPTY'), '')
        self.assertEqual(environ.get(' SPACED '), '  spaced')
        self.assertFalse('COMMENTED' in environ)
        self.assertFalse('# COMMENTED' in environ)

    def test_run(self):
        self.assertEqual(run(self.env_file, '/bin/true'), 0)
        self.assertEqual(run(self.env_file, '/bin/false'), 1)
        with capture(run, self.env_file, '/usr/bin/env') as output:
            self.assertTrue('_RUNENV_WRAPPED', output)

    def test_invalid_file(self):
        self.assertRaises(
            SystemExit, run, self.env_file, './missing'
        )

    def test_load_env_from_default_file(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENV_STRING' in os.environ)
        self.assertFalse('RUNENV_NUMBER' in os.environ)
        self.assertFalse('RUNENV_FLOAT' in os.environ)

        load_env()

        self.assertTrue('RUNENV_STRING' in os.environ)
        self.assertTrue('RUNENV_NUMBER' in os.environ)
        self.assertTrue('RUNENV_FLOAT' in os.environ)
        self.assertEqual(os.environ.get('RUNENV_STRING'), 'some string')
        self.assertEqual(os.environ.get('RUNENV_NUMBER'), '13')
        self.assertEqual(os.environ.get('RUNENV_FLOAT'), '12.12')

    def test_load_env_only_prefixed_variables(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

        load_env(env_file='env.custom', prefix='RUNENVC_S')

        self.assertTrue('TRING' in os.environ)
        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

    def test_load_env_only_prefixed_variables_without_strip_prefix(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

        load_env(env_file='env.custom', prefix='RUNENVC_S', strip_prefix=False)

        self.assertTrue('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

    def test_load_env_from_custom_file(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

        load_env(env_file='env.custom')

        self.assertTrue('RUNENVC_STRING' in os.environ)
        self.assertTrue('RUNENVC_NUMBER' in os.environ)
        self.assertTrue('RUNENVC_FLOAT' in os.environ)
        self.assertEqual(os.environ.get('RUNENVC_STRING'), 'custom string')
        self.assertEqual(os.environ.get('RUNENVC_NUMBER'), '14')
        self.assertEqual(os.environ.get('RUNENVC_FLOAT'), '14.14')

    def test_load_env_skip_if_wrapped_by_runenv(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

        # mark as runned by `envfile` wrapper
        os.environ['_RUNENV_WRAPPED'] = '1'

        load_env(env_file='env.custom')

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

    def test_load_env_force_even_wrapped_by_runenv(self):
        os.chdir(os.path.join(TESTS_DIR, 'cwd'))

        self.assertFalse('RUNENVC_STRING' in os.environ)
        self.assertFalse('RUNENVC_NUMBER' in os.environ)
        self.assertFalse('RUNENVC_FLOAT' in os.environ)

        os.environ['_RUNENV_WRAPPED'] = '1'

        load_env(env_file='env.custom', force=True)

        self.assertTrue('RUNENVC_STRING' in os.environ)
        self.assertTrue('RUNENVC_NUMBER' in os.environ)
        self.assertTrue('RUNENVC_FLOAT' in os.environ)
        self.assertEqual(os.environ.get('RUNENVC_STRING'), 'custom string')
        self.assertEqual(os.environ.get('RUNENVC_NUMBER'), '14')
        self.assertEqual(os.environ.get('RUNENVC_FLOAT'), '14.14')

if __name__ == '__main__':
    unittest.main()
