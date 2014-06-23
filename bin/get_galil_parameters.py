#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Dean Serenevy  <deans@apcisystems.com>
# This software is Copyright (c) 2014 APCI, LLC. All rights reserved.
from __future__ import division, absolute_import, print_function, unicode_literals

import sys
sys.path.insert(1, "pylib")
__version__ = '0.0.1'

from apci.galil import Galil, GalilConfig


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
