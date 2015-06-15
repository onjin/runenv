#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_runenv
----------------------------------

Tests for `runenv` module.
"""

import unittest
import os

from . import TESTS_DIR
from runenv import run, create_env


class TestRunenv(unittest.TestCase):

    def setUp(self):
        self.env_file = os.path.join(TESTS_DIR, 'env.test')

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

    def test_invalid_file(self):
        self.assertRaises(
            SystemExit, run, self.env_file, './missing'
        )

if __name__ == '__main__':
    unittest.main()
