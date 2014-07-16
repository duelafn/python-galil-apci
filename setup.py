#!/usr/bin/env python
"""
APCI LLC's python modules to interface with Galil controllers.
"""
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
import re

__version__ = re.search(r'(?m)^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"', open('galil_apci/__init__.py').read()).group(1)

from distutils.core import setup, Extension

galil_module = Extension(
    '_Galil',
    [ '_Galil.cpp' ],                            # Requires that swig called on development machine (beware version issues)
#     [ 'swig/Galil.i' ], swig_opts = ['-c++'],  # Requires swig on client; also doesn't work
    library_dirs = ['/usr/lib64'],               # galil installs to an improper path - no problem...
    libraries    = ['galil'],
    extra_compile_args = ['-Wno-write-strings', '-Wno-unused-but-set-variable'],
)

setup(
    name         = 'galil-apci',
    version      = __version__,
    url          = 'http://apcisystems.com/',
    author       = "APCI LLC",
    author_email = 'deans@apcisystems.com',
    description  = "Python Interface to Galil Controllers",
    packages     = [ 'galil_apci' ],
    py_modules   = [ 'Galil' ],
    ext_modules  = [ galil_module ],
    scripts      = [ 'bin/dmctool' ],
    provides     = "galil_apci",
    requires     = [ "jinja2_apci", ],
)
