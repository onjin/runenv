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
from runenv import create_env


class TestRunenv(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_env(self):
        environ = create_env(os.path.join(TESTS_DIR, 'env.test'))
        self.assertEqual(environ.get('STRING'), 'some string with spaces')
        self.assertEqual(environ.get('NUMBER'), '12')
        self.assertEqual(environ.get('FLOAT'), '11.11')
        self.assertEqual(environ.get('EMPTY'), '')
        self.assertEqual(environ.get(' SPACED '), '  spaced')
        self.assertFalse('COMMENTED' in environ)
        self.assertFalse('# COMMENTED' in environ)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
