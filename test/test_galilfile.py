#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2013 APCI, LLC.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, absolute_import, print_function, unicode_literals
import unittest2

import json
import sys
from os.path import dirname, abspath
sys.path.insert(1, dirname(dirname(abspath(__file__))))

from galil_apci.file import GalilFile
from jinja2 import UndefinedError

class BasicAccess(unittest2.TestCase):
    def setUp(self):
        self.gf = GalilFile(path="test/gal")
        self.machine = json.load(open("test/machine.json",'rb'))

    def test_galtest(self):
        got = self.gf.load("galtest.gal", self.machine)
        wanted = open('test/gal/galtest.out').read().strip()
        self.assertEqual( got, wanted, "galtest.gal" )

        with self.assertRaises(UndefinedError):
            self.gf.load("galtest.gal", dict())


if __name__ == '__main__':
    unittest2.main()
