#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC.
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
__version__ = '0.0.1'

from os.path import dirname, abspath
sys.path.insert(1, dirname(dirname(abspath(__file__))))

import logging
logging.basicConfig()

from galil_apci import Galil, GalilConfig


import argparse
def getopts():
    parser = argparse.ArgumentParser(description="""Extract galil controller parameters using a template""")

    # http://docs.python.org/2/library/argparse.html
    parser.add_argument('--version', action='version', version='This is %(prog)s version {}'.format(__version__))

    parser.add_argument('--address', type=str, default='10.10.10.2', help='controller address')
    parser.add_argument('--axes',    type=str, default='ABCDEFGH', help='axes present on controller')

    parser.add_argument('template', type=str, help='parameter definition file')
    parser.add_argument('output',   type=str, nargs='?', help='output file (will overwrite template if missing)')

    argv = parser.parse_args()

    if argv.output is None:
        argv.output = argv.template

    return argv


def MAIN(argv):
    if argv.address not in Galil.addresses():
        argv.address = ''
    galil = Galil(argv.address)
    conf = GalilConfig(galil, axes=argv.axes)
    conf.load(argv.template)
    for change in conf.check():
        print(change)
    conf.refresh()
    conf.save(argv.output)


if __name__ == '__main__':
    MAIN(getopts())
